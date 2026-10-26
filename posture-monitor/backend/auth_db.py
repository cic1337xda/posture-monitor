import sqlite3
import re
import secrets
import datetime
import os
import bcrypt
import jwt

DB_PATH = os.environ.get("AUTH_DB_PATH", "/data/posture_auth.db" if os.path.exists("/data") else "posture_auth.db")
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "posture_secret_auth_jwt_key_2026_flowkraft_xyz_secure_32bytes")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
OTP_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 5

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables for users, authentication attempts, and OTP records."""
    conn = get_db()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_active INTEGER DEFAULT 0,
                failed_login_attempts INTEGER DEFAULT 0,
                lockout_until TEXT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS otps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                otp_code TEXT NOT NULL,
                purpose TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                expires_at TEXT NOT NULL,
                is_used INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.close()

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    SOP Rule: Minimum 8 characters, uppercase, lowercase, number, and special character.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter (a-z)."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character (!@#$%^&* etc)."
    return True, ""

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def create_user(username: str, email: str, password: str) -> tuple[dict | None, str]:
    """Registers a new user in inactive state until OTP is verified."""
    username = username.strip().lower()
    email = email.strip().lower()

    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        return None, "Invalid email address format."
    if len(username) < 3:
        return None, "Username must be at least 3 characters."

    valid_pwd, pwd_err = validate_password_strength(password)
    if not valid_pwd:
        return None, pwd_err

    pwd_hash = hash_password(password)

    conn = get_db()
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO users (username, email, password_hash, is_active) VALUES (?, ?, ?, 0)",
                (username, email, pwd_hash)
            )
            user_id = cursor.lastrowid
        user = get_user_by_id(user_id)
        return user, ""
    except sqlite3.IntegrityError as e:
        err_msg = str(e).lower()
        if "email" in err_msg:
            return None, "Email address is already registered."
        elif "username" in err_msg:
            return None, "Username is already taken."
        return None, "Account already exists."
    finally:
        conn.close()

def get_user_by_id(user_id: int) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_email_or_username(identifier: str) -> dict | None:
    clean_id = identifier.strip().lower()
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ? OR username = ?",
        (clean_id, clean_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def record_failed_login(user_id: int) -> tuple[bool, str]:
    """
    SOP Rule: Lock user account for 15 minutes after 5 consecutive failed login attempts.
    """
    conn = get_db()
    with conn:
        user = conn.execute("SELECT failed_login_attempts FROM users WHERE id = ?", (user_id,)).fetchone()
        attempts = (user["failed_login_attempts"] if user else 0) + 1
        lockout_str = None
        is_locked = False
        msg = f"Invalid credentials. Attempt {attempts} of {MAX_FAILED_LOGIN_ATTEMPTS}."

        if attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
            is_locked = True
            lockout_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=LOCKOUT_MINUTES)
            lockout_str = lockout_time.isoformat()
            msg = f"Account temporarily locked for {LOCKOUT_MINUTES} minutes due to {MAX_FAILED_LOGIN_ATTEMPTS} failed attempts."

        conn.execute(
            "UPDATE users SET failed_login_attempts = ?, lockout_until = ? WHERE id = ?",
            (attempts, lockout_str, user_id)
        )
    conn.close()
    return is_locked, msg

def is_account_locked(user: dict) -> tuple[bool, str]:
    if not user.get("lockout_until"):
        return False, ""
    try:
        lock_until = datetime.datetime.fromisoformat(user["lockout_until"])
        now = datetime.datetime.utcnow()
        if now < lock_until:
            rem_mins = max(1, int((lock_until - now).total_seconds() / 60))
            return True, f"Account is locked. Please try again in {rem_mins} minutes."
        else:
            # Lockout expired, reset attempts
            reset_failed_logins(user["id"])
            return False, ""
    except Exception:
        return False, ""

def reset_failed_logins(user_id: int):
    conn = get_db()
    with conn:
        conn.execute("UPDATE users SET failed_login_attempts = 0, lockout_until = NULL WHERE id = ?", (user_id,))
    conn.close()

def generate_and_store_otp(user_id: int, email: str, purpose: str) -> str:
    """
    SOP Rule: Cryptographic 6-digit number, 10-minute expiry, max 5 failed attempts, single-use.
    """
    otp_code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = (datetime.datetime.utcnow() + datetime.timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()

    conn = get_db()
    with conn:
        # Invalidate previous unused OTPs for this user & purpose
        conn.execute(
            "UPDATE otps SET is_used = 1 WHERE user_id = ? AND purpose = ? AND is_used = 0",
            (user_id, purpose)
        )
        conn.execute(
            "INSERT INTO otps (user_id, email, otp_code, purpose, expires_at, is_used, attempts) VALUES (?, ?, ?, ?, ?, 0, 0)",
            (user_id, email.lower(), otp_code, purpose, expires_at)
        )
    conn.close()
    return otp_code

def verify_otp(email: str, otp_code: str, purpose: str) -> tuple[bool, str, dict | None]:
    clean_email = email.strip().lower()
    clean_code = otp_code.strip()

    conn = get_db()
    row = conn.execute(
        "SELECT * FROM otps WHERE email = ? AND purpose = ? AND is_used = 0 ORDER BY id DESC LIMIT 1",
        (clean_email, purpose)
    ).fetchone()

    if not row:
        conn.close()
        return False, "No active verification code found. Please request a new one.", None

    otp = dict(row)
    now = datetime.datetime.utcnow()
    expires_at = datetime.datetime.fromisoformat(otp["expires_at"])

    if now > expires_at:
        with conn:
            conn.execute("UPDATE otps SET is_used = 1 WHERE id = ?", (otp["id"],))
        conn.close()
        return False, "Verification code has expired. Please request a new one.", None

    if otp["attempts"] >= MAX_OTP_ATTEMPTS:
        with conn:
            conn.execute("UPDATE otps SET is_used = 1 WHERE id = ?", (otp["id"],))
        conn.close()
        return False, "Maximum verification attempts exceeded. Please request a new code.", None

    if otp["otp_code"] != clean_code:
        new_attempts = otp["attempts"] + 1
        with conn:
            conn.execute("UPDATE otps SET attempts = ? WHERE id = ?", (new_attempts, otp["id"]))
        conn.close()
        rem = MAX_OTP_ATTEMPTS - new_attempts
        return False, f"Incorrect code. {rem} attempt(s) remaining.", None

    # Code is valid - mark as used
    with conn:
        conn.execute("UPDATE otps SET is_used = 1 WHERE id = ?", (otp["id"],))
        if purpose == "register":
            conn.execute("UPDATE users SET is_active = 1 WHERE id = ?", (otp["user_id"],))

    user = conn.execute("SELECT * FROM users WHERE id = ?", (otp["user_id"],)).fetchone()
    conn.close()
    return True, "Verification successful.", dict(user) if user else None

def update_password_with_otp(email: str, otp_code: str, new_password: str) -> tuple[bool, str]:
    """Verifies reset OTP and updates password after validating password strength."""
    valid_pwd, pwd_err = validate_password_strength(new_password)
    if not valid_pwd:
        return False, pwd_err

    is_valid, msg, user = verify_otp(email, otp_code, "forgot_password")
    if not is_valid or not user:
        return False, msg

    new_hash = hash_password(new_password)
    conn = get_db()
    with conn:
        conn.execute(
            "UPDATE users SET password_hash = ?, failed_login_attempts = 0, lockout_until = NULL WHERE id = ?",
            (new_hash, user["id"])
        )
    conn.close()
    return True, "Password has been successfully updated. You may now log in."

def create_session_token(user_id: int, email: str, username: str) -> str:
    """Signs a JWT token with user identity and 7-day expiration."""
    exp = datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXPIRATION_DAYS)
    payload = {
        "sub": str(user_id),
        "email": email,
        "username": username,
        "exp": exp
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_session_token(token: str) -> dict | None:
    """Validates signature and claims of JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        return None

# Initialize the SQLite tables upon module load
init_db()

import os

def load_local_env():
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '.env'),
        os.path.join(os.path.dirname(__file__), '..', '.env'),
        os.path.join(os.getcwd(), '.env'),
        os.path.join(os.getcwd(), 'posture-monitor-docker', '.env')
    ]
    for p in possible_paths:
        if os.path.exists(p):
            with open(p, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        k, v = k.strip(), v.strip()
                        if k not in os.environ:
                            os.environ[k] = v
            break

load_local_env()

import mediapipe as mp
import numpy as np
import time
import io
import os
import json
from datetime import datetime
from collections import deque
from PIL import Image
from flask import Flask, request, jsonify, redirect, make_response
import auth_db
import email_service

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None

# ==============================================================================
# ENTERPRISE POSTURE PIPELINE (V4: STANDING + SITTING + BAD POSTURE + WEARABLE)
# ==============================================================================

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 

MAX_SITTING_SECONDS = float(os.environ.get("MAX_SITTING_SECONDS", "600"))
MAX_BAD_POSTURE_SECONDS = float(os.environ.get("MAX_BAD_POSTURE_SECONDS", "5.0"))
WARNING_PERCENT = float(os.environ.get("WARNING_PERCENT", "0.6"))
CRITICAL_PERCENT = float(os.environ.get("CRITICAL_PERCENT", "0.85"))
DETECTION_CONFIDENCE = float(os.environ.get("DETECTION_CONFIDENCE", "0.6"))
CALIBRATION_FRAMES = int(os.environ.get("CALIBRATION_FRAMES", "25"))
EMA_ALPHA = float(os.environ.get("EMA_ALPHA", "0.25"))
STATE_HYSTERESIS = int(os.environ.get("STATE_HYSTERESIS", "6"))
REQUIRED_STANDING_TIME = 5.0 # Must stand for 5 seconds to reset sitting timer

class EMASmoother:
    def __init__(self, alpha=EMA_ALPHA):
        self.alpha = alpha
        self.values = {}
    def update(self, key, value):
        if key not in self.values: self.values[key] = value
        else: self.values[key] = self.alpha * value + (1 - self.alpha) * self.values[key]
        return self.values[key]

class PostureMonitor:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose_estimator = self.mp_pose.Pose(min_detection_confidence=DETECTION_CONFIDENCE, min_tracking_confidence=DETECTION_CONFIDENCE, model_complexity=1)

        self.current_state = "Waiting for Calibration"
        self.current_metric_text = "N/A"
        self.alert_level = "normal"
        self.alert_message = ""

        # Calibration
        self.is_calibrated = False
        self.calibration_phase = 0
        self.calibration_buffer = []
        self.calibration_frames_needed = CALIBRATION_FRAMES
        self.baseline_y = 0.0
        self.baseline_width = 0.0
        self.baseline_neck_ratio = 0.0
        self.baseline_pitch = 0.0

        # Detection Thresholds (Tuned with Anti-Cheat)
        self.sensitivity_offset = 0.12        # Standing threshold offset
        self.slouch_ratio_threshold = 0.88   # If neck ratio < 88% of baseline -> Slouching
        self.lean_threshold = 0.10           # If shoulder height diff > 10% width -> Leaning
        self.hunch_offset = 0.035            # If shoulder drops > 0.035 -> Slumped (anti-cheat)
        self.pitch_up_threshold = 0.045      # If head pitch exceeds baseline + 0.045 -> Chin up (anti-cheat)
        self.pitch_down_threshold = 0.065    # If head pitch below baseline - 0.065 -> Looking down

        self.smoother = EMASmoother()
        self.state_votes = deque(maxlen=STATE_HYSTERESIS)

        # Advanced Chronometer Engine
        self.sitting_duration = 0.0
        self.sitting_start_time = None
        self.standing_start_time = None
        self.max_sitting_time = MAX_SITTING_SECONDS
        
        # Bad Posture Chronometer
        self.bad_posture_start_time = None
        self.bad_posture_duration = 0.0
        self.bad_posture_alarm = False
        self.max_bad_posture_time = MAX_BAD_POSTURE_SECONDS

        self.alarm_triggered = False
        self.stand_up_count = 0
        self.last_stand_celebration = 0

        # Wearable & MQTT Engine
        self.wearable_mac = ""
        self.mqtt_client = None
        if mqtt is not None:
            try:
                # Connect to local Mosquitto Docker container on port 1883
                self.mqtt_client = mqtt.Client()
                self.mqtt_client.connect("posturemonitor-mqtt", 1883, 60)
                self.mqtt_client.loop_start()
                print("Connected to Mosquitto Broker on Port 1883!")
            except Exception as e:
                print("MQTT Connection Failed (Operating in Standalone mode):", e)

    def set_max_sitting_time(self, seconds):
        self.max_sitting_time = seconds

    def link_wearable(self, mac):
        self.wearable_mac = str(mac).strip().upper()
        # Vibrate briefly upon successful pairing
        self._publish_mqtt("linked")

    def _publish_mqtt(self, command):
        if self.wearable_mac and self.mqtt_client:
            topic = f"posture/wearable/{self.wearable_mac}/command"
            try:
                self.mqtt_client.publish(topic, command, qos=0)
            except Exception:
                pass

    def trigger_calibration(self):
        self.is_calibrated = False
        self.calibration_phase = 1
        self.calibration_buffer = []

    def _extract_features(self, landmarks):
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_ear = landmarks[self.mp_pose.PoseLandmark.LEFT_EAR]
        right_ear = landmarks[self.mp_pose.PoseLandmark.RIGHT_EAR]
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE]

        shoulder_y = (left_shoulder.y + right_shoulder.y) / 2.0
        shoulder_width = max(0.03, abs(right_shoulder.x - left_shoulder.x))
        shoulder_tilt = abs(left_shoulder.y - right_shoulder.y) / shoulder_width

        # Head vertical calculation
        if left_ear.visibility > 0.35 and right_ear.visibility > 0.35:
            head_y = (left_ear.y + right_ear.y) / 2.0
        elif left_ear.visibility > 0.35:
            head_y = left_ear.y
        elif right_ear.visibility > 0.35:
            head_y = right_ear.y
        elif nose.visibility > 0.35:
            head_y = nose.y + 0.05
        else:
            head_y = shoulder_y - 0.15

        neck_height = shoulder_y - head_y
        neck_ratio = neck_height / shoulder_width
        head_pitch = (head_y - nose.y) / shoulder_width if nose.visibility > 0.3 else 0.0

        return {
            "shoulder_y": shoulder_y,
            "shoulder_width": shoulder_width,
            "shoulder_tilt": shoulder_tilt,
            "head_y": head_y,
            "neck_height": neck_height,
            "neck_ratio": neck_ratio,
            "head_pitch": head_pitch,
            "visibility": min(left_shoulder.visibility, right_shoulder.visibility)
        }

    def _evaluate_posture(self, landmarks, h, w):
        features = self._extract_features(landmarks)
        calibrating = not self.is_calibrated
        vis_threshold = 0.2 if calibrating else 0.4

        if not calibrating and features["visibility"] < vis_threshold:
            self.current_metric_text = "Shoulders Not Visible"
            return "Standing"

        features["shoulder_y"] = self.smoother.update("shoulder_y", features["shoulder_y"])
        features["shoulder_width"] = self.smoother.update("shoulder_width", features["shoulder_width"])
        features["neck_ratio"] = self.smoother.update("neck_ratio", features["neck_ratio"])
        features["head_pitch"] = self.smoother.update("head_pitch", features["head_pitch"])

        if calibrating:
            if features["visibility"] >= 0.15:
                self.calibration_buffer.append(features)
                self.current_metric_text = f"Calibrating: {int((len(self.calibration_buffer) / self.calibration_frames_needed) * 100)}%"
                if len(self.calibration_buffer) >= self.calibration_frames_needed:
                    self.baseline_y = float(np.mean([f["shoulder_y"] for f in self.calibration_buffer]))
                    self.baseline_width = float(np.mean([f["shoulder_width"] for f in self.calibration_buffer]))
                    self.baseline_neck_ratio = float(np.mean([f["neck_ratio"] for f in self.calibration_buffer]))
                    self.baseline_pitch = float(np.mean([f["head_pitch"] for f in self.calibration_buffer]))
                    self.calibration_phase = 0
                    self.is_calibrated = True
            return "Sitting (Calibrating)"

        safe_baseline = self.baseline_width if self.baseline_width > 0.01 else 0.01
        scale_factor = features["shoulder_width"] / safe_baseline
        expected_resting_y = 0.5 + (self.baseline_y - 0.5) * scale_factor
        self.standing_threshold_y = expected_resting_y - self.sensitivity_offset

        # 1. Decision 1: Standing or Sitting?
        if features["shoulder_y"] < self.standing_threshold_y:
            self.current_metric_text = f"Standing | Scale: {scale_factor:.2f}"
            return "Standing"

        # 2. Decision 2: Sitting -> Evaluate Posture Quality
        neck_pct = (features["neck_ratio"] / max(0.01, self.baseline_neck_ratio)) * 100
        shoulder_drop = features["shoulder_y"] - expected_resting_y
        pitch_diff = features["head_pitch"] - self.baseline_pitch

        self.current_metric_text = f"Neck: {neck_pct:.0f}% | Drop: {shoulder_drop:+.2f} | Pitch: {pitch_diff:+.2f}"

        # Anti-cheat 1: Shoulders dropped into chair
        if shoulder_drop > self.hunch_offset:
            return "Bad Posture"

        # Anti-cheat 2: Head tilted up / craning chin up
        if pitch_diff > self.pitch_up_threshold:
            return "Bad Posture"

        # Head bowed down
        if pitch_diff < -self.pitch_down_threshold:
            return "Bad Posture"

        # Slouching / neck compressed
        if features["neck_ratio"] < (self.baseline_neck_ratio * self.slouch_ratio_threshold):
            return "Bad Posture"

        # Lateral Leaning
        if features["shoulder_tilt"] > self.lean_threshold:
            return "Bad Posture"

        return "Sitting"

    def _apply_hysteresis(self, raw_state):
        if "Calibrating" in raw_state:
            return raw_state
        self.state_votes.append(raw_state)
        if len(self.state_votes) < 3:
            return raw_state
        counts = {}
        for s in self.state_votes:
            counts[s] = counts.get(s, 0) + 1
        most_common = max(counts, key=counts.get)
        if counts[most_common] >= (len(self.state_votes) // 2 + 1):
            return most_common
        return raw_state

    def _update_alert_system(self):
        now = time.time()

        # ------------------------------------------------------------------
        # CASE 1: USER IS STANDING
        # ------------------------------------------------------------------
        if self.current_state == "Standing":
            self.sitting_start_time = None  # Pause sitting timer
            self.bad_posture_start_time = None
            self.bad_posture_duration = 0.0

            if self.standing_start_time is None:
                self.standing_start_time = now
                self._publish_mqtt("stop")  # Stop vibration when user stands up
                self.alarm_triggered = False
                self.bad_posture_alarm = False

            stand_duration = now - self.standing_start_time
            if stand_duration >= REQUIRED_STANDING_TIME:
                if self.sitting_duration > 0:
                    self.stand_up_count += 1
                    self.last_stand_celebration = now
                    self.sitting_duration = 0.0  # RESET SITTING TIMER
                self.alert_level = "normal"
                self.alert_message = "Great posture!"
            else:
                if self.sitting_duration > 0:
                    self.alert_message = f"Keep standing... {int(REQUIRED_STANDING_TIME - stand_duration + 1)}s to reset"
                    self.alert_level = "warning"
                else:
                    self.alert_message = "Great posture!"

        # ------------------------------------------------------------------
        # CASE 2: USER IS SITTING (GOOD, BAD, OR CALIBRATING)
        # ------------------------------------------------------------------
        else:
            self.standing_start_time = None  # Cancel standing reset process

            # 2a. Sitting Timer Accumulation (Sitting too long)
            if self.current_state in ["Sitting", "Bad Posture", "Sitting (Calibrating)"]:
                if self.sitting_start_time is None:
                    self.sitting_start_time = now - self.sitting_duration
                self.sitting_duration = now - self.sitting_start_time

            # 2b. Bad Posture Timer Accumulation
            if self.current_state == "Bad Posture":
                if self.bad_posture_start_time is None:
                    self.bad_posture_start_time = now
                self.bad_posture_duration = now - self.bad_posture_start_time
            else:
                # Posture is good or calibrating -> reset bad posture timer
                if self.bad_posture_alarm:
                    self.bad_posture_alarm = False
                    # Stop vibration if sitting limit hasn't also been exceeded
                    if self.sitting_duration < self.max_sitting_time:
                        self.alarm_triggered = False
                        self._publish_mqtt("stop")
                self.bad_posture_start_time = None
                self.bad_posture_duration = 0.0

            # 2c. Dual Alert Prioritization:
            # PRIORITY 1: BAD POSTURE PERSISTS (e.g. >= 5 seconds)
            if self.bad_posture_duration >= self.max_bad_posture_time:
                self.alert_level = "exceeded"
                self.alert_message = f"Bad Posture! Straighten your spine ({int(self.bad_posture_duration)}s)"
                if not self.bad_posture_alarm:
                    self.bad_posture_alarm = True
                    self.alarm_triggered = True
                    self._publish_mqtt("vibrate_heavy")
            elif self.bad_posture_duration >= 2.0:
                self.alert_level = "warning"
                self.alert_message = f"Poor posture detected! Fix now ({int(self.max_bad_posture_time - self.bad_posture_duration + 1)}s)"

            # PRIORITY 2: SEDENTARY LIMIT (SITTING TOO LONG)
            else:
                fraction = self.sitting_duration / max(self.max_sitting_time, 1)
                if fraction >= 1.0:
                    self.alert_level = "exceeded"
                    if not self.alarm_triggered:
                        self.alarm_triggered = True
                        self._publish_mqtt("vibrate_heavy")
                    self.alert_message = "Time to stand up and stretch!"
                elif fraction >= CRITICAL_PERCENT:
                    self.alert_level = "critical"
                    self.alarm_triggered = False
                    self.alert_message = f"Almost at your limit — {int(self.max_sitting_time - self.sitting_duration)}s left!"
                else:
                    self.alert_level = "normal"
                    self.alarm_triggered = False
                    self.alert_message = "You're doing fine." if self.current_state != "Sitting (Calibrating)" else "Calibrating..."

    def process_frame_bytes(self, jpeg_bytes):
        try: img = Image.open(io.BytesIO(jpeg_bytes)).convert("RGB"); frame = np.array(img)
        except Exception: return None

        h, w = frame.shape[:2]
        results = self.pose_estimator.process(frame)

        raw_state = "Away / Out of Frame"
        self.current_metric_text = "No Subject Detected"
        landmarks_list = []

        if results.pose_landmarks:
            landmarks_list = [{"x": round(lm.x, 4), "y": round(lm.y, 4), "visibility": round(lm.visibility, 4)} for lm in results.pose_landmarks.landmark]
            raw_state = self._evaluate_posture(results.pose_landmarks.landmark, h, w)

        self.current_state = self._apply_hysteresis(raw_state)
        self._update_alert_system()

        return {
            "landmarks": landmarks_list,
            "state": self.current_state,
            "alert_level": self.alert_level,
            "alert_message": self.alert_message,
            "remaining": max(0, int(self.max_sitting_time - self.sitting_duration)),
            "fraction": round(min(self.sitting_duration / max(self.max_sitting_time, 1), 1.0), 3),
            "bad_posture_duration": round(self.bad_posture_duration, 1),
            "alarm": self.alarm_triggered,
            "metrics": self.current_metric_text,
            "calibrating": self.calibration_phase > 0,
            "calibration_progress": len(self.calibration_buffer) / max(self.calibration_frames_needed, 1) if self.calibration_phase > 0 else 0,
            "stand_up_count": self.stand_up_count,
            "recent_celebration": (time.time() - self.last_stand_celebration) < 5,
        }

monitor = PostureMonitor()
monitor.trigger_calibration()

# --- SECURITY & RATE LIMITING MIDDLEWARE ---
auth_rate_limits = {}

def check_rate_limit(ip, limit=15, window=60):
    now = time.time()
    if ip not in auth_rate_limits:
        auth_rate_limits[ip] = []
    auth_rate_limits[ip] = [t for t in auth_rate_limits[ip] if now - t < window]
    if len(auth_rate_limits[ip]) >= limit:
        return False
    auth_rate_limits[ip].append(now)
    return True

@app.after_request
def apply_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

def get_current_user():
    token = request.cookies.get('session_token')
    if not token:
        return None
    payload = auth_db.verify_session_token(token)
    if not payload:
        return None
    user = auth_db.get_user_by_id(int(payload["sub"]))
    if not user or not user["is_active"]:
        return None
    return user

# --- HEALTHCHECK ENDPOINT (SOP BASELINE) ---
@app.route('/api/v1/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "database": "connected",
        "timestamp": datetime.now().isoformat()
    })

# --- PAGE ROUTING ---
@app.route('/')
def index():
    user = get_current_user()
    if not user:
        return redirect('/login')
    return app.send_static_file('index.html')

@app.route('/login')
def login_page():
    user = get_current_user()
    if user:
        return redirect('/')
    return app.send_static_file('login.html')

@app.route('/privacy')
@app.route('/privacy.html')
def privacy_page():
    return app.send_static_file('privacy.html')

@app.route('/favicon.ico')
def favicon_ico():
    return app.send_static_file('favicon.ico')

@app.route('/favicon.svg')
def favicon_svg():
    return app.send_static_file('favicon.svg')

@app.route('/robots.txt')
def robots():
    return app.send_static_file('robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return app.send_static_file('sitemap.xml')

@app.route('/llms.txt')
def llms_txt():
    return app.send_static_file('llms.txt')

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "message": "Endpoint not found", "error": "Not Found"}), 404
    return app.send_static_file('404.html'), 404

# --- AUTHENTICATION API ENDPOINTS ---
@app.route('/api/auth/register', methods=['POST'])
def register():
    client_ip = request.remote_addr or 'unknown'
    if not check_rate_limit(client_ip):
        return jsonify({"success": False, "message": "Too many requests. Please wait a minute.", "error": "Rate limit"}), 429

    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    email = data.get("email", "")
    password = data.get("password", "")

    user, err = auth_db.create_user(username, email, password)
    if err:
        return jsonify({"success": False, "message": err, "error": err}), 400

    otp_code = auth_db.generate_and_store_otp(user["id"], user["email"], "register")
    email_service.send_otp_email(user["email"], otp_code, "register")

    return jsonify({
        "success": True,
        "message": "Account created! A 6-digit verification code has been sent to your email.",
        "data": {"email": user["email"]},
        "error": None
    })

@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    otp_code = data.get("otp_code", "")
    purpose = data.get("purpose", "register")

    ok, msg, user = auth_db.verify_otp(email, otp_code, purpose)
    if not ok or not user:
        return jsonify({"success": False, "message": msg, "error": msg}), 400

    token = auth_db.create_session_token(user["id"], user["email"], user["username"])
    resp = make_response(jsonify({
        "success": True,
        "message": msg,
        "data": {"user": {"id": user["id"], "username": user["username"], "email": user["email"]}},
        "error": None
    }))
    resp.set_cookie('session_token', token, httponly=True, samesite='Lax', max_age=7*24*3600)
    return resp

@app.route('/api/auth/login', methods=['POST'])
def login():
    client_ip = request.remote_addr or 'unknown'
    if not check_rate_limit(client_ip):
        return jsonify({"success": False, "message": "Too many login attempts. Please wait.", "error": "Rate limit"}), 429

    data = request.get_json(silent=True) or {}
    identifier = data.get("identifier", "")
    password = data.get("password", "")

    user = auth_db.get_user_by_email_or_username(identifier)
    if not user:
        return jsonify({"success": False, "message": "Invalid credentials.", "error": "User not found"}), 401

    is_locked, lock_msg = auth_db.is_account_locked(user)
    if is_locked:
        return jsonify({"success": False, "message": lock_msg, "error": "Account locked"}), 403

    if not auth_db.verify_password(password, user["password_hash"]):
        locked, fail_msg = auth_db.record_failed_login(user["id"])
        return jsonify({"success": False, "message": fail_msg, "error": "Invalid password"}), 401

    if not user["is_active"]:
        otp_code = auth_db.generate_and_store_otp(user["id"], user["email"], "register")
        email_service.send_otp_email(user["email"], otp_code, "register")
        return jsonify({
            "success": False,
            "requires_otp": True,
            "email": user["email"],
            "message": "Account email has not been verified. A new 6-digit code has been dispatched.",
            "error": "Account inactive"
        }), 200

    auth_db.reset_failed_logins(user["id"])
    token = auth_db.create_session_token(user["id"], user["email"], user["username"])
    resp = make_response(jsonify({
        "success": True,
        "message": "Login successful.",
        "data": {"user": {"id": user["id"], "username": user["username"], "email": user["email"]}},
        "error": None
    }))
    resp.set_cookie('session_token', token, httponly=True, samesite='Lax', max_age=7*24*3600)
    return resp

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")

    user = auth_db.get_user_by_email_or_username(email)
    if user:
        otp_code = auth_db.generate_and_store_otp(user["id"], user["email"], "forgot_password")
        email_service.send_otp_email(user["email"], otp_code, "forgot_password")

    return jsonify({
        "success": True,
        "message": "If an account exists with this email, a 6-digit reset code has been sent.",
        "error": None
    })

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    otp_code = data.get("otp_code", "")
    new_password = data.get("new_password", "")

    ok, msg = auth_db.update_password_with_otp(email, otp_code, new_password)
    if not ok:
        return jsonify({"success": False, "message": msg, "error": msg}), 400

    return jsonify({
        "success": True,
        "message": msg,
        "error": None
    })

@app.route('/api/auth/resend-otp', methods=['POST'])
def resend_otp():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    purpose = data.get("purpose", "register")

    user = auth_db.get_user_by_email_or_username(email)
    if not user:
        return jsonify({"success": False, "message": "User not found.", "error": "Not found"}), 404

    otp_code = auth_db.generate_and_store_otp(user["id"], user["email"], purpose)
    email_service.send_otp_email(user["email"], otp_code, purpose)

    return jsonify({
        "success": True,
        "message": "A new verification code has been dispatched to your email.",
        "error": None
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    resp = make_response(jsonify({"success": True, "message": "Logged out successfully.", "error": None}))
    resp.set_cookie('session_token', '', max_age=0)
    return resp

@app.route('/api/auth/me', methods=['GET'])
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Not authenticated", "error": "Unauthorized"}), 401
    return jsonify({
        "success": True,
        "data": {"user": {"id": user["id"], "username": user["username"], "email": user["email"]}},
        "error": None
    })

# --- HARDWARE TELEMETRY & CONTROLS ---
@app.route('/api/process', methods=['POST'])
def process():
    if not request.data: return jsonify({"error": "empty frame"}), 400
    return jsonify(monitor.process_frame_bytes(request.data))

@app.route('/command/<cmd>', methods=['POST'])
def command(cmd):
    if cmd == 'calibrate': monitor.trigger_calibration()
    return jsonify({"status": "success"})

@app.route('/command/set_time/<int:seconds>', methods=['POST'])
def set_time(seconds):
    monitor.set_max_sitting_time(seconds)
    return jsonify({"status": "success"})

@app.route('/command/wearable', methods=['POST'])
def wearable():
    mac = request.json.get("mac", "")
    monitor.link_wearable(mac)
    return jsonify({"status": "linked", "mac": mac})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
# 🛡️ Security Architecture & Biometric Algorithm Deep Dive (`SECURITY_AND_ARCHITECTURE.md`)

This document provides an exhaustive technical analysis of the security implementations, cryptographic protections, and biometric computer vision algorithms powering the **Posture AI Platform**.

---

## 🔒 1. Security Architecture & Mandate Compliance

Posture AI strictly implements the enterprise security baseline defined in `DEVELOPMENT.md`:

### A. HttpOnly JWT Cookie Authentication (XSS Defense)
* **Vulnerability Mitigated:** Token theft via Cross-Site Scripting (XSS).
* **Implementation:** Session credentials are never stored in client-side `localStorage` or `sessionStorage`.
* The server issues a cryptographically signed JSON Web Token (JWT) in a cookie configured with:
  * `HttpOnly`: Inaccessible to browser JavaScript.
  * `SameSite=Lax`: Blocks unauthorized Cross-Site Request Forgery (CSRF) across external origins.
  * `Max-Age=604800`: Automatic expiration after 7 days.

### B. Password Hashing & Strength Verification
* **Algorithm:** **Bcrypt** with random salt generation (`bcrypt.gensalt()`).
* **Validation Rules:**
  1. Minimum 8 characters.
  2. At least one uppercase letter (`[A-Z]`).
  3. At least one lowercase letter (`[a-z]`).
  4. At least one numerical digit (`[0-9]`).
  5. At least one special character (`[!@#$%^&*(),.?":{}|<>]`).

### C. Brute-Force Defense & Account Lockout
* The system tracks consecutive failed login attempts in the database.
* Upon reaching **5 consecutive failed attempts**, the account enters a **15-minute temporary lockout** (`lockout_until = now + 15m`).
* Rotating-proxy automated password attacks are thwarted, protecting user accounts against dictionary cracking.

### D. Transactional Two-Factor OTP Engine (Resend API)
* Accounts are initially created in an inactive state (`is_active = 0`).
* **Cryptographic Generation:** Uses Python's `secrets.randbelow(900000) + 100000` to produce an unpredictable 6-digit code.
* **Security Constraints:**
  * Maximum validity window of **10 minutes**.
  * Capped at **5 failed entry attempts** before automatic invalidation.
  * Marked single-use (`is_used = 1`) immediately upon verification.
* **Email Channel:** Transmitted securely via Resend API from `posture@mail.flowkraft.xyz`.

### E. Rate Limiting Middleware
* All authentication endpoints (`/login`, `/register`, `/verify-otp`, `/forgot-password`) enforce strict IP rate limiting (maximum 15 requests per 60-second window).

### F. HTTP Security Headers
Every HTTP response is fortified with:
* `X-Frame-Options: DENY` (Blocks Clickjacking).
* `X-Content-Type-Options: nosniff` (Blocks MIME-type sniffing attacks).
* `Referrer-Policy: strict-origin-when-cross-origin`.

---

## 📐 2. Biometric Computer Vision Algorithm Deep Dive

### A. Jitter Elimination & Signal Smoothing (`EMASmoother`)
Webcam landmark coordinates inherently experience micro-tremors from lighting fluctuations and sensor noise. Posture AI filters key spatial features through an **Exponential Moving Average (EMA)** filter:

$$S_t = \alpha \cdot X_t + (1 - \alpha) \cdot S_{t-1}$$

Where $\alpha = 0.25$. This achieves a responsive balance between real-time tracking and silky smooth landmark coordinates without lag.

### B. Proximity-Invariant Scaling
To prevent users from falsely triggering "Standing" states when leaning closer to the camera:
1. Baseline shoulder width ($W_{\text{base}}$) and Y-coordinate ($Y_{\text{base}}$) are recorded during upright calibration.
2. The current frame's shoulder width ($W_{\text{curr}}$) is compared to establish a dynamic scale factor:
   $$\text{Scale Factor} = \frac{W_{\text{curr}}}{W_{\text{base}}}$$
3. The expected resting Y coordinate is recalculated frame-by-frame:
   $$Y_{\text{expected}} = 0.5 + (Y_{\text{base}} - 0.5) \cdot \text{Scale Factor}$$
4. The standing threshold line adapts accordingly:
   $$\text{Threshold}_Y = Y_{\text{expected}} - \text{Sensitivity Offset}$$

### C. The 5-Vector Anti-Cheat Detection Matrix
To prevent users from "cheating" the tracker (e.g. slumping back into a chair while craning their chin upward):

```text
                  +-----------------------------------+
                  |     5-VECTOR BIOMETRIC MATRIX     |
                  +-----------------------------------+
                                    |
     +------------------------------+------------------------------+
     |                              |                              |
     v                              v                              v
[ 1. NECK RATIO ]          [ 2. SHOULDER DROP ]           [ 3. HEAD PITCH ]
Slouching Trigger:         Anti-Cheat 1 Trigger:          Anti-Cheat 2 Trigger:
Neck < 88% of Baseline     Shoulder > +0.035 Below Base   Pitch > +0.045 Above Base
     |                              |                              |
     +------------------------------+------------------------------+
                                    |
     +------------------------------+------------------------------+
     |                                                             |
     v                                                             v
[ 4. HEAD BOWED ]                                             [ 5. LATERAL TILT ]
Downward Trigger:                                             Leaning Trigger:
Pitch < -0.065 Below Base                                     Shoulder Tilt > 10%
```

1. **Neck Ratio Compression ($< 88\%$):** Detects forward head posture and cervical spine slouching.
2. **Shoulder Drop ($> +0.035$):** Detects when the user has slumped backward into their chair. Even if they crane their neck up, their shoulders remain sunken, triggering **Bad Posture**.
3. **Head Pitch Craning ($> +0.045$):** Evaluates vertical delta between ear landmarks and nose landmark. Excessive upward chin tilting triggers **Bad Posture**.
4. **Head Bowed Down ($< -0.065$):** Identifies downward gaze (e.g. looking down at a mobile phone).
5. **Lateral Shoulder Tilt ($> 10\%$):** Detects asymmetrical spinal leaning or resting on one armrest.

### D. Majority Vote State Hysteresis
To prevent rapid flickering of states, raw inferences are fed into a double-ended queue (`deque(maxlen=6)`). A state transition only occurs when a majority vote ($\ge 50\% + 1$) agrees on the new state classification.

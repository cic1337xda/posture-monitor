# 📖 REST API Documentation (`API_DOCUMENTATION.md`)

This document provides a comprehensive endpoint reference for the **Posture AI Backend API**, covering authentication, OTP verification, computer vision frame inference, and hardware command execution.

---

## 🏛️ Standard Response Envelope

All API endpoints return JSON conforming to the 2026 standardized response envelope:

```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": { ... },
  "error": null
}
```

---

## 🏥 Health & System Endpoints

### 1. Healthcheck
* **Method:** `GET`
* **Route:** `/api/v1/health`
* **Authentication:** None (Public)
* **Response Example:**
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "timestamp": "2026-10-26T20:30:00+08:00"
  }
  ```

---

## 🔒 Authentication & OTP Endpoints

### 2. User Registration
* **Method:** `POST`
* **Route:** `/api/auth/register`
* **Rate Limit:** 15 requests / minute
* **Request Body:**
  ```json
  {
    "username": "johndoe",
    "email": "john@example.com",
    "password": "StrongPassword123!"
  }
  ```
* **Validation Rules:**
  * Username: $\ge 3$ characters.
  * Password: $\ge 8$ chars, containing uppercase, lowercase, number, and special character.
* **Behavior:** Creates account in inactive status (`is_active = 0`) and dispatches a 6-digit cryptographic OTP to the registered email via the Resend API.
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "message": "Account created! A 6-digit verification code has been sent to your email.",
    "data": { "email": "john@example.com" },
    "error": null
  }
  ```

---

### 3. Verify OTP & Activate Session
* **Method:** `POST`
* **Route:** `/api/auth/verify-otp`
* **Request Body:**
  ```json
  {
    "email": "john@example.com",
    "otp_code": "849201",
    "purpose": "register"
  }
  ```
* **Behavior:** Validates 6-digit OTP against expiration (10 minutes) and attempt limits ($\le 5$). Activates user account and sets a signed `session_token` cookie (`HttpOnly; SameSite=Lax; Max-Age=604800`).
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "message": "Verification successful.",
    "data": {
      "user": {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com"
      }
    },
    "error": null
  }
  ```

---

### 4. User Login
* **Method:** `POST`
* **Route:** `/api/auth/login`
* **Rate Limit:** 15 requests / minute
* **Request Body:**
  ```json
  {
    "identifier": "johndoe",
    "password": "StrongPassword123!"
  }
  ```
* **Behavior:** Checks lockout status (locks for 15 minutes after 5 failed attempts). Verifies Bcrypt hash. If user is inactive, automatically triggers an activation OTP email.
* **Success Response (200 OK):** Issues `session_token` cookie and returns user profile.

---

### 5. Forgot Password Request
* **Method:** `POST`
* **Route:** `/api/auth/forgot-password`
* **Request Body:**
  ```json
  {
    "email": "john@example.com"
  }
  ```
* **Behavior:** Generates a 6-digit reset OTP and emails it to the user. Returns a generic success message to prevent user enumeration attacks.

---

### 6. Reset Password with OTP
* **Method:** `POST`
* **Route:** `/api/auth/reset-password`
* **Request Body:**
  ```json
  {
    "email": "john@example.com",
    "otp_code": "849201",
    "new_password": "NewStrongPassword456!"
  }
  ```
* **Behavior:** Validates OTP and updates password hash upon satisfying password strength requirements.

---

### 7. User Logout
* **Method:** `POST`
* **Route:** `/api/auth/logout`
* **Behavior:** Clears the `session_token` cookie (`Max-Age=0`).

---

### 8. Current Session Profile
* **Method:** `GET`
* **Route:** `/api/auth/me`
* **Cookie Required:** `session_token`
* **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "user": {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com"
      }
    },
    "error": null
  }
  ```

---

## 👁️ Computer Vision & Inference Endpoints

### 9. Stream Frame Inference
* **Method:** `POST`
* **Route:** `/api/process`
* **Content-Type:** `image/jpeg` (Raw binary frame payload)
* **Body:** Binary JPEG byte stream from webcam canvas
* **Success Response (200 OK):**
  ```json
  {
    "state": "Sitting",
    "alert_level": "normal",
    "alert_message": "You're doing fine.",
    "remaining": 582,
    "fraction": 0.03,
    "bad_posture_duration": 0.0,
    "alarm": false,
    "metrics": "Neck: 98% | Drop: +0.01 | Pitch: -0.01",
    "calibrating": false,
    "calibration_progress": 0,
    "stand_up_count": 3,
    "recent_celebration": false,
    "landmarks": [
      { "x": 0.5123, "y": 0.3412, "visibility": 0.98 },
      ...
    ]
  }
  ```

---

## 🎮 Hardware Controls & Commands

### 10. Recalibrate Baseline
* **Method:** `POST`
* **Route:** `/command/calibrate`
* **Behavior:** Triggers a 25-frame calibration sequence to sample upright resting shoulder height, width, and neck ratio.

### 11. Custom Sitting Timer
* **Method:** `POST`
* **Route:** `/command/set_time/<int:seconds>`
* **Example:** `POST /command/set_time/300` (Sets maximum continuous sitting duration to 5 minutes).

### 12. Link ESP32 Wearable Watch
* **Method:** `POST`
* **Route:** `/command/wearable`
* **Request Body:**
  ```json
  {
    "mac": "70:04:1D:XX:XX:XX"
  }
  ```
* **Behavior:** Binds MAC address to MQTT topic `posture/wearable/<MAC>/command` and publishes confirmation payload `"linked"` to trigger a 300ms verification pulse on the watch.

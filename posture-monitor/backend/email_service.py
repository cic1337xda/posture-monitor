import os
import json
import urllib.request
import urllib.error

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "posture@mail.flowkraft.xyz")

def send_otp_email(to_email: str, otp_code: str, purpose: str = "register") -> bool:
    """
    Sends a 6-digit OTP email using Resend API.
    SOP Domain: mail.flowkraft.xyz
    """
    api_key = os.environ.get("RESEND_API_KEY", RESEND_API_KEY).strip()
    from_email = os.environ.get("RESEND_FROM_EMAIL", RESEND_FROM_EMAIL).strip()

    if not api_key:
        print("[EMAIL WARNING] RESEND_API_KEY is not configured. Simulating OTP:", otp_code)
        return True

    if purpose == "forgot_password":
        subject = "Posture AI - Password Reset Code"
        heading = "Reset Your Password"
        instruction = "We received a request to reset your password. Use the verification code below to set a new password."
    else:
        subject = "Posture AI - Verification Code"
        heading = "Activate Your Account"
        instruction = "Thank you for registering with Posture AI. Please use the verification code below to verify your email."

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>{subject}</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #0c111c; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #fdfdfe;">
      <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #0c111c; padding: 40px 20px;">
        <tr>
          <td align="center">
            <table width="100%" max-width="500" border="0" cellspacing="0" cellpadding="0" style="max-width: 500px; background: linear-gradient(135deg, rgba(25, 25, 27, 0.95) 0%, rgba(17, 17, 19, 0.95) 100%); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 24px; padding: 36px; box-shadow: 0 20px 50px rgba(0,0,0,0.6);">
              <tr>
                <td align="center" style="padding-bottom: 24px;">
                  <div style="display: inline-block; width: 44px; height: 44px; line-height: 44px; border-radius: 12px; background: #3d63dd; color: #ffffff; font-weight: bold; font-size: 20px; text-align: center;">P</div>
                  <h1 style="margin: 14px 0 6px 0; font-size: 22px; font-weight: 700; color: #ffffff; letter-spacing: -0.02em;">Posture AI</h1>
                  <p style="margin: 0; font-size: 13px; color: #8b8d98;">Intelligent Ergonomics & Posture Monitoring</p>
                </td>
              </tr>
              <tr>
                <td style="padding: 10px 0 24px 0;">
                  <h2 style="margin: 0 0 10px 0; font-size: 17px; font-weight: 600; color: #ffffff;">{heading}</h2>
                  <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #b9bbc6;">{instruction}</p>
                </td>
              </tr>
              <tr>
                <td align="center" style="padding: 20px 0;">
                  <div style="display: inline-block; padding: 16px 36px; background: rgba(61, 99, 221, 0.15); border: 1px solid #3d63dd; border-radius: 16px; font-family: monospace; font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #a6bff9;">
                    {otp_code}
                  </div>
                </td>
              </tr>
              <tr>
                <td style="padding-top: 10px;">
                  <p style="margin: 0; font-size: 12px; color: #8b8d98; line-height: 1.5; text-align: center;">
                    This one-time passcode will expire in <strong>10 minutes</strong>.<br>
                    If you did not request this, you can safely ignore this email.
                  </p>
                </td>
              </tr>
              <tr>
                <td style="padding-top: 30px; border-top: 1px solid rgba(255, 255, 255, 0.08); margin-top: 24px; text-align: center;">
                  <p style="margin: 0; font-size: 11px; color: #62636c;">
                    &copy; 2026 Posture AI &bull; Flowkraft Enterprise
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    payload = {
        "from": f"Posture AI <{from_email}>",
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }

    try:
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "PostureAI-Backend/1.0"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            print(f"[RESEND SUCCESS] Sent OTP to {to_email}. Response: {res_body}")
            return True
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"[RESEND HTTP ERROR {e.code}] Failed to send OTP to {to_email}: {err_msg}")
        return False
    except Exception as e:
        print(f"[RESEND EXCEPTION] Error sending OTP to {to_email}: {e}")
        return False

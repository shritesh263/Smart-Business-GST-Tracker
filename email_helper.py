"""
email_helper.py — GST Compliance Tracker
Handles sending GST invoice PDFs via Gmail SMTP.

SETUP INSTRUCTIONS:
-------------------
1. Open .env file in the project root.
2. Set SENDER_EMAIL to your Gmail address.
3. Set SENDER_APP_PASSWORD to your Gmail App Password.

   SENDER_APP_PASSWORD is NOT your regular Gmail password.
   Steps to generate an App Password:
     - Go to https://myaccount.google.com
     - Security → 2-Step Verification → must be ON
     - Then: Security → App Passwords
     - Select "Mail" and "Windows Computer" → Generate
     - Copy the 16-character password (with spaces) and paste it in .env
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import os


def send_invoice_email(receiver_email, buyer_name, seller_name,
                       invoice_number, total_amount, pdf_bytes):
    """
    Sends a GST invoice as a PDF attachment via Gmail SMTP.

    Args:
        receiver_email (str): The recipient's email address.
        buyer_name     (str): Name of the buyer (shown in email body).
        seller_name    (str): Name of the seller (shown in subject + body).
        invoice_number (str): Invoice number (e.g., "INV-1234").
        total_amount   (str or float): Grand total of the invoice.
        pdf_bytes      (bytes): Raw PDF bytes to attach.

    Returns:
        dict: {"success": True/False, "message": "..."}
    """

    load_dotenv()
    sender_email = os.getenv("SENDER_EMAIL", "").strip()
    app_password = os.getenv("SENDER_APP_PASSWORD", "").strip()

    # Guard: missing credentials
    if not sender_email or sender_email == "your_email@gmail.com":
        return {
            "success": False,
            "message": (
                "Sender email not configured. "
                "Open .env and set SENDER_EMAIL to your Gmail address."
            )
        }
    if not app_password or app_password == "your_16_digit_app_password":
        return {
            "success": False,
            "message": (
                "Gmail App Password not configured. "
                "Open .env, set SENDER_APP_PASSWORD. "
                "Generate one at: myaccount.google.com → Security → App Passwords."
            )
        }

    # ── Build email ──────────────────────────────────────────────────────────
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = f"GST Invoice {invoice_number} from {seller_name}"

    # Plain-text body
    body = f"""Dear {buyer_name},

Please find attached your GST Invoice {invoice_number}.

Invoice Details:
- Invoice Number : {invoice_number}
- Seller         : {seller_name}
- Total Amount   : Rs.{total_amount}

Kindly make the payment at your earliest convenience.

Regards,
{seller_name}

---
This is a system generated email from GST Compliance Tracker.
"""
    msg.attach(MIMEText(body, "plain"))

    # ── Attach PDF ────────────────────────────────────────────────────────────
    part = MIMEBase("application", "octet-stream")
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    safe_inv_no = str(invoice_number).replace(" ", "_").replace("/", "-")
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="Invoice_{safe_inv_no}.pdf"'
    )
    msg.attach(part)

    # ── Send via Gmail SMTP ───────────────────────────────────────────────────
    # Primary: port 587 with STARTTLS
    # Fallback: port 465 with SSL (if 587 is blocked on the network)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return {"success": True, "message": "Email sent successfully"}

    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": (
                "Gmail authentication failed. "
                "Check that SENDER_APP_PASSWORD in .env is a valid App Password "
                "(not your regular Gmail password) and 2-Step Verification is ON."
            )
        }

    except (ConnectionRefusedError, smtplib.SMTPConnectError, OSError):
        # Port 587 blocked — retry on port 465 with SSL
        try:
            server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15)
            server_ssl.ehlo()
            server_ssl.login(sender_email, app_password)
            server_ssl.sendmail(sender_email, receiver_email, msg.as_string())
            server_ssl.quit()
            return {"success": True, "message": "Email sent successfully (via port 465)"}
        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "message": (
                    "Gmail authentication failed on port 465 too. "
                    "Please verify your App Password in .env."
                )
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Both port 587 and 465 failed. Last error: {str(e)}"
            }

    except smtplib.SMTPException as e:
        return {"success": False, "message": f"SMTP error: {str(e)}"}

    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}"}

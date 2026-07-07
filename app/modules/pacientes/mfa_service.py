import os
import secrets
import smtplib
import httpx
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LOG_FILE_PATH = os.path.join(BASE_DIR, "mfa_codes.log")


def generate_mfa_code() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(6))


def log_mfa_code_locally(email: str, code: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] EMAIL: {email} | CODE: {code}\n"

    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(log_message)
    except Exception as e:
        print(f"[MFA] Error escribiendo log local: {e}")

    print("\n" + "=" * 60)
    print(f"[MFA ECO-SALUD] Código generado para: {email}")
    print(f"CÓDIGO MFA: {code}")
    print("=" * 60 + "\n")


def build_email_html(nombres: str, code: str) -> str:
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f4f7f6; padding: 20px; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px; border-top: 5px solid #007c89;">
          <h2 style="color: #007c89; text-align: center;">Portal de Pacientes ECOSALUD</h2>
          <p>Hola, <strong>{nombres}</strong>:</p>
          <p>Tu código de verificación es:</p>
          <div style="text-align: center; margin: 30px 0;">
            <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #007c89; background-color: #f0fdfa; padding: 12px 30px; border-radius: 6px;">
              {code}
            </span>
          </div>
          <p style="font-size: 0.9em; color: #666; text-align: center;">
            Este código es válido durante <strong>5 minutos</strong>.
          </p>
        </div>
      </body>
    </html>
    """


def send_mfa_brevo(email: str, nombres: str, code: str, html_content: str) -> bool:
    brevo_api_key = os.getenv("BREVO_API_KEY")
    brevo_sender_email = os.getenv("BREVO_SENDER_EMAIL")
    brevo_sender_name = os.getenv("BREVO_SENDER_NAME", "ECOSALUD")

    if not brevo_api_key or not brevo_sender_email:
        print("[MFA - Brevo] Faltan BREVO_API_KEY o BREVO_SENDER_EMAIL.")
        return False

    payload = {
        "sender": {
            "name": brevo_sender_name,
            "email": brevo_sender_email
        },
        "to": [
            {
                "email": email,
                "name": nombres
            }
        ],
        "subject": f"{code} es tu código de verificación de ECOSALUD",
        "htmlContent": html_content
    }

    headers = {
        "accept": "application/json",
        "api-key": brevo_api_key,
        "content-type": "application/json"
    }

    try:
        response = httpx.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers=headers,
            timeout=15
        )

        if response.status_code in (200, 201, 202):
            print(f"[MFA - Brevo] Correo enviado correctamente a {email}")
            return True

        print(f"[MFA - Brevo] Error {response.status_code}: {response.text}")
        return False

    except Exception as e:
        print(f"[MFA - Brevo] Error inesperado: {e}")
        return False


def send_mfa_smtp(email: str, nombres: str, code: str, html_content: str) -> bool:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_sender = os.getenv("SMTP_SENDER", smtp_user)

    if not smtp_host or not smtp_user or not smtp_password:
        print("[MFA - SMTP] SMTP no configurado.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{code} es tu código de verificación de ECOSALUD"
    msg["From"] = smtp_sender
    msg["To"] = email
    msg.attach(MIMEText(html_content, "html"))

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.starttls()

        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_sender, [email], msg.as_string())
        server.quit()

        print(f"[MFA - SMTP] Correo enviado correctamente a {email}")
        return True

    except Exception as e:
        print(f"[MFA - SMTP] Error: {e}")
        return False


def send_mfa_email(email: str, nombres: str, code: str) -> bool:
    html_content = build_email_html(nombres, code)

    if send_mfa_brevo(email, nombres, code, html_content):
        return True

    if send_mfa_smtp(email, nombres, code, html_content):
        return True

    return False


def send_mfa_code(email: str, nombres: str, code: str) -> bool:
    log_mfa_code_locally(email, code)

    enviado = send_mfa_email(email, nombres, code)

    if not enviado:
        print("[MFA] No se pudo enviar el correo. Configura BREVO o SMTP en el servidor.")

    return enviado

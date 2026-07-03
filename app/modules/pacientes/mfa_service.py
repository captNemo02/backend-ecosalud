import os
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# Path to log MFA codes locally
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LOG_FILE_PATH = os.path.join(BASE_DIR, "mfa_codes.log")

def generate_mfa_code() -> str:
    # Genera un código criptográficamente seguro de 6 dígitos
    return "".join(secrets.choice("0123456789") for _ in range(6))

def log_mfa_code_locally(email: str, code: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] EMAIL: {email} | CODE: {code}\n"
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(log_message)
    except Exception as e:
        print(f"Error escribiendo código MFA en archivo local: {e}")

    # Imprimir en consola de forma llamativa
    print("\n" + "=" * 60)
    print(f"  [MFA ECO-SALUD] Código enviado a: {email}")
    print(f"  CÓDIGO DE ACCESO (6 DÍGITOS): {code}")
    print(f"  Ver archivo de logs en: {LOG_FILE_PATH}")
    print("=" * 60 + "\n")

def send_mfa_resend(email: str, nombres: str, code: str, html_content: str) -> bool:
    resend_api_key = os.getenv("RESEND_API_KEY")
    if not resend_api_key:
        return False

    # Por defecto en desarrollo libre con Resend se usa el remitente "onboarding@resend.dev"
    # pero puedes cambiarlo a tu dominio configurando RESEND_SENDER
    resend_sender = os.getenv("RESEND_SENDER", "onboarding@resend.dev")

    print(f"[MFA - Resend] Enviando código {code} a {email}...")

    headers = {
        "Authorization": f"Bearer {resend_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "from": resend_sender,
        "to": [email],
        "subject": f"{code} es tu código de verificación de ECOSALUD",
        "html": html_content
    }

    try:
        import httpx
        response = httpx.post(
            "https://api.resend.com/emails",
            json=payload,
            headers=headers,
            timeout=10
        )
        if response.status_code in (200, 201):
            print(f"[MFA - Resend] Correo enviado exitosamente via Resend a {email}")
            return True
        else:
            print(f"[MFA - Resend] Error de Resend API ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"[MFA - Resend] Error al enviar via Resend API: {e}")
        return False

def send_mfa_brevo(email: str, nombres: str, code: str, html_content: str) -> bool:
    brevo_api_key = os.getenv("BREVO_API_KEY")
    if not brevo_api_key:
        return False

    brevo_sender_email = os.getenv("BREVO_SENDER_EMAIL", "leonardosalaza291@gmail.com")
    brevo_sender_name = os.getenv("BREVO_SENDER_NAME", "ECOSALUD")

    print(f"[MFA - Brevo] Enviando código {code} a {email} via Brevo...")

    headers = {
        "accept": "application/json",
        "api-key": brevo_api_key,
        "content-type": "application/json"
    }

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

    try:
        import httpx
        response = httpx.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers=headers,
            timeout=10
        )
        if response.status_code in (200, 201, 202):
            print(f"[MFA - Brevo] Correo enviado exitosamente via Brevo a {email}")
            return True
        else:
            print(f"[MFA - Brevo] Error de Brevo API ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"[MFA - Brevo] Error al enviar via Brevo API: {e}")
        return False

def send_mfa_email(email: str, nombres: str, code: str) -> bool:
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f4f7f6; padding: 20px; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-top: 5px solid #007c89;">
          <h2 style="color: #007c89; margin-top: 0; text-align: center;">Portal de Pacientes ECOSALUD</h2>
          <p>Hola, <strong>{nombres}</strong>:</p>
          <p>Has solicitado iniciar sesión en tu cuenta. Para completar tu acceso, utiliza el siguiente código de verificación de doble factor:</p>
          <div style="text-align: center; margin: 30px 0;">
            <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #007c89; background-color: #f0fdfa; padding: 12px 30px; border-radius: 6px; border: 1px dashed #007c89;">{code}</span>
          </div>
          <p style="font-size: 0.9em; color: #666; text-align: center;">Este código es válido durante <strong>5 minutos</strong>. Si no has iniciado esta sesión, por favor ignora este correo.</p>
          <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
          <p style="font-size: 0.8em; color: #999; text-align: center; margin-bottom: 0;">© 2026 ECOSALUD. Todos los derechos reservados.</p>
        </div>
      </body>
    </html>
    """

    # 1. Intentar enviar con Brevo API (si está configurada su API Key)
    if os.getenv("BREVO_API_KEY"):
        bre_success = send_mfa_brevo(email, nombres, code, html)
        if bre_success:
            return True

    # 2. Intentar enviar con Resend API (si está configurada su API Key)
    if os.getenv("RESEND_API_KEY"):
        res_success = send_mfa_resend(email, nombres, code, html)
        if res_success:
            return True

    # 3. Fallback a SMTP tradicional (si está configurado)
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port_str = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_sender = os.getenv("SMTP_SENDER", "no-reply@ecosalud.com")

    if not smtp_host or not smtp_user or not smtp_password:
        print("[MFA] SMTP no configurado (y Resend/Brevo API no configuradas o fallaron). Se omite el envío de correo.")
        return False

    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        smtp_port = 587

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"{code} es tu código de verificación de ECOSALUD"
    msg['From'] = smtp_sender
    msg['To'] = email
    msg.attach(MIMEText(html, 'html'))

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()

        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_sender, [email], msg.as_string())
        server.quit()
        print(f"[MFA] Correo enviado exitosamente via SMTP a {email}")
        return True
    except Exception as e:
        print(f"[MFA] Error al enviar correo SMTP: {e}")
        return False

def send_mfa_code(email: str, nombres: str, code: str):
    # Log local de respaldo (gratuito, seguro y fácil de usar en desarrollo)
    log_mfa_code_locally(email, code)
    # Intentar enviar por correo
    send_mfa_email(email, nombres, code)

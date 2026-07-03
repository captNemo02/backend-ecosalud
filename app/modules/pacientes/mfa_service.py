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

def send_mfa_email(email: str, nombres: str, code: str) -> bool:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port_str = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_sender = os.getenv("SMTP_SENDER", "no-reply@ecosalud.com")

    # Si falta la configuración básica, se omite el envío
    if not smtp_host or not smtp_user or not smtp_password:
        print("[MFA] SMTP no configurado en variables de entorno. Omitiendo envío de correo.")
        return False

    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        smtp_port = 587

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"{code} es tu código de verificación de ECOSALUD"
    msg['From'] = smtp_sender
    msg['To'] = email

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
        print(f"[MFA] Correo enviado exitosamente a {email}")
        return True
    except Exception as e:
        print(f"[MFA] Error al enviar correo SMTP: {e}")
        return False

def send_mfa_code(email: str, nombres: str, code: str):
    # Log local de respaldo (gratuito, seguro y fácil de usar en desarrollo)
    log_mfa_code_locally(email, code)
    # Intentar enviar por correo
    send_mfa_email(email, nombres, code)

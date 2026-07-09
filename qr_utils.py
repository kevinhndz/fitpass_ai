import qrcode
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import date
from dotenv import load_dotenv

load_dotenv()

GMAIL_REMITENTE    = os.environ.get("GMAIL_REMITENTE")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
QR_FOLDER           = os.path.join("static", "qr")

# SERVER_DOMAIN debe ser tu dominio en producción (ej. "tudominio.com")
# o la IP local solo mientras pruebas dentro del gimnasio.
# SERVER_PORT vacío si usas HTTPS/Nginx en el puerto 443 (producción).
SERVER_DOMAIN = os.environ.get("SERVER_DOMAIN", "localhost")
SERVER_PORT   = os.environ.get("SERVER_PORT", "5000")


def _asegurar_carpeta():
    os.makedirs(QR_FOLDER, exist_ok=True)


def _construir_url(cliente_id: int) -> str:
    if SERVER_PORT:
        return f"http://{SERVER_DOMAIN}:{SERVER_PORT}/validar/{cliente_id}"
    return f"https://{SERVER_DOMAIN}/validar/{cliente_id}"


def generar_qr(cliente_id: int, nombre: str, membresia: str,
               fecha_vencimiento: date) -> str:
    _asegurar_carpeta()

    url = _construir_url(cliente_id)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(fecha_vencimiento   )
    qr.make(fit=True)

    
    img = qr.make_image(fill_color="black", back_color="white")

    ruta = os.path.join(QR_FOLDER, f"qr_cliente_{cliente_id}.png")
    img.save(ruta)
    return ruta

def enviar_qr_por_correo(destinatario: str, nombre: str,
                          fecha_vencimiento: date, ruta_qr: str) -> bool:
    try:
        msg = MIMEMultipart("related")
        msg["Subject"] = "🏋️ Tu acceso Sport Fitness — Código QR"
        msg["From"]    = GMAIL_REMITENTE
        msg["To"]      = destinatario

        html = f"""
        <html><body style="background:#0d0d10;color:#fff;font-family:sans-serif;padding:32px;">
          <div style="max-width:480px;margin:auto;text-align:center;">
            <h1 style="color:#00d68f;">🏋️‍♂️ Sport Fitness</h1>
            <p style="font-size:16px;">Hola <strong>{nombre}</strong>, aquí está tu código de acceso.</p>
            <div style="background:#1a1a1e;border:1px solid #2c2c33;border-radius:16px;padding:24px;margin:24px 0;">
              <img src="cid:qr_imagen" style="width:220px;height:220px;" alt="Código QR de acceso">
              <p style="color:#a8a8b3;font-size:14px;margin-top:16px;">
                Válido hasta: <strong style="color:#00d68f;">{fecha_vencimiento.strftime('%d/%m/%Y')}</strong>
              </p>
            </div>
            <p style="color:#a8a8b3;font-size:13px;">
              Presenta este código al ingresar al gimnasio.<br>
              Los pagos se realizan presencialmente (efectivo o tarjeta).
            </p>
          </div>
        </body></html>
        """
        msg.attach(MIMEText(html, "html"))

        with open(ruta_qr, "rb") as f:
            img_mime = MIMEImage(f.read())
        img_mime.add_header("Content-ID", "<qr_imagen>")
        img_mime.add_header("Content-Disposition", "inline", filename="acceso_qr.png")
        msg.attach(img_mime)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_REMITENTE, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_REMITENTE, destinatario, msg.as_string())
        return True

    except Exception as e:
        print(f"[ERROR correo QR] {e}")
        return False


def enviar_correo_recordatorio(destinatario: str, nombre: str,
                                fecha_vencimiento: date, dias_restantes: int) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "⚠️ Tu membresía Sport Fitness vence pronto"
        msg["From"]    = GMAIL_REMITENTE
        msg["To"]      = destinatario

        if dias_restantes > 0:
            estado_texto = f"vence en <strong style='color:#f5a623;'>{dias_restantes} día(s)</strong>"
            instruccion  = "Acércate a recepción antes de esa fecha para renovarla."
            color_borde  = "#f5a623"
        else:
            retraso      = abs(dias_restantes)
            estado_texto = f"venció hace <strong style='color:#ff5c5c;'>{retraso} día(s)</strong>"
            instruccion  = "Por favor acércate a recepción a regularizar tu situación."
            color_borde  = "#ff5c5c"

        html = f"""
        <html><body style="background:#0d0d10;color:#fff;font-family:sans-serif;padding:32px;">
          <div style="max-width:480px;margin:auto;text-align:center;">
            <h1 style="color:#00d68f;">🏋️‍♂️ Sport Fitness</h1>
            <p style="font-size:16px;">Hola <strong>{nombre}</strong>,</p>
            <div style="background:#1a1a1e;border:2px solid {color_borde};border-radius:16px;padding:28px;margin:24px 0;">
              <p style="font-size:18px;margin:0;">Tu membresía {estado_texto}.</p>
              <p style="color:#a8a8b3;font-size:14px;margin-top:12px;">
                Fecha límite: <strong style="color:{color_borde};">{fecha_vencimiento.strftime('%d/%m/%Y')}</strong>
              </p>
              <p style="color:#fff;font-size:15px;margin-top:16px;">{instruccion}</p>
              <p style="color:#a8a8b3;font-size:13px;">Pagos: efectivo o tarjeta en recepción.</p>
            </div>
            <p style="color:#3a3a42;font-size:11px;">© 2026 Sport Fitness — Uso interno</p>
          </div>
        </body></html>
        """
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_REMITENTE, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_REMITENTE, destinatario, msg.as_string())
        return True

    except Exception as e:
        print(f"[ERROR correo recordatorio] {e}")
        return False
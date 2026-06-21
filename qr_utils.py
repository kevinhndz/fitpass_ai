"""
qr_utils.py — Módulo de generación de QR y envío por correo.

Responsabilidades:
  1. Generar imagen QR con datos del cliente y fecha de vencimiento.
  2. Guardar el QR en disco (carpeta static/qr/).
  3. Enviar el QR por correo vía SMTP (Gmail App Password).

Por qué SMTP y no una API de pago:
  Gmail SMTP es gratuito hasta ~500 correos/día y no requiere tarjeta.
  Para producción con más volumen se recomienda SendGrid o Mailgun.
"""

import qrcode
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import date, timedelta
import json

# ──────────────────────────────────────────────
# CONFIGURACIÓN — reemplaza con tus credenciales
# ──────────────────────────────────────────────
GMAIL_REMITENTE = "kh925063@gmail.com"          # tu cuenta Gmail
GMAIL_APP_PASSWORD = "yqnr vqoj ngsi rqwj"    # App Password de Google (16 chars)
QR_FOLDER = os.path.join("static", "qr")       # carpeta donde se guardan los QR


def _asegurar_carpeta():
    """Crea la carpeta de QR si no existe."""
    os.makedirs(QR_FOLDER, exist_ok=True)


def generar_qr(cliente_id: int, nombre: str, membresia: str,
               fecha_vencimiento: date) -> str:
    """
    Genera un código QR con los datos del cliente codificados como JSON.

    El contenido del QR es un JSON legible por cualquier escáner:
      {"id": 12, "nombre": "Ana López", "membresia": "mensual_estandar",
       "vence": "2026-07-21", "gym": "Sport Fitness"}

    Retorna la ruta relativa del archivo PNG generado.

    Por qué JSON en el QR:
      Permite que una app de escaneo futura valide la membresía
      descodificando el JSON sin depender de internet.
    """
    _asegurar_carpeta()

    payload = json.dumps({
        "id": cliente_id,
        "nombre": nombre,
        "membresia": membresia,
        "vence": str(fecha_vencimiento),
        "gym": "Sport Fitness"
    }, ensure_ascii=False)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # alta tolerancia a daños
        box_size=10,
        border=4
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#00d68f", back_color="#0d0d10")

    nombre_archivo = f"qr_cliente_{cliente_id}.png"
    ruta = os.path.join(QR_FOLDER, nombre_archivo)
    img.save(ruta)

    return ruta


def enviar_qr_por_correo(destinatario: str, nombre: str,
                          fecha_vencimiento: date, ruta_qr: str) -> bool:
    """
    Envía un correo HTML con el QR embebido como imagen inline (cid).

    Por qué imagen inline y no adjunto:
      Los clientes de correo móviles muestran imágenes inline directamente
      en el cuerpo del mensaje, sin que el usuario tenga que abrir adjuntos.
      Mejora la tasa de visualización del QR.

    Retorna True si el envío fue exitoso, False en caso de error.
    """
    try:
        msg = MIMEMultipart("related")
        msg["Subject"] = "🏋️ Tu acceso Sport Fitness — Código QR"
        msg["From"] = GMAIL_REMITENTE
        msg["To"] = destinatario

        # Cuerpo HTML con QR embebido
        html = f"""
        <html><body style="background:#0d0d10; color:#fff; font-family:sans-serif; padding:32px;">
          <div style="max-width:480px; margin:auto; text-align:center;">
            <h1 style="color:#00d68f;">🏋️‍♂️ Sport Fitness</h1>
            <p style="font-size:16px;">Hola <strong>{nombre}</strong>, aquí está tu código de acceso.</p>
            <div style="background:#1a1a1e; border:1px solid #2c2c33;
                        border-radius:16px; padding:24px; margin:24px 0;">
              <img src="cid:qr_imagen" style="width:220px; height:220px;"
                   alt="Código QR de acceso">
              <p style="color:#a8a8b3; font-size:14px; margin-top:16px;">
                Válido hasta: <strong style="color:#00d68f;">{fecha_vencimiento.strftime('%d/%m/%Y')}</strong>
              </p>
            </div>
            <p style="color:#a8a8b3; font-size:13px;">
              Presenta este código al ingresar al gimnasio.<br>
              Los pagos se realizan presencialmente (efectivo o tarjeta).
            </p>
            <p style="color:#3a3a42; font-size:11px; margin-top:32px;">
              © 2026 Sport Fitness — Uso interno
            </p>
          </div>
        </body></html>
        """

        alt_part = MIMEText(html, "html")
        msg.attach(alt_part)

        # Adjuntar la imagen con Content-ID para que el HTML la referencie
        with open(ruta_qr, "rb") as f:
            img_data = f.read()
        img_mime = MIMEImage(img_data)
        img_mime.add_header("Content-ID", "<qr_imagen>")
        img_mime.add_header("Content-Disposition", "inline", filename="acceso_qr.png")
        msg.attach(img_mime)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(GMAIL_REMITENTE, GMAIL_APP_PASSWORD)
            servidor.sendmail(GMAIL_REMITENTE, destinatario, msg.as_string())

        return True

    except Exception as e:
        print(f"[ERROR correo] {e}")
        return False
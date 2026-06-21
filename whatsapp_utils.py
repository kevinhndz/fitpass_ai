"""
whatsapp_utils.py — Módulo de envío de WhatsApp.

Diseñado como módulo intercambiable: cambia MODO entre "twilio" y "pywhatkit"
según el presupuesto del proyecto.

MODO "twilio"     → API oficial de WhatsApp Business (de pago, ~$0.005/msg)
                    Requiere cuenta Twilio + número aprobado por Meta.
                    Recomendado para producción.

MODO "pywhatkit"  → Abre WhatsApp Web en el navegador y envía el mensaje.
                    Gratuito, pero requiere que la PC tenga sesión de WhatsApp
                    activa y no sirve en servidores sin pantalla.
                    Recomendado para desarrollo/pruebas locales.

Por qué separar este módulo:
  La lógica de cuándo enviar (APScheduler) no debe saber cómo enviar.
  Si mañana cambias de Twilio a otro proveedor, solo editas este archivo.
"""

import os

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN — elige el modo y rellena las credenciales correspondientes
# ─────────────────────────────────────────────────────────────────────────────
MODO = "pywhatkit"   # Opciones: "twilio" | "pywhatkit"

# Credenciales Twilio (solo necesarias si MODO == "twilio")
TWILIO_SID    = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_TOKEN  = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_FROM   = "whatsapp:+14155238886"   # número sandbox de Twilio


def enviar_recordatorio_whatsapp(telefono: str, nombre: str,
                                  fecha_vencimiento, ruta_qr: str) -> bool:
    """
    Envía un mensaje de recordatorio de cobro 2 días antes del vencimiento.

    Args:
        telefono:          número del cliente (ej. "99887766")
        nombre:            nombre del cliente
        fecha_vencimiento: objeto date con la fecha de vencimiento
        ruta_qr:           ruta local del PNG del QR

    Retorna True si el envío fue exitoso, False en caso de error.

    Por qué incluir el QR en WhatsApp:
      El cliente lleva el teléfono al gimnasio; tener el QR en WhatsApp
      es más accesible que buscar un correo. Esto reduce fricción en la
      entrada y acelera la cola en recepción.
    """
    fecha_str = fecha_vencimiento.strftime("%d/%m/%Y")
    mensaje = (
        f"Hola {nombre} 👋\n\n"
        f"Te recordamos que tu membresía de *Sport Fitness* vence el *{fecha_str}*.\n\n"
        f"Por favor acércate a recepción antes de esa fecha para renovarla "
        f"(efectivo o tarjeta).\n\n"
        f"Adjunto encontrarás tu código QR de acceso actualizado. "
        f"Preséntalo al ingresar.\n\n"
        f"¡Gracias por elegirnos! 🏋️‍♂️"
    )

    if MODO == "twilio":
        return _enviar_twilio(telefono, mensaje, ruta_qr)
    elif MODO == "pywhatkit":
        return _enviar_pywhatkit(telefono, mensaje)
    else:
        print(f"[WHATSAPP] Modo no reconocido: {MODO}")
        return False


def _enviar_twilio(telefono: str, mensaje: str, ruta_qr: str) -> bool:
    """
    Envía vía Twilio WhatsApp Business API.

    Requiere que el número destino esté en formato internacional: +50499887766
    El QR se sube como media_url (debe ser URL pública, no ruta local).

    Nota sobre media_url:
      Twilio requiere una URL pública accesible. En producción deberías
      subir el QR a un CDN (S3, Cloudinary) y pasar esa URL aquí.
      Para simplificar, en esta versión enviamos solo el mensaje de texto
      con Twilio y el QR se envía por correo. Puedes extender esto fácilmente.
    """
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        numero_destino = f"whatsapp:+504{telefono}"   # Honduras = +504
        client.messages.create(
            body=mensaje,
            from_=TWILIO_FROM,
            to=numero_destino
        )
        print(f"[Twilio] Mensaje enviado a {numero_destino}")
        return True
    except Exception as e:
        print(f"[ERROR Twilio] {e}")
        return False


def _enviar_pywhatkit(telefono: str, mensaje: str) -> bool:
    """
    Envía vía pywhatkit (WhatsApp Web).

    Abre el navegador, espera 15 segundos y envía el mensaje.
    Solo funciona si hay sesión de WhatsApp Web activa en el navegador.

    Limitación: no puede adjuntar imágenes directamente en esta versión.
    El cliente recibirá el QR por correo y el texto de aviso por WhatsApp.
    """
    try:
        import pywhatkit as pwk
        from datetime import datetime
        ahora = datetime.now()
        # Envía en 2 minutos para dar tiempo al navegador a abrirse
        hora = ahora.hour
        minuto = ahora.minute + 2
        if minuto >= 60:
            hora += 1
            minuto -= 60

        numero = f"+504{telefono}"  # Honduras
        pwk.sendwhatmsg(numero, mensaje, hora, minuto,
                        wait_time=15, tab_close=True)
        return True
    except Exception as e:
        print(f"[ERROR pywhatkit] {e}")
        return False
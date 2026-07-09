import os
from datetime import date

MODO = "desactivado"

TWILIO_SID   = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_FROM  = "whatsapp:+14155238886"


def _parsear_fecha(fecha) -> date:
    if isinstance(fecha, str):
        return date.fromisoformat(fecha)
    return fecha


def enviar_recordatorio_whatsapp(telefono: str, nombre: str, fecha_vencimiento, ruta_qr: str) -> bool:
    fecha_vencimiento = _parsear_fecha(fecha_vencimiento)
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
        print(f"[WHATSAPP] Modo desactivado en producción")
        return False


def _enviar_twilio(telefono: str, mensaje: str, ruta_qr: str) -> bool:
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        numero_destino = f"whatsapp:+504{telefono}"
        client.messages.create(body=mensaje, from_=TWILIO_FROM, to=numero_destino)
        print(f"[Twilio] Mensaje enviado a {numero_destino}")
        return True
    except Exception as e:
        print(f"[ERROR Twilio] {e}")
        return False


def _enviar_pywhatkit(telefono: str, mensaje: str) -> bool:
    try:
        import pywhatkit as pwk
        from datetime import datetime
        ahora = datetime.now()
        hora = ahora.hour
        minuto = ahora.minute + 2
        if minuto >= 60:
            hora += 1
            minuto -= 60
        numero = f"+504{telefono}"
        pwk.sendwhatmsg(numero, mensaje, hora, minuto, wait_time=15, tab_close=True)
        return True
    except Exception as e:
        print(f"[ERROR pywhatkit] {e}")
        return False
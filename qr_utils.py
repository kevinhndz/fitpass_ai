import os
import requests
from datetime import date, datetime
from dotenv import load_dotenv

load_dotenv()

# Configuración de la API de WhatsApp (UltraMsg u otra similar)
WHATSAPP_API_URL = os.environ.get("WHATSAPP_API_URL")
WHATSAPP_TOKEN   = os.environ.get("WHATSAPP_TOKEN")
WHATSAPP_MODO    = os.environ.get("WHATSAPP_MODO", "desactivado").lower()

def enviar_qr_por_whatsapp(telefono: str, nombre: str, membresia: str, 
                           fecha_vencimiento: date, ruta_imagen_qr: str) -> bool:
    """
    Envía el mensaje de bienvenida y el código QR de acceso por WhatsApp.
    Si WHATSAPP_MODO es 'desactivado', simula el envío exitoso sin consumir créditos.
    """
    # 1. Asegurar que la fecha sea un objeto date/datetime antes de usar strftime
    if isinstance(fecha_vencimiento, str):
        try:
            # Intenta convertir formato YYYY-MM-DD
            fecha_vencimiento = date.fromisoformat(fecha_vencimiento)
        except ValueError:
            try:
                # Por si acaso viene con hora YYYY-MM-DD HH:MM:SS
                fecha_vencimiento = datetime.strptime(fecha_vencimiento.split(" ")[0], "%Y-%m-%d").date()
            except ValueError:
                print(f"[WHATSAPP] No se pudo parsear la fecha: {fecha_vencimiento}")
                # Si falla el parseo, lo dejamos como string para evitar el crash total
                fecha_str = fecha_vencimiento
                return False

    # Ahora sí podemos hacer el strftime de forma segura
    fecha_str = fecha_vencimiento.strftime("%d/%m/%Y")

    # 2. Verificar el modo después de procesar los datos de entrada
    if WHATSAPP_MODO == "desactivado":
        print("[WHATSAPP] Modo no reconocido o desactivado. Simulación de envío exitosa.")
        return True

    if not WHATSAPP_API_URL or not WHATSAPP_TOKEN:
        print("[WHATSAPP] Error: WHATSAPP_API_URL o WHATSAPP_TOKEN no configurados en .env")
        return False

    # Limpiar el teléfono (quitar espacios o caracteres raros)
    telefono_limpio = "".join(filter(str.isdigit, telefono))
    
    # Asegurar que tenga el código de país (ej. Honduras 504 si no lo tiene)
    if not telefono_limpio.startswith("504") and len(telefono_limpio) == 8:
        telefono_limpio = f"504{telefono_limpio}"

    # Construir el mensaje de texto
    mensaje = (
        f"🏋️‍♂️ *¡Bienvenido a Sport Fitness, {nombre}!* 🏋️‍♂️\n\n"
        f"Tu inscripción a la membresía *{membresia}* ha sido exitosa.\n"
        f"📅 *Vence el:* {fecha_str}\n\n"
        f"Te adjuntamos tu *Código QR de acceso*. Preséntalo en la entrada cada vez que ingreses al gimnasio.\n\n"
        f"¡A darle con todo al entrenamiento! 💪🔥"
    )

    try:
        # Enviar la imagen junto con el texto (Depende del formato exacto de tu API, ej: Ultramsg)
        payload = {
            "token": WHATSAPP_TOKEN,
            "to": telefono_limpio,
            "image": f"{requests.utils.requote_uri(ruta_imagen_qr)}", # O la URL pública si corresponde
            "caption": mensaje
        }
        
        headers = {"content-type": "application/x-www-form-urlencoded"}
        
        # Ajusta el endpoint según la API que utilices (ej: /messages/image)
        url_endpoint = f"{WHATSAPP_API_URL.rstrip('/')}/messages/image"
        
        response = requests.post(url_endpoint, data=payload, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            print(f"[WHATSAPP] Mensaje enviado correctamente a {telefono_limpio}")
            return True
        else:
            print(f"[WHATSAPP] Error en la API de WhatsApp. Status: {response.status_code}, Response: {response.text}")
            return False

    except Exception as e:
        print(f"[WHATSAPP] Excepción al intentar enviar mensaje: {e}")
        return False
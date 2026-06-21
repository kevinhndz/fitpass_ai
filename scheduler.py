"""
scheduler.py — Recordatorios automáticos de vencimiento.

Usa APScheduler (Advanced Python Scheduler) para ejecutar un job
cada día a las 09:00 AM que busca clientes que vencen en 2 días
y les envía un recordatorio por WhatsApp y correo.

Por qué APScheduler y no cron:
  APScheduler corre dentro del mismo proceso de Flask. No requiere
  configurar cron del sistema operativo ni permisos adicionales.
  Es fácil de arrancar, detener y modificar desde Python.
  Para producción a mayor escala se recomendaría Celery + Redis,
  pero para un negocio pequeño APScheduler es perfecto.

Por qué 09:00 AM:
  Es una hora razonable para que el cliente reciba el mensaje
  y tenga tiempo de ir al gimnasio ese día o el siguiente.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date, timedelta
from qr_utils import generar_qr, enviar_qr_por_correo
from whatsapp_utils import enviar_recordatorio_whatsapp


def _job_recordatorios(conectar_fn):
    """
    Job principal: busca clientes que vencen en exactamente 2 días
    y les envía recordatorio por WhatsApp y correo con su QR.

    Por qué exactamente 2 días (no "menos de 2"):
      Si buscáramos "vence dentro de ≤2 días" el cliente recibiría
      un mensaje cada día durante esos 2 días, lo cual es molesto.
      Con "exactamente en 2 días" el recordatorio es único y puntual.
    """
    objetivo = date.today() + timedelta(days=2)

    db = conectar_fn()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM clientes WHERE fecha_vencimiento = %s",
        (objetivo,)
    )
    clientes = cursor.fetchall()
    cursor.close()
    db.close()

    print(f"[Scheduler] {date.today()} — {len(clientes)} cliente(s) vencen el {objetivo}")

    for c in clientes:
        # Regenerar el QR con la fecha de vencimiento actual (no renovar, solo recordar)
        ruta_qr = generar_qr(
            cliente_id=c["id"],
            nombre=c["nombre"],
            membresia=c["membresia"],
            fecha_vencimiento=c["fecha_vencimiento"]
        )

        # Enviar por correo
        ok_correo = enviar_qr_por_correo(
            destinatario=c["correo"],
            nombre=c["nombre"],
            fecha_vencimiento=c["fecha_vencimiento"],
            ruta_qr=ruta_qr
        )

        # Enviar por WhatsApp
        ok_wa = enviar_recordatorio_whatsapp(
            telefono=c["telefono"],
            nombre=c["nombre"],
            fecha_vencimiento=c["fecha_vencimiento"],
            ruta_qr=ruta_qr
        )

        estado = "✓ correo" if ok_correo else "✗ correo"
        estado += " | ✓ WhatsApp" if ok_wa else " | ✗ WhatsApp"
        print(f"  → {c['nombre']} ({c['correo']}) — {estado}")


def iniciar_scheduler(conectar_fn):
    """
    Arranca el scheduler en background y programa el job diario.

    Args:
        conectar_fn: referencia a la función conectar_base_datos()
                     del módulo principal. Se pasa como argumento
                     para evitar importaciones circulares.

    El scheduler se inicia con daemon=True para que se detenga
    automáticamente cuando Flask se cierra, sin necesidad de
    llamar scheduler.shutdown() manualmente.
    """
    scheduler = BackgroundScheduler(daemon=True)

    scheduler.add_job(
        func=lambda: _job_recordatorios(conectar_fn),
        trigger="cron",
        hour=9,
        minute=0,
        id="recordatorio_vencimiento",
        replace_existing=True
    )

    scheduler.start()
    print("[Scheduler] Iniciado — recordatorios diarios a las 09:00 AM")
    return scheduler
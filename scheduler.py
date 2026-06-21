from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date, timedelta
from qr_utils import generar_qr, enviar_qr_por_correo, enviar_correo_recordatorio
from whatsapp_utils import enviar_recordatorio_whatsapp


def _job_recordatorios(conectar_fn):
    """
    Corre cada día a las 9AM.
    Busca clientes que vencen EXACTAMENTE en 2 días y les manda aviso por correo.
    """
    objetivo = date.today() + timedelta(days=2)

    db     = conectar_fn()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM clientes WHERE fecha_vencimiento = %s", (objetivo,))
    clientes = cursor.fetchall()
    cursor.close()
    db.close()

    print(f"[Scheduler] {date.today()} — {len(clientes)} cliente(s) vencen el {objetivo}")

    for c in clientes:
        # Correo de recordatorio de pago (el nuevo, con mensaje claro)
        ok_correo = enviar_correo_recordatorio(
            destinatario    = c["correo"],
            nombre          = c["nombre"],
            fecha_vencimiento = c["fecha_vencimiento"],
            dias_restantes  = 2
        )

        # WhatsApp (opcional, si está configurado)
        ruta_qr = generar_qr(c["id"], c["nombre"], c["membresia"], c["fecha_vencimiento"])
        ok_wa   = enviar_recordatorio_whatsapp(
            telefono          = c["telefono"],
            nombre            = c["nombre"],
            fecha_vencimiento = c["fecha_vencimiento"],
            ruta_qr           = ruta_qr
        )

        print(f"  → {c['nombre']} — correo={'✓' if ok_correo else '✗'} wa={'✓' if ok_wa else '✗'}")


def iniciar_scheduler(conectar_fn):
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        func            = lambda: _job_recordatorios(conectar_fn),
        trigger         = "cron",
        hour            = 9,
        minute          = 0,
        id              = "recordatorio_vencimiento",
        replace_existing= True
    )
    scheduler.start()
    print("[Scheduler] Iniciado — recordatorios diarios a las 09:00 AM")
    return scheduler
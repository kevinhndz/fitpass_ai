from datetime import date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal
from services.clientes import ClienteService
from qr_utils import generar_qr, enviar_correo_recordatorio
from whatsapp_utils import enviar_recordatorio_whatsapp


def _job_recordatorios():
    objetivo = date.today() + timedelta(days=2)
    db = SessionLocal()
    try:
        clientes = ClienteService().vencen_el(db, objetivo)
        print(f"[Scheduler] {date.today()} — {len(clientes)} cliente(s) activos vencen el {objetivo}")
        for cliente in clientes:
            ok_correo = enviar_correo_recordatorio(cliente.correo, cliente.nombre, cliente.fecha_vencimiento, 2) if cliente.correo else False
            ruta_qr = generar_qr(cliente.id, cliente.nombre, cliente.membresia, cliente.fecha_vencimiento)
            ok_wa = enviar_recordatorio_whatsapp(cliente.telefono, cliente.nombre, cliente.fecha_vencimiento, ruta_qr) if cliente.telefono else False
            print(f"  → {cliente.nombre} — correo={'✓' if ok_correo else '✗'} wa={'✓' if ok_wa else '✗'}")
    finally:
        db.close()


def iniciar_scheduler():
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(_job_recordatorios, trigger="cron", hour=9, minute=0, id="recordatorio_vencimiento", replace_existing=True)
    scheduler.start()
    print("[Scheduler] Iniciado — recordatorios diarios a las 09:00 AM")
    return scheduler

import os
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import require_user
from schemas import ClienteCreate, ClienteRead, ClienteUpdate
from services.clientes import ClienteService
from qr_utils import generar_qr, enviar_qr_por_correo
from whatsapp_utils import enviar_recordatorio_whatsapp

router = APIRouter(prefix="/api")
service = ClienteService()


@router.get("/clientes", response_model=list[ClienteRead])
def obtener_clientes(buscar: str | None = Query(default=None), db: Session = Depends(get_db), _=Depends(require_user)):
    return service.listar(db, buscar)


@router.post("/registrar")
def registrar_cliente(data: ClienteCreate, db: Session = Depends(get_db), _=Depends(require_user)):
    cliente = service.registrar(db, data)
    ruta_qr = generar_qr(cliente.id, cliente.nombre, cliente.membresia, cliente.fecha_vencimiento)
    correo_ok = enviar_qr_por_correo(cliente.correo, cliente.nombre, cliente.fecha_vencimiento, ruta_qr) if cliente.correo else False
    nota = " QR enviado a su correo." if correo_ok else " (No se pudo enviar el correo.)"
    return {"mensaje_pantalla": f"Cliente {cliente.nombre} registrado.{nota}", "cliente_id": cliente.id}


@router.put("/clientes/{client_id}")
def actualizar_cliente(client_id: int, data: ClienteUpdate, db: Session = Depends(get_db), _=Depends(require_user)):
    if not service.actualizar(db, client_id, data):
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"mensaje_pantalla": "Cliente actualizado correctamente."}


@router.delete("/clientes/{client_id}")
def eliminar_cliente(client_id: int, db: Session = Depends(get_db), _=Depends(require_user)):
    if not service.eliminar(db, client_id):
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"mensaje_pantalla": "Cliente eliminado del sistema."}


@router.get("/reportes/hoy", response_model=list[ClienteRead])
def obtener_reportes_hoy(db: Session = Depends(get_db), _=Depends(require_user)):
    return service.vencen_hoy(db)


@router.post("/clientes/{client_id}/qr")
def regenerar_qr(client_id: int, db: Session = Depends(get_db), _=Depends(require_user)):
    cliente = service.renovar(db, client_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    ruta_qr = generar_qr(cliente.id, cliente.nombre, cliente.membresia, cliente.fecha_vencimiento)
    correo_ok = enviar_qr_por_correo(cliente.correo, cliente.nombre, cliente.fecha_vencimiento, ruta_qr) if cliente.correo else False
    wa_ok = enviar_recordatorio_whatsapp(cliente.telefono, cliente.nombre, cliente.fecha_vencimiento, ruta_qr) if cliente.telefono else False
    return {"mensaje_pantalla": f"Membresía renovada y QR generado para {cliente.nombre}. {'Correo enviado.' if correo_ok else 'Correo no enviado.'}"}


@router.get("/validar/{client_id}")
def api_validar(client_id: int, db: Session = Depends(get_db)):
    cliente = service.repository.find(db, client_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"id": cliente.id, "nombre": cliente.nombre, "telefono": cliente.telefono, "membresia": cliente.membresia, "fecha_inicio": str(cliente.fecha_inicio), "fecha_vencimiento": str(cliente.fecha_vencimiento)}


@router.get("/qr/{client_id}")
def ver_qr(client_id: int):
    ruta = os.path.join("static", "qr", f"qr_cliente_{client_id}.png")
    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="QR no generado aún")
    return FileResponse(ruta, media_type="image/png")

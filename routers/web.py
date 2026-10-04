from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from routers.auth import current_user

router = APIRouter()


@router.get("/")
def dashboard(request: Request, user=Depends(current_user)):
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return FileResponse("static/registro.html")


@router.get("/validar/{client_id}")
def pagina_validar(client_id: int):
    return FileResponse("static/validar.html")

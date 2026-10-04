from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, FileResponse
from sqlalchemy.orm import Session
from database import get_db
from services.auth import AuthService

router = APIRouter()
auth_service = AuthService()


def current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return auth_service.get_user(db, int(user_id))


def require_user(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    return user


@router.get("/login")
def login_page():
    return FileResponse("static/login.html")


@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, username, password)
    if not user:
        return FileResponse("static/login.html", status_code=401)
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

from datetime import date
from pydantic import BaseModel, ConfigDict


class Credenciales(BaseModel):
    username: str
    password: str


class ClienteCreate(BaseModel):
    nombre: str
    whatsapp: str | None = None
    correo: str | None = None
    membresia: str | None = None


class ClienteUpdate(BaseModel):
    nombre: str
    whatsapp: str | None = None
    correo: str | None = None
    membresia: str | None = None


class ClienteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    telefono: str | None
    fecha_inicio: date | None
    fecha_vencimiento: date | None
    estado: str
    correo: str | None
    membresia: str | None
    user_id: int | None

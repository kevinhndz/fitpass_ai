from datetime import date, timedelta
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from schemas import ClienteCreate, ClienteUpdate
from tablas import Cliente


class ClienteRepository:
    def list_all(self, db: Session, buscar: str | None = None) -> list[Cliente]:
        query = select(Cliente).order_by(Cliente.id)
        if buscar:
            term = f"%{buscar}%"
            query = query.where(or_(Cliente.nombre.like(term), Cliente.telefono.like(term), Cliente.correo.like(term)))
        return list(db.scalars(query).all())

    def find(self, db: Session, client_id: int) -> Cliente | None:
        return db.get(Cliente, client_id)

    def create(self, db: Session, data: ClienteCreate) -> Cliente:
        today = date.today()
        cliente = Cliente(nombre=data.nombre, telefono=data.whatsapp, correo=data.correo, membresia=data.membresia, fecha_inicio=today, fecha_vencimiento=today + timedelta(days=30), estado="Activo")
        db.add(cliente)
        db.commit()
        db.refresh(cliente)
        return cliente

    def update(self, db: Session, cliente: Cliente, data: ClienteUpdate) -> Cliente:
        cliente.nombre, cliente.telefono, cliente.correo, cliente.membresia = data.nombre, data.whatsapp, data.correo, data.membresia
        db.commit()
        db.refresh(cliente)
        return cliente

    def delete(self, db: Session, cliente: Cliente) -> None:
        db.delete(cliente)
        db.commit()

    def due_today(self, db: Session) -> list[Cliente]:
        return list(db.scalars(select(Cliente).where(Cliente.fecha_vencimiento == date.today())).all())

    def due_on(self, db: Session, target: date) -> list[Cliente]:
        return list(db.scalars(select(Cliente).where(Cliente.fecha_vencimiento == target, Cliente.estado == "Activo")).all())

from datetime import date, timedelta
from sqlalchemy.orm import Session
from repositories.clientes import ClienteRepository
from schemas import ClienteCreate, ClienteUpdate


class ClienteService:
    def __init__(self, repository: ClienteRepository | None = None):
        self.repository = repository or ClienteRepository()

    def listar(self, db: Session, buscar: str | None = None):
        return self.repository.list_all(db, buscar)

    def registrar(self, db: Session, data: ClienteCreate):
        return self.repository.create(db, data)

    def actualizar(self, db: Session, client_id: int, data: ClienteUpdate):
        cliente = self.repository.find(db, client_id)
        if not cliente:
            return None
        return self.repository.update(db, cliente, data)

    def eliminar(self, db: Session, client_id: int):
        cliente = self.repository.find(db, client_id)
        if not cliente:
            return False
        self.repository.delete(db, cliente)
        return True

    def renovar(self, db: Session, client_id: int):
        cliente = self.repository.find(db, client_id)
        if not cliente:
            return None
        cliente.fecha_inicio = date.today()
        cliente.fecha_vencimiento = date.today() + timedelta(days=30)
        cliente.estado = "Activo"
        db.commit()
        db.refresh(cliente)
        return cliente

    def vencen_hoy(self, db: Session):
        return self.repository.due_today(db)

    def vencen_el(self, db: Session, target: date):
        return self.repository.due_on(db, target)

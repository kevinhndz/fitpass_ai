from sqlalchemy import select
from sqlalchemy.orm import Session
from tablas import Usuario


class UsuarioRepository:
    def find_by_id(self, db: Session, user_id: int) -> Usuario | None:
        return db.scalar(select(Usuario).where(Usuario.id == user_id))

    def find_by_username(self, db: Session, username: str) -> Usuario | None:
        return db.scalar(select(Usuario).where(Usuario.username == username))

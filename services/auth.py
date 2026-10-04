from werkzeug.security import check_password_hash
from sqlalchemy.orm import Session
from repositories.usuarios import UsuarioRepository


class AuthService:
    def __init__(self, repository: UsuarioRepository | None = None):
        self.repository = repository or UsuarioRepository()

    def authenticate(self, db: Session, username: str, password: str):
        user = self.repository.find_by_username(db, username)
        return user if user and check_password_hash(user.password_hash, password) else None

    def get_user(self, db: Session, user_id: int):
        return self.repository.find_by_id(db, user_id)

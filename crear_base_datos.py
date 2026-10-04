import os

from dotenv import load_dotenv
from sqlalchemy import select
from werkzeug.security import generate_password_hash

from database import Base, SessionLocal, engine
from tablas import Usuario

load_dotenv()


def crear_base_datos():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.scalar(select(Usuario).where(Usuario.username == "admin")):
            db.add(Usuario(username="admin", password_hash=generate_password_hash(os.getenv("ADMIN_PASSWORD", "admin123"))))
            db.commit()
            print("Usuario administrador creado")
        else:
            print("La base de datos y el usuario administrador ya existen")
    finally:
        db.close()


if __name__ == "__main__":
    crear_base_datos()

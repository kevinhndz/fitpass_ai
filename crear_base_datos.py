import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.environ.get("DB_PATH", "fitpass.db")

def crear_base_datos():
    if os.path.exists(DB_PATH):
        print(f"La base de datos {DB_PATH} ya existe")
        return

    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()
    
    # Tabla de usuarios para autenticación
    cursor.execute('''
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # Tabla principal de clientes
    cursor.execute('''
        CREATE TABLE clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            fecha_inicio DATE,
            fecha_vencimiento DATE,
            estado TEXT DEFAULT 'Activo',
            correo TEXT,
            membresia TEXT,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES usuarios(id)
        )
    ''')
    
    # Ingresar un usuario administrador (el cambio recomendado)
    # ⚠️ MODIFIQUE LA CONTRASEÑA EN .env ANTES DE CREAR LA BASE DE DATOS
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    from werkzeug.security import generate_password_hash
    
    cursor.execute(
        '''INSERT INTO usuarios (username, password_hash) VALUES (?, ?)''',
        ('admin', generate_password_hash(admin_password))
    )
    
    conexion.commit()
    conexion.close()
    print(f"Base de datos SQLite {DB_PATH} creada exitosamente")

if __name__ == '__main__':
    crear_base_datos()
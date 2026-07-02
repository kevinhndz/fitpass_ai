import sqlite3
import os
from datetime import date, timedelta
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

DB_PATH = os.environ.get("DB_PATH", "fitpass.db")

def verificar_e_integridad():
    print(f"Verificando integridad de {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = c.fetchall()
    
    print(f"\nTablas encontradas ({len(tablas)}):")
    for t in tablas:
        tabla = t['name']
        print(f"  [TABLA] {tabla}")
        c.execute(f"SELECT COUNT(*) as count FROM {tabla}")
        total = c.fetchone()['count']
        print(f"     {total} filas")
    
    if len(tablas) == 0:
        print("\nERROR: No hay tablas en la base de datos")
        print("Ejecute 'python crear_base_datos.py' para crear esquemas")
        return False
    
    for tabla in tablas:
        if tabla['name'] in ['usuarios', 'clientes']:
            c.execute(f"PRAGMA table_info({tabla['name']})")
            columnas = c.fetchall()
            print(f"\n[COLUMNAS] {tabla['name']}:")
            for col in columnas:
                print(f"   - {col['name']}")
    
    if 'usuarios' in [t['name'] for t in tablas]:
        c.execute("SELECT username, password_hash FROM usuarios")
        usuarios = c.fetchall()
        print(f"\nUsuarios ({len(usuarios)}):")
        for u in usuarios:
            print(f"   - username: {u['username']}")
    
    if 'clientes' in [t['name'] for t in tablas]:
        c.execute("SELECT id, nombre, telefono, fecha_vencimiento FROM clientes ORDER BY fecha_vencimiento")
        clientes = c.fetchall()
        print(f"\nClientes ({len(clientes)}):")
        for c in clientes:
            print(f"   - ID: {c['id']:03d}, Nombre: {c['nombre']}, Tel: {c['telefono']}, Vence: {c['fecha_vencimiento']}")
    
    print(f"\nIntegridad: {c.execute('PRAGMA integrity_check').fetchone()[0]}")
    conn.close()
    return True

if __name__ == "__main__":
    verificar_e_integridad()
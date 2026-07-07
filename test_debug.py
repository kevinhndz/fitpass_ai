"""Script de debug para encontrar el Internal Server Error"""
import sqlite3
import os
import traceback

DB_PATH = os.environ.get("DB_PATH", "fitpass.db")

print(f"[1] DB_PATH = {DB_PATH}")
print(f"[2] DB file exists: {os.path.exists(DB_PATH)}")

# Test conexion
try:
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    cur = conn.cursor()
    
    # List tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    print(f"[3] Tables: {tables}")
    
    # Check clientes table structure
    cur.execute("PRAGMA table_info(clientes)")
    cols = cur.fetchall()
    print(f"[4] clientes columns: {cols}")
    
    # Check usuarios table
    cur.execute("PRAGMA table_info(usuarios)")
    ucols = cur.fetchall()
    print(f"[5] usuarios columns: {ucols}")
    
    # Test a simple query
    cur.execute("SELECT * FROM clientes LIMIT 1")
    row = cur.fetchone()
    print(f"[6] First client row: {row}")
    
    # Test cursor.close()
    cur.close()
    print("[7] cursor.close() works OK")
    
    conn.close()
    print("[8] conn.close() works OK")
    
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

# Now test the Flask app startup
print("\n--- Testing Flask app import ---")
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[9] dotenv OK")
except Exception as e:
    print(f"[9] dotenv ERROR: {e}")

try:
    from conexion import conectar_base_datos
    db = conectar_base_datos()
    cur = db.cursor()
    cur.execute("SELECT * FROM clientes LIMIT 1")
    print(f"[10] conexion.py works: {cur.fetchone()}")
    cur.close()
    db.close()
except Exception as e:
    print(f"[10] conexion ERROR: {e}")
    traceback.print_exc()

# Test the secret key
print(f"[11] FLASK_SECRET_KEY set: {bool(os.environ.get('FLASK_SECRET_KEY'))}")

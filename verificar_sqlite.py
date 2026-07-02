"""
Verificador rápido de integridad de base de datos SQLite
"""

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.environ.get("DB_PATH", "fitpass.db")

def verificar_bd():
    print(f"Verificando base de datos: {DB_PATH}")
    print("=" * 50)
    
    # Verificar si el archivo existe
    if not os.path.exists(DB_PATH):
        print("❌ ERROR: Archivo no encontrado")
        print("Ejecute: 'python crear_base_datos.py' para crear la base de datos")
        return
    
    print(f"✅ Archivo encontrado ({os.path.getsize(DB_PATH)} bytes)")
    
    # Conectar y verificar
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Verificar integridad
    try:
        resultado = cursor.execute("PRAGMA integrity_check").fetchone()[0]
        print(f"✅ Integridad: {resultado.upper()}")
    except Exception as e:
        print(f"❌ Error de integridad: {e}")
    
    # 2. Verificar tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = cursor.fetchall()
    
    print(f"\n📋 Tablas encontradas: {len(tablas)}")
    for tabla in tablas:
        nombre = tabla[0]
        print(f"\n   🎯 {nombre}:")
        
        # Contar filas
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {nombre}")
            total = cursor.fetchone()[0]
            print(f"      Total filas: {total}")
        except Exception as e:
            print(f"      ❌ Error al contar: {e}")
        
        # Mostrar columnas
        try:
            cursor.execute(f"PRAGMA table_info({nombre})")
            columnas = cursor.fetchall()
            print(f"      Columnas: {len(columnas)}")
        except Exception as e:
            print(f"      ❌ Error al obtener columnas: {e}")
        
        # Mostrar muestra de datos si hay filas
        if total > 0:
            try:
                cursor.execute(f"SELECT * FROM {nombre} LIMIT 3")
                filas = cursor.fetchall()
                print(f"      Ejemplo ({len(filas)} filas):")
                for i, fila in enumerate(filas):
                    campos = [f"{k}: {v}" for k, v in fila.items()]
                    print(f"        {i+1}. {', '.join(campos)}")
            except Exception as e:
                print(f"      ❌ Error al obtener datos: {e}")
    
    cursor.close()
    conn.close()
    
    # 3. Verificar si hay tablas necesarias
    nombres_tablas = [t[0] for t in tablas]
    if "usuarios" in nombres_tablas and "clientes" in nombres_tablas:
        print("\n✅ Estructuras esenciales encontradas:")
        print("   - usuarios (autenticación)")
        print("   - clientes (datos principales)")
    else:
        print("\n⚠️  Advertencia: Estructuras esenciales faltantes")
        print(f"   Tablas encontradas: {', '.join(nombres_tablas)}")
    
    print("\n" + "=" * 50)
    print("✅ Verificación completada")

if __name__ == "__main__":
    verificar_bd()
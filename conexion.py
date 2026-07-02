import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()  

DB_PATH = os.environ.get("DB_PATH", "fitpass.db")

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def conectar_base_datos():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = dict_factory
    return conexion
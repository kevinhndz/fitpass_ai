"""Compatibilidad para scripts antiguos; la aplicación usa database.get_db."""

from database import SessionLocal, get_db


def conectar_base_datos():
    return SessionLocal()

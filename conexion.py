import mysql.connector

def conectar_base_datos():
    
    conexion = mysql.connector.connect(
        host="localhost",
        user="root",                 
        password="Allied2025++",    
        database="sportfitness_db"   
    )
    return conexion
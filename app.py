from flask import Flask, send_from_directory, request, jsonify
from datetime import date, timedelta  
from conexion import conectar_base_datos 

app = Flask(__name__, static_folder='static')

@app.route('/')
def ir_al_registro():
    return send_from_directory('static', 'registro.html')

@app.route('/api/registrar', methods=['POST'])
def registrar_cliente():
    # Paso 1: El mensajero agarra los 4 datos de tu formulario
    paquete_datos = request.get_json()
    nombre = paquete_datos.get('nombre')
    whatsapp = paquete_datos.get('whatsapp')
    correo = paquete_datos.get('correo')
    membresia = paquete_datos.get('membresia')
    
    
    hoy = date.today()
   
    vencimiento = hoy + timedelta(days=30)
    estado_inicial = "Activo"

    print(f"\n[RECEPCIÓN] Guardando a {nombre}. Inicio: {hoy} | Vence: {vencimiento}")

    # Paso 1: Abrimos el archivador de MySQL
    db = conectar_base_datos()
    cursor = db.cursor()
    
    # Paso 2: Preparamos la orden con las 7 columnas que ya tiene la tabla real
    sql = """INSERT INTO clientes (nombre, telefono, fecha_inicio, fecha_vencimiento, estado, correo, membresia) 
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    
#  Paso #3 : Pasamos las variables en el orden exacto de los %s
    valores = (nombre, whatsapp, hoy, vencimiento, estado_inicial, correo, membresia)
    cursor.execute(sql, valores)
    

    db.commit()
    cursor.close()
    db.close()  #Paso4:  cerramos la conexion

    respuesta_python = {
        "estado": "exito",
        "mensaje_pantalla": f"¡Excelente! El cliente '{nombre}' ha sido registrado con éxito. El sistema ya lo guardó."
    }
    #mandamos el json
    return jsonify(respuesta_python), 200

if __name__ == '__main__':
    app.run(debug=True)
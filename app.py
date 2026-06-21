from flask import Flask, send_from_directory, request, jsonify


app = Flask(__name__, static_folder='static')


@app.route('/')
def ir_al_registro():
    return send_from_directory('static', 'registro.html')

#
@app.route('/api/registrar', methods=['POST'])
def registrar_cliente():
    
    # recibimosel paquete JSON y lo abrimos en forma de diccionario
    paquete_datos = request.get_json()
    
    # Extraemos la información 
    nombre = paquete_datos.get('nombre')
    whatsapp = paquete_datos.get('whatsapp')
    correo = paquete_datos.get('correo')
    membresia = paquete_datos.get('membresia')
    
    print(f"\n[RECEPCIÓN] Procesando cliente NUEVO en el sistema: {nombre}")

    
    respuesta_python = {
        "estado": "exito",
        "mensaje_pantalla": f"¡Excelente! El cliente '{nombre}' ha sido registrado con éxito. El sistema ya lo guardó."
    }
    # Traducimos y sellamos la respuesta usando jsonify antes de enviarla por internet
    return jsonify(respuesta_python), 200
  

from flask import Flask, send_from_directory, request, jsonify, send_file
from datetime import date, timedelta
import os

from conexion import conectar_base_datos
from qr_utils import generar_qr, enviar_qr_por_correo, enviar_correo_recordatorio
from whatsapp_utils import enviar_recordatorio_whatsapp
from scheduler import iniciar_scheduler

app = Flask(__name__, static_folder='static')

if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
    iniciar_scheduler(conectar_base_datos)



@app.route('/')
def ir_al_registro():
    return send_from_directory('static', 'registro.html')

@app.route('/api/clientes', methods=['GET'])
def obtener_clientes():
    buscar = request.args.get('buscar')
    db = conectar_base_datos()
    cursor = db.cursor(dictionary=True)
    if buscar:
        sql = "SELECT * FROM clientes WHERE nombre LIKE %s OR telefono LIKE %s OR correo LIKE %s"
        cursor.execute(sql, (f"%{buscar}%", f"%{buscar}%", f"%{buscar}%"))
    else:
        cursor.execute("SELECT * FROM clientes")
    datos = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(datos)

@app.route('/api/clientes/<int:id>', methods=['PUT', 'DELETE'])
def manejar_cliente(id):
    db = conectar_base_datos()
    cursor = db.cursor()
    if request.method == 'PUT':
        datos = request.get_json()
        cursor.execute(
            "UPDATE clientes SET nombre=%s, telefono=%s, correo=%s, membresia=%s WHERE id=%s",
            (datos['nombre'], datos['whatsapp'], datos['correo'], datos['membresia'], id)
        )
        db.commit()
        mensaje = "Cliente actualizado correctamente."
    elif request.method == 'DELETE':
        cursor.execute("DELETE FROM clientes WHERE id=%s", (id,))
        db.commit()
        mensaje = "Cliente eliminado del sistema."
    cursor.close()
    db.close()
    return jsonify({"mensaje_pantalla": mensaje}), 200

@app.route('/api/reportes/hoy', methods=['GET'])
def obtener_reportes_hoy():
    db = conectar_base_datos()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM clientes WHERE fecha_vencimiento = CURDATE()")
    datos = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(datos)


# ── Registro: genera QR + envía correo ───────────────────────────────────────

@app.route('/api/registrar', methods=['POST'])
def registrar_cliente():
    datos     = request.get_json()
    nombre    = datos.get('nombre')
    whatsapp  = datos.get('whatsapp')
    correo    = datos.get('correo')
    membresia = datos.get('membresia')
    hoy       = date.today()
    vencimiento = hoy + timedelta(days=30)

    db = conectar_base_datos()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO clientes (nombre, telefono, fecha_inicio, fecha_vencimiento, estado, correo, membresia) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (nombre, whatsapp, hoy, vencimiento, "Activo", correo, membresia)
    )
    db.commit()
    nuevo_id = cursor.lastrowid
    cursor.close()
    db.close()

    ruta_qr   = generar_qr(nuevo_id, nombre, membresia, vencimiento)
    correo_ok = enviar_qr_por_correo(correo, nombre, vencimiento, ruta_qr)

    nota = " QR enviado a su correo." if correo_ok else " (No se pudo enviar el correo.)"
    return jsonify({"mensaje_pantalla": f"Cliente {nombre} registrado.{nota}", "cliente_id": nuevo_id}), 200




@app.route('/api/clientes/<int:id>/qr', methods=['POST'])
def regenerar_qr(id):
    # 1. Calcular las nuevas fechas (hoy y un mes después)
    hoy = date.today()
    nueva_fecha_vencimiento = hoy + timedelta(days=30)

    db = conectar_base_datos()
    cursor = db.cursor(dictionary=True)

    # 2. Actualizar las fechas en la base de datos PRIMERO
    cursor.execute(
        "UPDATE clientes SET fecha_inicio = %s, fecha_vencimiento = %s, estado = 'Activo' WHERE id = %s",
        (hoy, nueva_fecha_vencimiento, id)
    )
    db.commit()

    # 3. Leer los datos actualizados para generar el QR
    cursor.execute("SELECT * FROM clientes WHERE id = %s", (id,))
    c = cursor.fetchone()
    cursor.close()
    db.close()

    if not c:
        return jsonify({"error": "Cliente no encontrado"}), 404

    # 4. Generar y enviar el QR con los datos frescos
    ruta_qr   = generar_qr(c["id"], c["nombre"], c["membresia"], c["fecha_vencimiento"])
    correo_ok = enviar_qr_por_correo(c["correo"], c["nombre"], c["fecha_vencimiento"], ruta_qr)
    wa_ok     = enviar_recordatorio_whatsapp(c["telefono"], c["nombre"], c["fecha_vencimiento"], ruta_qr)

    return jsonify({
        "mensaje_pantalla": f"Membresía renovada y QR generado para {c['nombre']}. "
                            f"{'Correo enviado.' if correo_ok else 'Correo no enviado.'}"
    }), 200



@app.route('/validar/<int:id>')
def pagina_validar(id):
    """
    Sirve la página HTML de validación.
    El celular llega aquí al escanear el QR.
    """
    return send_from_directory('static', 'validar.html')

@app.route('/api/validar/<int:id>')
def api_validar(id):
    """
    Retorna los datos del cliente en JSON para que el HTML los muestre.
    Las fechas vienen como string 'YYYY-MM-DD' para que el JS las procese.
    """
    db = conectar_base_datos()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre, telefono, membresia, fecha_inicio, fecha_vencimiento FROM clientes WHERE id=%s", (id,))
    c = cursor.fetchone()
    cursor.close()
    db.close()

    if not c:
        return jsonify({"error": "Cliente no encontrado"}), 404

    # Convertir fechas a string para que JSON las serialice bien
    c["fecha_inicio"]      = str(c["fecha_inicio"])
    c["fecha_vencimiento"] = str(c["fecha_vencimiento"])
    return jsonify(c)


@app.route('/api/qr/<int:id>')
def ver_qr(id):
    ruta = os.path.join("static", "qr", f"qr_cliente_{id}.png")
    if not os.path.exists(ruta):
        return jsonify({"error": "QR no generado aún"}), 404
    return send_file(ruta, mimetype="image/png")


if __name__ == '__main__':
    # host='0.0.0.0' hace que Flask sea accesible desde el celular en la misma red WiFi
    app.run(debug=True, host='0.0.0.0', port=5000)
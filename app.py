"""
app.py — Servidor principal Sport Fitness (versión con QR + recordatorios).

Cambios respecto a la versión original:
  1. Se importan qr_utils y scheduler al inicio.
  2. /api/registrar ahora genera QR y lo envía por correo después de guardar.
  3. Nuevo endpoint POST /api/clientes/<id>/qr para regenerar QR desde la tabla.
  4. Nuevo endpoint GET /api/qr/<id> para descargar el PNG del QR.
  5. El scheduler se inicia al arrancar Flask (solo en el proceso principal).

Todo el código original de rutas fue preservado íntegramente.
"""

from flask import Flask, send_from_directory, request, jsonify, send_file
from datetime import date, timedelta
import os

from conexion import conectar_base_datos
from qr_utils import generar_qr, enviar_qr_por_correo
from whatsapp_utils import enviar_recordatorio_whatsapp
from scheduler import iniciar_scheduler

app = Flask(__name__, static_folder='static')

# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULER: se inicia solo si este es el proceso principal de Flask.
# Por qué la condición con WERKZEUG_RUN_MAIN:
#   Flask en modo debug arranca 2 procesos (el reloader + el servidor).
#   Sin esta condición, el scheduler se iniciaría dos veces y enviaría
#   recordatorios duplicados. Con la condición, solo corre en el proceso hijo.
# ─────────────────────────────────────────────────────────────────────────────
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
    iniciar_scheduler(conectar_base_datos)


# ─────────────────────────────────────────────────────────────────────────────
# RUTAS ORIGINALES (sin modificaciones)
# ─────────────────────────────────────────────────────────────────────────────

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
        val = (f"%{buscar}%", f"%{buscar}%", f"%{buscar}%")
        cursor.execute(sql, val)
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
        sql = "UPDATE clientes SET nombre=%s, telefono=%s, correo=%s, membresia=%s WHERE id=%s"
        val = (datos['nombre'], datos['whatsapp'], datos['correo'], datos['membresia'], id)
        cursor.execute(sql, val)
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


# ─────────────────────────────────────────────────────────────────────────────
# RUTA MODIFICADA: /api/registrar
# Cambio: después de INSERT exitoso, genera QR y lo envía por correo.
# La respuesta al frontend incluye si el correo se envió o no,
# pero el registro del cliente siempre se completa independientemente.
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/registrar', methods=['POST'])
def registrar_cliente():
    datos = request.get_json()
    nombre   = datos.get('nombre')
    whatsapp = datos.get('whatsapp')
    correo   = datos.get('correo')
    membresia = datos.get('membresia')

    hoy        = date.today()
    vencimiento = hoy + timedelta(days=30)
    estado     = "Activo"

    db = conectar_base_datos()
    cursor = db.cursor()
    sql = ("INSERT INTO clientes "
           "(nombre, telefono, fecha_inicio, fecha_vencimiento, estado, correo, membresia) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s)")
    cursor.execute(sql, (nombre, whatsapp, hoy, vencimiento, estado, correo, membresia))
    db.commit()

    # Obtenemos el ID autogenerado para nominar el archivo QR
    nuevo_id = cursor.lastrowid
    cursor.close()
    db.close()

    # ── Generar QR ──────────────────────────────────────────────────────────
    # Se genera después del commit para garantizar que el cliente existe en BD.
    # Si la generación del QR falla, el cliente igual queda registrado;
    # el recepcionista puede regenerarlo manualmente desde la tabla.
    ruta_qr = generar_qr(
        cliente_id=nuevo_id,
        nombre=nombre,
        membresia=membresia,
        fecha_vencimiento=vencimiento
    )

    # ── Enviar por correo ────────────────────────────────────────────────────
    correo_ok = enviar_qr_por_correo(
        destinatario=correo,
        nombre=nombre,
        fecha_vencimiento=vencimiento,
        ruta_qr=ruta_qr
    )

    nota_correo = " El QR fue enviado a su correo." if correo_ok else \
                  " (No se pudo enviar el correo; el QR está disponible en el sistema.)"

    return jsonify({
        "mensaje_pantalla": f"Cliente {nombre} registrado con éxito.{nota_correo}",
        "qr_generado": True,
        "correo_enviado": correo_ok,
        "cliente_id": nuevo_id
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT NUEVO: POST /api/clientes/<id>/qr
# El recepcionista lo llama desde la tabla al presionar "Generar nuevo QR".
# Regenera el QR con la fecha de vencimiento actual en BD y lo envía al cliente.
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/clientes/<int:id>/qr', methods=['POST'])
def regenerar_qr(id):
    """
    Regenera y reenvía el QR de un cliente existente.

    Por qué no extendemos la fecha aquí:
      Este endpoint solo regenera el QR con los datos actuales en BD.
      La extensión de la fecha de vencimiento es responsabilidad del
      recepcionista al documentar el pago (flujo de edición existente).
      Separar ambas acciones evita confusiones: primero el recepcionista
      registra el pago y actualiza la fecha, luego genera el nuevo QR.
    """
    db = conectar_base_datos()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM clientes WHERE id = %s", (id,))
    cliente = cursor.fetchone()
    cursor.close()
    db.close()

    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    ruta_qr = generar_qr(
        cliente_id=cliente["id"],
        nombre=cliente["nombre"],
        membresia=cliente["membresia"],
        fecha_vencimiento=cliente["fecha_vencimiento"]
    )

    correo_ok = enviar_qr_por_correo(
        destinatario=cliente["correo"],
        nombre=cliente["nombre"],
        fecha_vencimiento=cliente["fecha_vencimiento"],
        ruta_qr=ruta_qr
    )

    # También enviar por WhatsApp si está configurado
    wa_ok = enviar_recordatorio_whatsapp(
        telefono=cliente["telefono"],
        nombre=cliente["nombre"],
        fecha_vencimiento=cliente["fecha_vencimiento"],
        ruta_qr=ruta_qr
    )

    return jsonify({
        "mensaje_pantalla": f"QR regenerado para {cliente['nombre']}. "
                            f"{'Correo enviado.' if correo_ok else 'Correo no disponible.'} "
                            f"{'WhatsApp enviado.' if wa_ok else ''}",
        "correo_enviado": correo_ok,
        "whatsapp_enviado": wa_ok
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT NUEVO: GET /api/qr/<id>
# Permite descargar o visualizar el PNG del QR directamente desde el navegador.
# Útil si el recepcionista quiere imprimirlo o mostrarlo en pantalla.
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/qr/<int:id>', methods=['GET'])
def ver_qr(id):
    ruta = os.path.join("static", "qr", f"qr_cliente_{id}.png")
    if not os.path.exists(ruta):
        return jsonify({"error": "QR no generado aún"}), 404
    return send_file(ruta, mimetype="image/png")


if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, send_from_directory, request, jsonify, send_file, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import check_password_hash
from datetime import date, timedelta
import os
from dotenv import load_dotenv

from conexion import conectar_base_datos
from qr_utils import generar_qr, enviar_qr_por_correo, enviar_correo_recordatorio
from whatsapp_utils import enviar_recordatorio_whatsapp
from scheduler import iniciar_scheduler

load_dotenv()

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get("FLASK_SECRET_KEY")


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class Usuario(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    db = conectar_base_datos()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
    u = cursor.fetchone()
    cursor.close()
    db.close()
    if u:
        return Usuario(u['id'], u['username'])
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_in = request.form['username']
        pw_in = request.form['password']
        
        db = conectar_base_datos()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE username = %s", (user_in,))
        user_db = cursor.fetchone()
        cursor.close()
        db.close()
        
        if user_db and check_password_hash(user_db['password_hash'], pw_in):
            user_obj = Usuario(user_db['id'], user_db['username'])
            login_user(user_obj)
            return redirect(url_for('ir_al_registro'))
            
        flash("Usuario o contraseña incorrectos")
        
    return send_from_directory('static', 'login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
    iniciar_scheduler(conectar_base_datos)



@app.route('/')
@login_required
def ir_al_registro():
    return send_from_directory('static', 'registro.html')

@app.route('/api/clientes', methods=['GET'])
@login_required
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
@login_required
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
@login_required
def obtener_reportes_hoy():
    db = conectar_base_datos()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM clientes WHERE fecha_vencimiento = CURDATE()")
    datos = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(datos)



@app.route('/api/registrar', methods=['POST'])
@login_required
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
@login_required
def regenerar_qr(id):
    # 1. Calcular las nuevas fechas (hoy y un mes despues)
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


    cursor.execute("SELECT * FROM clientes WHERE id = %s", (id,))
    c = cursor.fetchone()
    cursor.close()
    db.close()

    if not c:
        return jsonify({"error": "Cliente no encontrado"}), 404

    ruta_qr   = generar_qr(c["id"], c["nombre"], c["membresia"], c["fecha_vencimiento"])
    correo_ok = enviar_qr_por_correo(c["correo"], c["nombre"], c["fecha_vencimiento"], ruta_qr)
    wa_ok     = enviar_recordatorio_whatsapp(c["telefono"], c["nombre"], c["fecha_vencimiento"], ruta_qr)

    return jsonify({
        "mensaje_pantalla": f"Membresía renovada y QR generado para {c['nombre']}. "
                            f"{'Correo enviado.' if correo_ok else 'Correo no enviado.'}"
    }), 200


@app.route('/validar/<int:id>')
def pagina_validar(id):
   
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

    #
    app.run(debug=False, host='0.0.0.0', port=5000)
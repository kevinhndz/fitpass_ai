from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='static')

@app.route('/')
def ir_al_registro():
    # Le decimos a Flask que envie directamente el archivo HTML tal cual está
    return send_from_directory('static', 'registro.html')

if __name__ == '__main__':
    app.run(debug=True)

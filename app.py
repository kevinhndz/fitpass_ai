from flask import Flask # trae todas las herramientas para hacer paginas web

app = Flask(__name__) # creamos la aplicacion

@app.route('/')
def home ():
  return "<h1>¡Bienvenidos a Sport Fitness con IA! El sistema está encendido con éxito.</h1>"


if __name__ == '__main__':
    app.run(debug=True)


from flask import Flask, render_template
app = Flask(__name__) # creamos la aplicacion

@app.route('/')
def home ():
  return render_template('registro.html')


if __name__ == '__main__':
    app.run(debug=True)


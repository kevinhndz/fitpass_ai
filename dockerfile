# 1. Ingrediente base: Una versión ligera de Python
FROM python:3.10-slim

# 2. Creando la "mesa de trabajo" dentro de la caja
WORKDIR /app

# 3. Copiar la lista de compras primero (esto hace que todo sea más rápido)
COPY requirements.txt .

# 4. Instalar todas las librerías que la app necesita
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar TODO el código  al contendor
COPY . .

# 6. Avisar por qué puerto se va a escuchar la app 
EXPOSE 5000

# 7. La orden final: El comando para encender el servidor cuando la caja se abra
CMD ["python", "app.py"]
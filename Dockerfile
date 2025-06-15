# Usa una imagen oficial de Python
FROM python:3.10-slim

# Crea el directorio de trabajo
WORKDIR /app

# Copia archivos
COPY . .
COPY .env .env

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto por defecto que Gunicorn usará
EXPOSE 8080

# Comando para correr Gunicorn apuntando a wsgi.py
CMD ["gunicorn", "-b", "0.0.0.0:8080", "wsgi:app"]

# Imagen base oficial de Python
FROM python:3.10-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar los archivos necesarios
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . .

# Exponer el puerto (Cloud Run lo ignora, pero es buena práctica)
EXPOSE 8080

# Variable de entorno obligatoria para Flask
ENV PYTHONUNBUFFERED True
ENV PORT 8080

# Usar Gunicorn para servir la app (importamos desde run.py)
CMD ["gunicorn", "--bind", ":8080", "app:create_app()"]

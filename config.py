# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

# Obtener variables individuales
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
dbname = os.getenv('DB_NAME')

# Construir la URL de conexión
DB_URL = f'postgresql://{user}:{password}@{host}:{port}/{dbname}'

# Configuracion de la aplicacion
APP_HOST = os.environ.get('APP_HOST', '127.0.0.1')
APP_PORT = int(os.environ.get('APP_PORT', 5000))

# Configuracion de rutas
RECIBOS_DIR = os.environ.get('RECIBOS_DIR', 'recibos')

# Asegurar que el directorio de recibos exista
os.makedirs(RECIBOS_DIR, exist_ok=True)

# Ruta al logo de la empresa
LOGO_PATH = os.path.join('recursos', 'Lender_logo.jpg')

# Nombre de tu bucket GCS (sin gs://)
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "recibos-nestor-gcp")
GCS_PUBLIC_URL_BASE = os.getenv("GCS_PUBLIC_URL_BASE", "https://storage.googleapis.com/recibos-nestor-gcp")
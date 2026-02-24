# -*- coding: utf-8 -*-
import os
import yaml
from pathlib import Path

# 1. Localizar y cargar el archivo env.yaml
BASE_DIR = Path(__file__).resolve().parent
yaml_path = BASE_DIR / 'env.yaml'

if yaml_path.exists():
    with open(yaml_path, 'r') as f:
        config_data = yaml.safe_load(f)
        if config_data:
            # Inyectamos los valores al entorno para que os.getenv los reconozca
            for key, value in config_data.items():
                os.environ[key] = str(value)
else:
    # Opcional: imprimir una advertencia si el archivo no existe
    print(f"Advertencia: No se encontró el archivo {yaml_path}")

class Config:
    # Base de Datos
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    
    # Si os.getenv devuelve None, usamos '5432' como puerto por defecto
    DB_PORT = os.getenv('DB_PORT') or '5432'
    
    DB_NAME = os.getenv('DB_NAME')
    
    # Construcción de la URL de SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

    # Configuración de la Aplicación
    APP_HOST = os.getenv('APP_HOST', '127.0.0.1')
    APP_PORT = int(os.getenv('APP_PORT', 5000))

    # Configuración de Archivos y Rutas
    RECIBOS_DIR = os.getenv('RECIBOS_DIR', 'recibos')
    LOGO_PATH = os.path.join('recursos', 'Lender_logo.jpg')

    # Cloud Storage
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "recibos-nestor-gcp")
    GCS_PUBLIC_URL_BASE = os.getenv("GCS_PUBLIC_URL_BASE", "https://storage.googleapis.com/recibos-nestor-gcp")

    @staticmethod
    def init_app(app):
        os.makedirs(Config.RECIBOS_DIR, exist_ok=True)

# Instancia para uso rápido en el resto de la app
settings = Config()
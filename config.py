# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Base de Datos
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    
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

# Instancia para uso rápido
settings = Config()
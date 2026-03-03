# -*- coding: utf-8 -*-
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field

class Config(BaseSettings):
    """
    Configuración centralizada con validación estricta.
    La aplicación no arrancará si faltan variables críticas de la base de datos.
    """
    
    # --- Base de Datos (OBLIGATORIAS) ---
    # Al no tener 'default=None', Pydantic exigirá que existan en el .env
    DB_USER: str = Field(alias="DB_USER")
    DB_PASSWORD: str = Field(alias="DB_PASSWORD")
    DB_HOST: str = Field(alias="DB_HOST")
    DB_NAME: str = Field(alias="DB_NAME")
    DB_PORT: str = Field(default="5432", alias="DB_PORT")

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """URL de conexión construida dinámicamente."""
        return f'postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    # --- Configuración de la Aplicación ---
    APP_HOST: str = Field(default="127.0.0.1", alias="APP_HOST")
    APP_PORT: int = Field(default=5000, alias="APP_PORT")
    RECIBOS_DIR: str = Field(default="recibos", alias="RECIBOS_DIR")
    
    @computed_field
    @property
    def LOGO_PATH(self) -> str:
        """Ruta absoluta al logo para que siempre se encuentre."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, 'recursos', 'Lender_logo.jpg')

    # --- Cloud Storage (GCS) ---
    GCS_BUCKET_NAME: str = Field(default="recibos-nestor-gcp", alias="GCS_BUCKET_NAME")
    
    @computed_field
    @property
    def GCS_PUBLIC_URL_BASE(self) -> str:
        """URL pública de acceso a archivos en GCS."""
        return os.getenv("GCS_PUBLIC_URL_BASE", f"https://storage.googleapis.com/{self.GCS_BUCKET_NAME}")

    # --- Integraciones (OBLIGATORIAS para WhatsApp) ---
    TWILIO_ACCOUNT_SID: str = Field(alias="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = Field(alias="TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER: str = Field(default="whatsapp:+14155238886", alias="TWILIO_WHATSAPP_NUMBER")
    WHATSAPP_ADMINS: str = Field(default="", alias="WHATSAPP_ADMINS")

    # --- Configuración del archivo .env ---
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # Ignora otras variables que puedan estar en el .env
    )

    def init_app(self, app):
        """Crea las carpetas necesarias al iniciar la app."""
        if not os.path.exists(self.RECIBOS_DIR):
            os.makedirs(self.RECIBOS_DIR, exist_ok=True)


# Instancia única para importar en toda la aplicación
# --- Al final de tu archivo config.py ---
try:
    # Creamos la instancia que será importada por los demás módulos
    settings = Config()
except Exception as e:
    import sys
    # Esto es vital en Google Cloud: si falta una variable, 
    # verás este mensaje exacto en los logs.
    print(f"\n[!] ERROR CRÍTICO DE CONFIGURACIÓN: {e}")
    sys.exit(1)


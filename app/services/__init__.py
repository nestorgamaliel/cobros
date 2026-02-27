# -*- coding: utf-8 -*-
import os
from flask import Flask
# Importamos settings y logger primero para asegurar que la config sea válida desde el inicio
from config import settings
from app.utils.logger import setup_logger

# Configurar logger global de la aplicación
logger = setup_logger(__name__)

# Variables globales para los servicios (Singleton pattern)
db_service = None
pdf_service = None
pago_service = None
persona_service = None
credito_service = None
vendedor_service = None

def create_app(test_config=None):
    """Factory para crear y configurar la aplicación Flask."""
    app = Flask(__name__, instance_relative_config=True)
    
    # 1. Cargar configuración desde el objeto Pydantic Settings
    if test_config is None:
        app.config.from_object(settings)
    else:
        app.config.from_mapping(test_config)
    
    # 2. Inicializar carpetas físicas y validaciones de entorno
    settings.init_app(app)
    
    # 3. Inicializar servicios de negocio y base de datos
    # Si el archivo .env está incompleto, Pydantic ya habrá detenido la app antes de aquí
    inicializar_servicios()
    
    # 4. Registrar rutas (Blueprint)
    # Importación local para evitar ciclos (Circular Imports)
    from app.api.routes import init_routes
    
    app.register_blueprint(
        init_routes(pago_service, persona_service, credito_service, vendedor_service),
        url_prefix='/api'
    )
        
    @app.route('/')
    def index():
        return {
            'status': 'ok', 
            'version': '3.0 (Pydantic & DTO Ready)',
            'message': 'Sistema de Gestión de Cobros - API Funcionando',
            'services_status': 'all_loaded' if all([db_service, pago_service]) else 'partial_load'
        }
    
    logger.info("Aplicación Flask inicializada exitosamente con configuración validada")
    return app

def inicializar_servicios():
    """Inicializa los servicios centralizados inyectando las dependencias necesarias."""
    global db_service, pdf_service, pago_service, persona_service, credito_service, vendedor_service
    
    try:
        # Importamos las clases desde el __init__.py de services que ya configuraste
        from app.services import (
            BaseDatos, GeneradorRecibos, ServicioPagos, 
            ServicioPersonas, ServicioCreditos, ServicioVendedores
        )

        # 1. Instanciar servicios base
        db_service = BaseDatos(settings.SQLALCHEMY_DATABASE_URI)
        pdf_service = GeneradorRecibos(settings.RECIBOS_DIR)
        
        # 2. Instanciar servicios de negocio (Inyección de dependencias)
        pago_service = ServicioPagos(db_service, pdf_service)
        persona_service = ServicioPersonas(db_service)
        credito_service = ServicioCreditos(db_service)    
        vendedor_service = ServicioVendedores(db_service)
        
        logger.info("Carga de servicios completada: Base de Datos, PDF y Lógica de Negocio")
        
    except Exception as e:
        logger.error(f"Error fatal al inicializar servicios: {str(e)}")
        # Importante re-lanzar para que el proceso de Gunicorn/Flask sepa que falló
        raise e

# --- Getters para acceso desde otros módulos ---
def get_db_service(): return db_service
def get_pdf_service(): return pdf_service
def get_pago_service(): return pago_service
def get_persona_service(): return persona_service
def get_vendedor_service(): return vendedor_service
def get_credito_service(): return credito_service
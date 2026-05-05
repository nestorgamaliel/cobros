# -*- coding: utf-8 -*-
import os
from flask import Flask
from config import settings
from app.utils.logger import setup_logger
from .estado_cuenta_service import EstadoCuentaService

# Configurar logger global
logger = setup_logger(__name__)

# Singletons para los servicios
db_service = None
pdf_service = None
pago_service = None
persona_service = None
credito_service = None
vendedor_service = None
estado_cuenta_service = None
finiquito_service = None

def inicializar_servicios():
    """Inicializa los servicios centralizados inyectando dependencias."""
    global db_service, pdf_service, pago_service, persona_service, credito_service, vendedor_service, estado_cuenta_service
    
    try:
        from app.services import (
            BaseDatos, GeneradorRecibos, ServicioPagos, 
            ServicioPersonas, ServicioCreditos, ServicioVendedores, ServicioVendedores
        )

        # 1. Base de Datos y PDF (Dependencias base)
        logger.info("Conectando a la base de datos...")
        db_service = BaseDatos(settings.SQLALCHEMY_DATABASE_URI)
        pdf_service = GeneradorRecibos(settings.RECIBOS_DIR)
        
        # 2. Servicios de Negocio
        persona_service = ServicioPersonas(db_service)
        credito_service = ServicioCreditos(db_service)    
        vendedor_service = ServicioVendedores(db_service)
        
        # --- INSTANCIAR EL NUEVO SERVICIO ---
        estado_cuenta_service = EstadoCuentaService(db_service)

        # 3. PagoService requiere db y pdf
        pago_service = ServicioPagos(db_service, pdf_service)


        logger.info("Servicios del sistema cargados correctamente")
        return True
        
    except Exception as e:
        logger.error(f"Error fatal en inicialización de servicios: {str(e)}")
        raise e

def create_app(test_config=None):
    """Factory principal de la aplicación."""
    app = Flask(__name__)
    
    # 1. Configuración
    if test_config:
        app.config.from_mapping(test_config)
    else:
        app.config.from_object(settings)
    
    # 2. Preparar entorno (carpetas, etc.)
    settings.init_app(app)
    
    # 3. Arrancar servicios ANTES que las rutas
    inicializar_servicios()
    
    # 4. Registrar Blueprints con inyección manual
    # Importamos aquí para evitar importaciones circulares
    from app.api.routes import init_routes
    
    # Validamos que los servicios existan antes de pasarlos
    if all([pago_service, persona_service, credito_service, vendedor_service, finiquito_service, estado_cuenta_service]):
        api_bp = init_routes(
            pago_service, 
            persona_service, 
            credito_service, 
            vendedor_service,
            finiquito_service,
            estado_cuenta_service             
        )
        app.register_blueprint(api_bp, url_prefix='/api')
        logger.info("Blueprints registrados exitosamente")
    else:
        logger.error("No se pudieron registrar las rutas: Algunos servicios son None")

    @app.route('/')
    def index():
        return {
            'status': 'ok',
            'version': '3.1',
            'database': 'connected' if db_service else 'error',
            'services': 'ready' if all([pago_service, persona_service]) else 'initializing'
        }
    
    return app

# Getters para otros módulos
def get_db_service(): return db_service
def get_pago_service(): return pago_service
def get_persona_service(): return persona_service
def get_credito_service(): return credito_service
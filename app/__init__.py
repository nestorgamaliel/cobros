# -*- coding: utf-8 -*-
import os
from flask import Flask
# Importamos settings y logger primero para asegurar que la config sea válida
from config import settings
from app.utils.logger import setup_logger

# Configurar logger
logger = setup_logger(__name__)

# Variables globales para los servicios (Singleton pattern manual)
db_service = None
pdf_service = None
pago_service = None
persona_service = None
credito_service = None
vendedor_service = None
finiquito_service = None 
estado_cuenta_service = None

def create_app(test_config=None):
    """Factory para crear y configurar la aplicación Flask."""
    app = Flask(__name__, instance_relative_config=True)
    
    # 1. Cargar configuración desde el objeto Pydantic
    if test_config is None:
        app.config.from_object(settings)
    else:
        app.config.from_mapping(test_config)
    
    # 2. Inicializar carpetas físicas (como RECIBOS_DIR)
    settings.init_app(app)
    
    # 3. Inicializar servicios de negocio y base de datos
    inicializar_servicios()
    
    # 4. Registrar rutas (Blueprint)
    from app.api.routes import init_routes
    
    # Agregamos finiquito_service a la inyección de rutas
    app.register_blueprint(
        init_routes(
            pago_service, 
            persona_service, 
            credito_service, 
            vendedor_service, 
            finiquito_service,
            estado_cuenta_service
        ),
        url_prefix='/api'
    )
        
    @app.route('/')
    def index():
        return {
            'status': 'ok', 
            'version': '3.1 (Finiquitos manuales)',
            'message': 'Sistema de Gestión de Cobros funcionando correctamente',
            'environment': 'Production' if not app.debug else 'Development'
        }
    
    logger.info("Aplicación Flask inicializada exitosamente")
    return app

def inicializar_servicios():
    """Inicializa los servicios centralizados inyectando las dependencias necesarias."""
    global db_service, pdf_service, pago_service, persona_service, credito_service, vendedor_service, finiquito_service
    
    try:
        # Importaciones tardías para evitar dependencias circulares
        from app.services.db_service import BaseDatos
        from app.services.pdf_service import GeneradorRecibos
        from app.services.pago_service import ServicioPagos
        from app.services.persona_service import ServicioPersonas
        from app.services.credito_service import ServicioCreditos
        from app.services.vendedor_service import ServicioVendedores
        from app.services.finiquito_service import FiniquitoService # Nueva importación
        from app.services.estado_cuenta_service import EstadoCuentaService

        # 1. Servicios base
        db_service = BaseDatos(settings.SQLALCHEMY_DATABASE_URI)
        pdf_service = GeneradorRecibos(settings.RECIBOS_DIR)
        
        # 2. Servicios de negocio con inyección de dependencias
        pago_service = ServicioPagos(db_service, pdf_service)
        persona_service = ServicioPersonas(db_service)
        credito_service = ServicioCreditos(db_service)    
        vendedor_service = ServicioVendedores(db_service)
        finiquito_service = FiniquitoService(db_service)
        estado_cuenta_service = EstadoCuentaService(db_service)
        
        logger.info("Todos los servicios del sistema (incluyendo Finiquitos) han sido cargados")
        
    except Exception as e:
        logger.error(f"Error crítico al inicializar servicios: {str(e)}")
        raise e

# --- Getters para acceso externo (opcional) ---
def get_db_service(): return db_service
def get_pdf_service(): return pdf_service
def get_pago_service(): return pago_service
def get_persona_service(): return persona_service
def get_vendedor_service(): return vendedor_service
def get_credito_service(): return credito_service
def get_finiquito_service(): return finiquito_service
def get_estado_cuenta_service(): return estado_cuenta_service
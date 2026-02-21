import os
from flask import Flask
from app.services import BaseDatos, GeneradorRecibos, ServicioPagos
from app.services import ServicioPersonas, ServicioCreditos, ServicioVendedores
from app.api import init_routes
from app.utils.logger import setup_logger
# Importamos el objeto settings
from config import settings

# Configurar logger
logger = setup_logger(__name__)

# Variables globales para los servicios
db_service = None
pdf_service = None
pago_service = None
persona_service = None
credito_service = None
vendedor_service = None

def create_app(test_config=None):
    """Crea y configura la aplicacion Flask."""
    app = Flask(__name__, instance_relative_config=True)
    
    # 1. Cargar configuración desde el objeto profesional
    if test_config is None:
        # Cargamos directamente desde nuestra clase Config
        app.config.from_object(settings)
    else:
        app.config.from_mapping(test_config)
    
    # 2. Ejecutar inicialización de carpetas (como RECIBOS_DIR)
    settings.init_app(app)
    
    # 3. Inicializar servicios usando settings
    # Ya no pasamos parámetros manuales, la función los toma de settings
    inicializar_servicios()
    
    # Registrar blueprint de la API
    app.register_blueprint(
        init_routes(pago_service, persona_service, credito_service, vendedor_service),
        url_prefix='/api'
    )
        
    @app.route('/')
    def index():
        return {
            'status': 'ok', 
            'message': 'Sistema de Gestion de Cobros Crediticios funcionando correctamente'
        }
    
    logger.info("Aplicacion Flask inicializada correctamente")
    return app

def inicializar_servicios():
    """Inicializa los servicios centralizados usando el objeto settings."""
    global db_service, pdf_service, pago_service, persona_service, credito_service, vendedor_service
    
    # Usamos settings directamente para evitar pasar strings por todos lados
    db_service = BaseDatos(settings.SQLALCHEMY_DATABASE_URI)
    pdf_service = GeneradorRecibos(settings.RECIBOS_DIR)
    
    # Inyección de dependencias
    pago_service = ServicioPagos(db_service, pdf_service)
    persona_service = ServicioPersonas(db_service)
    credito_service = ServicioCreditos(db_service)    
    vendedor_service = ServicioVendedores(db_service)
    
    logger.info("Servicios inicializados correctamente")

# Getters (se mantienen igual para no romper compatibilidad en otros archivos)
def get_db_service(): return db_service
def get_pdf_service(): return pdf_service
def get_pago_service(): return pago_service
def get_persona_service(): return persona_service
def get_vendedor_service(): return vendedor_service
def get_credito_service(): return credito_service
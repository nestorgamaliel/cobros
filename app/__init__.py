import os
from flask import Flask
from app.services import BaseDatos, GeneradorRecibos, ServicioPagos
from app.services import ServicioPersonas, ServicioCreditos
from app.api import init_routes
from app.utils.logger import setup_logger
import config

# Configurar logger
logger = setup_logger(__name__)

# Variables globales para los servicios
db_service = None
pdf_service = None
pago_service = None
persona_service = None
credito_service = None


def create_app(test_config=None):
    """
    Crea y configura la aplicacion Flask.
    
    Args:
        test_config (dict, opcional): Configuracion para pruebas.
        
    Returns:
        Flask: Aplicacion Flask configurada.
    """
    # Crear y configurar la aplicacion
    app = Flask(__name__, instance_relative_config=True)
    
    # Cargar la configuracion predeterminada
    if test_config is None:
        # Usar la configuracion de produccion
        app.config.from_pyfile('../config.py', silent=True)
    else:
        # Cargar la configuracion de prueba
        app.config.from_mapping(test_config)
    
    # Inicializar servicios
    inicializar_servicios(app.config.get('DB_URL', config.DB_URL),
                          app.config.get('RECIBOS_DIR', config.RECIBOS_DIR))
    
    # Registrar blueprint de la API
    app.register_blueprint(init_routes(pago_service, persona_service, credito_service),
                           url_prefix='/api')
        
    # Ruta de inicio para verificar que la aplicacion está funcionando
    @app.route('/')
    def index():
        return {'status': 'ok', 'message': 'Sistema de Gestion de Cobros \
                Crediticios funcionando correctamente'}
    
    logger.info("Aplicacion Flask inicializada correctamente")
    return app


def inicializar_servicios(db_url, recibos_dir):
    """
    Inicializa los servicios necesarios para la aplicacion.
    
    Args:
        db_url (str): URL de conexion a la base de datos.
        recibos_dir (str): Directorio donde se guardarán los recibos.
    """
    global db_service
    global pdf_service
    global pago_service
    global persona_service
    global credito_service
    
    # Inicializar el servicio de base de datos
    db_service = BaseDatos(db_url)
    
    # Inicializar el servicio de generacion de PDF
    pdf_service = GeneradorRecibos(recibos_dir)
    
    # Inicializar servicio de gestion de datos
    pago_service = ServicioPagos(db_service, pdf_service)
    persona_service = ServicioPersonas(db_service)
    credito_service = ServicioCreditos(db_service)    
    
    logger.info("Servicios inicializados correctamente")
    
    
def get_db_service():
    """
    Obtiene el servicio de base de datos.
    
    Returns:
        BaseDatos: Instancia del servicio de base de datos.
    """
    return db_service


def get_pdf_service():
    """
    Obtiene el servicio de generacion de PDF.
    
    Returns:
        GeneradorRecibos: Instancia del servicio de generacion de recibos.
    """
    return pdf_service


def get_pago_service():
    """
    Obtiene el servicio de pagos.
    
    Returns:
        ServicioPagos: Instancia del servicio de gestion de pagos.
    """
    return pago_service


def get_persona_service():
    """
    Obtiene el servicio de personas.
    
    Returns:
        ServicioPersonas: Instancia del servicio de gestion de personas.
    """
    return persona_service


def get_credito_service():
    """
    Obtiene el servicio de creditos.
    
    Returns:
        ServicioCreditos: Instancia del servicio de gestion de creditos.
    """
    return credito_service

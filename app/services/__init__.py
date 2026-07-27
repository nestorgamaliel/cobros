# -*- coding: utf-8 -*-
import os
from flask import Flask
from config import settings
from app.utils.logger import setup_logger
from .estado_cuenta_service import EstadoCuentaService
from .saldo_diario_service import ServicioSaldoDiario  # <--- 1. Importar Clase

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
saldo_diario_service = None  # <--- 2. Variable Global

def inicializar_servicios():
    global db_service, pdf_service, pago_service, persona_service, credito_service, vendedor_service, estado_cuenta_service, finiquito_service, saldo_diario_service
    
    try:
        from app.services import (
            BaseDatos, GeneradorRecibos, ServicioPagos, 
            ServicioPersonas, ServicioCreditos, ServicioVendedores,
            ServicioFiniquitos 
        )

        logger.info("Conectando a la base de datos...")
        db_service = BaseDatos(settings.SQLALCHEMY_DATABASE_URI)
        pdf_service = GeneradorRecibos(settings.RECIBOS_DIR)
        
        persona_service = ServicioPersonas(db_service)
        credito_service = ServicioCreditos(db_service)    
        vendedor_service = ServicioVendedores(db_service)
        
        estado_cuenta_service = EstadoCuentaService(db_service)
        finiquito_service = ServicioFiniquitos(db_service)
        saldo_diario_service = ServicioSaldoDiario(db_service)  # <--- 3. Instanciar Servicio

        pago_service = ServicioPagos(db_service, pdf_service)

        logger.info("Todos los servicios han sido cargados correctamente")
        return True
        
    except Exception as e:
        logger.error(f"Error fatal en inicialización de servicios: {str(e)}")
        raise e

def create_app(test_config=None):
    app = Flask(__name__)
    
    if test_config:
        app.config.from_mapping(test_config)
    else:
        app.config.from_object(settings)
    
    settings.init_app(app)
    inicializar_servicios()
    
    from app.api.routes import init_routes
    
    global pago_service, persona_service, credito_service, vendedor_service, finiquito_service, estado_cuenta_service, saldo_diario_service

    servicios_check = [
        pago_service, 
        persona_service, 
        credito_service, 
        vendedor_service, 
        finiquito_service, 
        estado_cuenta_service,
        saldo_diario_service  # <--- 4. Agregar a la verificación
    ]

    logger.info(f"Verificando servicios para rutas: {[s is not None for s in servicios_check]}")

    if all(servicios_check):
        api_bp = init_routes(
            pago_service, 
            persona_service, 
            credito_service, 
            vendedor_service,
            finiquito_service,     
            estado_cuenta_service,
            saldo_diario_service  # <--- 5. Pasar a init_routes
        )
        app.register_blueprint(api_bp, url_prefix='/api')
        logger.info("Blueprints registrados exitosamente")
    else:
        missing = []
        if not pago_service: missing.append("pago")
        if not persona_service: missing.append("persona")
        if not credito_service: missing.append("credito")
        if not vendedor_service: missing.append("vendedor")
        if not finiquito_service: missing.append("finiquito")
        if not estado_cuenta_service: missing.append("estado_cuenta")
        if not saldo_diario_service: missing.append("saldo_diario")
        logger.error(f"No se pudieron registrar las rutas. Servicios faltantes: {missing}")
        

    @app.route('/')
    def index():
        return {
            'status': 'ok',
            'version': '3.1',
            'database': 'connected' if db_service else 'error',
            'services': 'ready' if all([pago_service, persona_service]) else 'initializing'
        }
    
    return app

def get_db_service(): return db_service
def get_pago_service(): return pago_service
def get_persona_service(): return persona_service
def get_credito_service(): return credito_service
def get_saldo_diario_service(): return saldo_diario_service
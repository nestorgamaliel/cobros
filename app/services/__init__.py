# -*- coding: utf-8 -*-
import os
from flask import Flask
from config import settings
from app.utils.logger import setup_logger

# Importación explícita de los servicios
from app.services.estado_cuenta_service import EstadoCuentaService
from app.services.estado_cuenta_diario_service import EstadoCuentaDiarioService
from app.services.saldo_diario_service import ServicioSaldoDiario

logger = setup_logger(__name__)

# Singletons globales para los servicios
db_service = None
pdf_service = None
pago_service = None
persona_service = None
credito_service = None
vendedor_service = None
estado_cuenta_service = None
estado_cuenta_diario_service = None
finiquito_service = None
saldo_diario_service = None

def inicializar_servicios():
    global db_service, pdf_service, pago_service, persona_service, credito_service
    global vendedor_service, estado_cuenta_service, estado_cuenta_diario_service
    global finiquito_service, saldo_diario_service
    
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
        estado_cuenta_diario_service = EstadoCuentaDiarioService(db_service)
        finiquito_service = ServicioFiniquitos(db_service)
        saldo_diario_service = ServicioSaldoDiario(db_service)

        pago_service = ServicioPagos(db_service, pdf_service)

        logger.info("Todos los servicios han sido cargados correctamente")
        return True
        
    except Exception as e:
        logger.error(f"Error fatal en inicialización de servicios: {str(e)}", exc_info=True)
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
    
    global pago_service, persona_service, credito_service, vendedor_service
    global finiquito_service, estado_cuenta_service, estado_cuenta_diario_service, saldo_diario_service

    servicios_check = [
        pago_service, 
        persona_service, 
        credito_service, 
        vendedor_service, 
        finiquito_service, 
        estado_cuenta_service,
        estado_cuenta_diario_service,
        saldo_diario_service
    ]

    logger.info(f"Verificando servicios para rutas: {[s is not None for s in servicios_check]}")

    if all(servicios_check):
        # Invocación con argumentos nombrados (kwargs) para evitar desfasamientos posicionales
        api_bp = init_routes(
            servicio_pagos=pago_service, 
            servicio_personas=persona_service, 
            servicio_creditos=credito_service, 
            servicio_vendedores=vendedor_service,
            servicio_finiquitos=finiquito_service,     
            servicio_estado_cuenta=estado_cuenta_service,
            servicio_saldo_diario=saldo_diario_service,
            servicio_estado_cuenta_diario=estado_cuenta_diario_service
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
        if not estado_cuenta_diario_service: missing.append("estado_cuenta_diario")
        if not saldo_diario_service: missing.append("saldo_diario")
        logger.error(f"No se pudieron registrar las rutas. Servicios faltantes: {missing}")
        

    @app.route('/')
    def index():
        return {
            'status': 'ok',
            'version': '3.1',
            'database': 'connected' if db_service else 'error',
            'services': 'ready' if all([pago_service, persona_service, estado_cuenta_diario_service]) else 'initializing'
        }
    
    return app

def get_db_service(): return db_service
def get_pago_service(): return pago_service
def get_persona_service(): return persona_service
def get_credito_service(): return credito_service
def get_saldo_diario_service(): return saldo_diario_service
def
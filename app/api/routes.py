# -*- coding: utf-8 -*-
import os
import traceback
from flask import Blueprint, request, jsonify, send_file
from app.utils.logger import setup_logger
from config import settings
from app.services.notificacion_service import NotificacionService

# Importación de DTOs para validación
from app.schemas.persona import PersonaCreate, PersonaUpdate
from app.schemas.credito import (
    CreditoCreate, 
    ConsultaSaldoDiarioRequest, 
    ReestructuracionCreate,
    EstadoCuentaDiarioPDFRequest
)
from app.schemas.pago import PagoCreate

# Importación de servicios de comunicación
from app.services.whatsapp_service import WhatsAppService, TwilioProvider

logger = setup_logger(__name__)


def init_routes(
    servicio_pagos, 
    servicio_personas, 
    servicio_creditos, 
    servicio_vendedores, 
    servicio_finiquitos, 
    servicio_estado_cuenta,
    servicio_saldo_diario=None,
    servicio_reestructuracion=None,
    servicio_estado_cuenta_diario=None
):
    """
    Inyecta los servicios y registra las rutas dentro de un Blueprint.
    Mantiene compatibilidad total con la lógica previa e integra el estado de cuenta por saldo diario con depuración activa.
    """
    api_blueprint = Blueprint('api', __name__)

    # --- CONFIGURACIÓN DE WHATSAPP ---
    if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
        try:
            provider = TwilioProvider()
            provider.sid = settings.TWILIO_ACCOUNT_SID
            provider.token = settings.TWILIO_AUTH_TOKEN
            provider.from_number = settings.TWILIO_WHATSAPP_NUMBER
            
            whatsapp = WhatsAppService(provider)
            
            if settings.WHATSAPP_ADMINS:
                whatsapp.admin_numbers = [n.strip() for n in settings.WHATSAPP_ADMINS.split(',')]
            
            # Inyectamos el servicio de WhatsApp en el servicio de créditos
            if servicio_creditos:
                servicio_creditos.whatsapp = whatsapp
                logger.info("WhatsAppService vinculado exitosamente a CréditoService")
        except Exception as e:
            logger.error(f"Fallo en vinculación de WhatsApp: {e}")
    else:
        logger.warning("WhatsApp no configurado: Faltan credenciales")

    # --- RUTAS DE PERSONAS ---
    @api_blueprint.route('/persona', methods=['POST'])
    def crear_persona():
        try:
            datos_validados = PersonaCreate(**request.get_json())
            resultado, error = servicio_personas.crear_persona(datos_validados)
            
            if error:
                return jsonify({'error': error}), 400
            
            return jsonify({
                'mensaje': 'Persona registrada correctamente',
                'persona_id': resultado.persona_id
            }), 201
        except Exception as e:
            logger.error(f"Error en POST /persona: {str(e)}")
            return jsonify({'error': str(e)}), 400

    @api_blueprint.route('/personas/buscar', methods=['GET'])
    def buscar_persona():
        try:
            filtros = {
                'dui': request.args.get('dui', '').strip(),
                'nombres': request.args.get('nombres', '').strip(),
                'apellidos': request.args.get('apellidos', '').strip()
            }
            limite = int(request.args.get('limite', 10))
            pagina = int(request.args.get('pagina', 1))

            resultado = servicio_personas.buscar_personas(filtros, limite, pagina)
            
            if not resultado.get('success'):
                return jsonify(resultado), 400
            
            personas_serializables = []
            for p in resultado['personas']:
                personas_serializables.append({
                    'persona_id': p.persona_id,
                    'nombres': p.nombres,
                    'apellidos': p.apellidos,
                    'dui': p.dui,
                    'telefono': p.telefono,
                    'direccion': p.direccion,
                    'fecha_nacimiento': p.fecha_nacimiento.strftime('%Y-%m-%d') if p.fecha_nacimiento else None
                })
            
            resultado['personas'] = personas_serializables
            return jsonify(resultado), 200
        except Exception as e:
            logger.error(f"Error en GET /personas/buscar: {str(e)}")
            return jsonify({'error': 'Error interno al procesar la búsqueda'}), 500

    # --- RUTAS DE CRÉDITOS Y SALDO DIARIO ---
    @api_blueprint.route('/credito', methods=['POST'])
    def crear_credito():
        try:
            datos_validados = CreditoCreate(**request.get_json())
            resultado, error = servicio_creditos.crear_credito(datos_validados)
            
            if error:
                return jsonify({'error': error}), 400
                
            return jsonify({
                'mensaje': 'Crédito creado exitosamente',
                'credito_id': resultado.credito_id
            }), 201
        except Exception as e:
            logger.error(f"Error en POST /credito:
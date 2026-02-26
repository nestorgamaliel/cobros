import os
import datetime
from flask import Blueprint, request, jsonify, send_file
from app.services import ServicioPagos, ServicioPersonas, ServicioCreditos, ServicioVendedores
from app.schemas.persona import PersonaCreate, PersonaUpdate
from app.schemas.credito import CreditoCreate
from app.schemas.pago import PagoCreate
from app.utils.logger import setup_logger
from app.services.whatsapp_service import WhatsAppService, TwilioProvider

logger = setup_logger(__name__)
api_blueprint = Blueprint('api', __name__)

# Globales para inyección de dependencias
pago_service = None
persona_service = None
credito_service = None
vendedor_service = None

def init_routes(servicio_pagos, servicio_personas, servicio_creditos, servicio_vendedores):
    global pago_service, persona_service, credito_service, vendedor_service
    pago_service = servicio_pagos
    persona_service = servicio_personas
    credito_service = servicio_creditos
    vendedor_service = servicio_vendedores
    
    # Inyectar WhatsApp al servicio de créditos
    whatsapp = WhatsAppService(TwilioProvider())
    credito_service.whatsapp = whatsapp
    
    logger.info("Rutas de la API inicializadas con DTOs")
    return api_blueprint

# --- RUTAS DE PERSONAS ---

@api_blueprint.route('/persona', methods=['POST'])
def crear_persona():
    try:
        # VALIDACIÓN CON DTO
        datos_validados = PersonaCreate(**request.get_json())
        resultado, error = persona_service.crear_persona(datos_validados)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'mensaje': 'Persona registrada correctamente',
            'persona_id': resultado.persona_id
        }), 201
    except Exception as e:
        logger.error(f"Error en /persona: {str(e)}")
        return jsonify({'error': str(e)}), 400

@api_blueprint.route('/personas/buscar', methods=['GET'])
def buscar_persona():
    filtros = {
        'dui': request.args.get('dui', '').strip(),
        'nombres': request.args.get('nombres', '').strip(),
        'apellidos': request.args.get('apellidos', '').strip()
    }
    limite = int(request.args.get('limite', 10))
    pagina = int(request.args.get('pagina', 1))

    resultado = persona_service.buscar_personas(filtros, limite, pagina)
    return jsonify(resultado), 200

# --- RUTAS DE CRÉDITOS ---

@api_blueprint.route('/credito', methods=['POST'])
def crear_credito():
    try:
        # VALIDACIÓN CON DTO (Atrapa fechas mal formateadas o montos negativos)
        datos_validados = CreditoCreate(**request.get_json())
        resultado, error = credito_service.crear_credito(datos_validados)
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify({
            'mensaje': 'Crédito creado',
            'credito_id': resultado.credito_id
        }), 201
    except Exception as e:
        return jsonify({'error': f"Datos inválidos: {str(e)}"}), 400

# --- RUTAS DE PAGOS ---

@api_blueprint.route('/pago', methods=['POST'])
def registrar_pago():
    try:
        # VALIDACIÓN CON DTO
        datos_validados = PagoCreate(**request.get_json())
        ruta, nombre, url = pago_service.registrar_pago(datos_validados)
        
        if not ruta:
            return jsonify({'error': nombre}), 400
            
        return jsonify({
            'mensaje': 'Pago exitoso',
            'url_recibo': url,
            'nombre_archivo': nombre
        }), 201
    except Exception as e:
        return jsonify({'error': f"Error en pago: {str(e)}"}), 400

@api_blueprint.route('/recibo/<nombre_recibo>', methods=['GET'])
def obtener_recibo(nombre_recibo):
    from config import settings
    ruta_recibo = os.path.join(settings.RECIBOS_DIR, nombre_recibo)
    if os.path.exists(ruta_recibo):
        return send_file(ruta_recibo, as_attachment=True)
    return jsonify({'error': 'No encontrado'}), 404

# --- REPORTES Y CRON ---

@api_blueprint.route('/cron/reporte-diario', methods=['POST'])
def ejecutar_reporte_diario():
    resultado = credito_service.enviar_reporte_diario_vencimientos()
    return jsonify({'success': True, 'enviado': bool(resultado)}), 200
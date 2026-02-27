# -*- coding: utf-8 -*-
import os
from flask import Blueprint, request, jsonify, send_file
from app.utils.logger import setup_logger

# Importamos el objeto settings para acceder a las rutas y credenciales
from config import settings

# Importación de DTOs para validación
from app.schemas.persona import PersonaCreate, PersonaUpdate
from app.schemas.credito import CreditoCreate
from app.schemas.pago import PagoCreate

# Importación de proveedores de servicios
from app.services.whatsapp_service import WhatsAppService, TwilioProvider

logger = setup_logger(__name__)
api_blueprint = Blueprint('api', __name__)

# Globales para inyección de dependencias
pago_service = None
persona_service = None
credito_service = None
vendedor_service = None

def init_routes(servicio_pagos, servicio_personas, servicio_creditos, servicio_vendedores):
    """
    Inicializa las rutas inyectando los servicios de negocio y configurando
    las integraciones externas como WhatsApp.
    """
    global pago_service, persona_service, credito_service, vendedor_service
    pago_service = servicio_pagos
    persona_service = servicio_personas
    credito_service = servicio_creditos
    vendedor_service = servicio_vendedores
    
    # --- Configuración Dinámica de WhatsApp ---
    if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
        try:
            provider = TwilioProvider(
                account_sid=settings.TWILIO_ACCOUNT_SID,
                auth_token=settings.TWILIO_AUTH_TOKEN,
                from_number=settings.TWILIO_WHATSAPP_NUMBER
            )
            whatsapp = WhatsAppService(provider)
            
            # Si existen administradores en el .env, se inyectan como lista
            if settings.WHATSAPP_ADMINS:
                whatsapp.admin_numbers = [n.strip() for n in settings.WHATSAPP_ADMINS.split(',')]
                
            credito_service.whatsapp = whatsapp
            logger.info("Servicio de WhatsApp vinculado exitosamente a Créditos")
        except Exception as e:
            logger.error(f"Error al configurar el proveedor de WhatsApp: {e}")
    else:
        logger.warning("WhatsApp no inicializado: Faltan credenciales en el archivo .env")
    
    logger.info("Rutas de la API inicializadas correctamente")
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

        resultado = persona_service.buscar_personas(filtros, limite, pagina)
        
        if not resultado.get('success'):
            return jsonify(resultado), 400
        
        # Serialización manual de objetos SQLAlchemy a JSON
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

# --- RUTAS DE CRÉDITOS ---

@api_blueprint.route('/credito', methods=['POST'])
def crear_credito():
    try:
        # VALIDACIÓN CON DTO
        datos_validados = CreditoCreate(**request.get_json())
        resultado, error = credito_service.crear_credito(datos_validados)
        
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify({
            'mensaje': 'Crédito creado exitosamente',
            'credito_id': resultado.credito_id
        }), 201
    except Exception as e:
        logger.error(f"Error en POST /credito: {str(e)}")
        return jsonify({'error': f"Datos inválidos: {str(e)}"}), 400

# --- RUTAS DE PAGOS ---

@api_blueprint.route('/pago', methods=['POST'])
def registrar_pago():
    try:
        # VALIDACIÓN CON DTO
        datos_validados = PagoCreate(**request.get_json())
        ruta, nombre, url = pago_service.registrar_pago(datos_validados)
        
        if not ruta:
            # En este caso 'nombre' contiene el mensaje de error del servicio
            return jsonify({'error': nombre}), 400
            
        return jsonify({
            'mensaje': 'Pago procesado exitosamente',
            'url_recibo': url,
            'nombre_archivo': nombre
        }), 201
    except Exception as e:
        logger.error(f"Error en POST /pago: {str(e)}")
        return jsonify({'error': f"Error en procesamiento de pago: {str(e)}"}), 400

@api_blueprint.route('/recibo/<nombre_recibo>', methods=['GET'])
def obtener_recibo(nombre_recibo):
    # Usamos settings.RECIBOS_DIR validado por Pydantic
    ruta_recibo = os.path.join(settings.RECIBOS_DIR, nombre_recibo)
    
    if os.path.exists(ruta_recibo):
        return send_file(ruta_recibo, as_attachment=True)
    
    logger.warning(f"Intento fallido de descargar recibo: {nombre_recibo}")
    return jsonify({'error': 'Archivo de recibo no encontrado'}), 404

# --- REPORTES Y AUTOMATIZACIÓN ---

@api_blueprint.route('/cron/reporte-diario', methods=['POST'])
def ejecutar_reporte_diario():
    try:
        resultado = credito_service.enviar_reporte_diario_vencimientos()
        return jsonify({
            'success': True, 
            'enviado': bool(resultado),
            'timestamp': os.times()
        }), 200
    except Exception as e:
        logger.error(f"Error en cron reporte-diario: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
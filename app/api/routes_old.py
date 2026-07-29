# -*- coding: utf-8 -*-
import os
from flask import Blueprint, request, jsonify, send_file
from app.utils.logger import setup_logger
from config import settings
from app.services.notificacion_service import NotificacionService

# Importación de DTOs para validación
from app.schemas.persona import PersonaCreate, PersonaUpdate
from app.schemas.credito import CreditoCreate
from app.schemas.pago import PagoCreate

# Importación de servicios de comunicación
from app.services.whatsapp_service import WhatsAppService, TwilioProvider

logger = setup_logger(__name__)

def init_routes(servicio_pagos, servicio_personas, servicio_creditos, servicio_vendedores, servicio_finiquitos, servicio_estado_cuenta):
    """
    Inyecta los servicios y registra las rutas dentro de un Blueprint.
    Al definir las funciones aquí, los servicios nunca serán None.
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
            datos_validados = CreditoCreate(**request.get_json())
            resultado, error = servicio_creditos.crear_credito(datos_validados)
            
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
            datos_validados = PagoCreate(**request.get_json())
            
            # 1. Registramos el pago y generamos el PDF
            # (Asumimos que tu servicio de pago devuelve estos datos)
            ruta, nombre, url, pago_obj, credito_obj, persona_obj = servicio_pagos.registrar_pago(datos_validados)            
            
            if not ruta:
                return jsonify({'error': nombre}), 400

            # 3. Generar el texto usando el método estático (como el static de Java)
            texto_sms = NotificacionService.generar_texto_recibo(
                pago_obj, 
                credito_obj, 
                persona_obj
            )
                
            return jsonify({
                'mensaje': 'Pago procesado exitosamente',
                'url_recibo': url,
                'nombre_archivo': nombre,
                'sms_copy_paste': texto_sms  # <--- Aquí verás el texto en Postman
            }), 201

        except Exception as e:
            logger.error(f"Error en POST /pago: {str(e)}")
            return jsonify({'error': f"Error en procesamiento de pago: {str(e)}"}), 400
        

    @api_blueprint.route('/recibo/<nombre_recibo>', methods=['GET'])
    def obtener_recibo(nombre_recibo):
        ruta_recibo = os.path.join(settings.RECIBOS_DIR, nombre_recibo)
        if os.path.exists(ruta_recibo):
            return send_file(ruta_recibo, as_attachment=True)
        return jsonify({'error': 'Archivo no encontrado'}), 404


    @api_blueprint.route('/credito/<int:credito_id>/generar-finiquito', methods=['POST'])
    def generar_finiquito(credito_id):
        try:
            logger.info(f"Iniciando generación manual de finiquito para crédito: {credito_id}")
            
            url, error = servicio_finiquitos.generar_finiquito_manual(credito_id)
            
            if error:
                return jsonify({'error': error}), 400
                
            return jsonify({
                'mensaje': 'Finiquito generado y registrado correctamente',
                'url_documento': url
            }), 201
            
        except Exception as e:
            logger.error(f"Error en POST /generar-finiquito: {str(e)}")
            return jsonify({'error': f"Error al procesar finiquito: {str(e)}"}), 500
        

    # NUEVA RUTA PARA ESTADO DE CUENTA
    @api_blueprint.route('/credito/<int:credito_id>/estado-cuenta', methods=['GET'])
    def generar_estado_cuenta(credito_id):
        """
        Genera y devuelve la URL del PDF del estado de cuenta detallado.
        """
        try:
            logger.info(f"Generando estado de cuenta para crédito ID: {credito_id}")
            
            # Llamamos al método que creamos en el Paso 2
            url, error = servicio_estado_cuenta.generar_estado_cuenta_completo(credito_id)
            
            if error:
                return jsonify({'error': error}), 400
                
            return jsonify({
                'mensaje': 'Estado de cuenta generado exitosamente',
                'url_pdf': url,
                'credito_id': credito_id
            }), 200
            
        except Exception as e:
            logger.error(f"Error en GET /credito/{credito_id}/estado-cuenta: {str(e)}")
            return jsonify({'error': 'Error interno al generar el documento'}), 500
        


    # --- REPORTES ---
    @api_blueprint.route('/cron/reporte-diario', methods=['POST'])
    def ejecutar_reporte_diario():
        try:
            resultado = servicio_creditos.enviar_reporte_diario_vencimientos()
            return jsonify({
                'success': True, 
                'enviado': bool(resultado)
            }), 200
        except Exception as e:
            logger.error(f"Error en cron reporte-diario: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    return api_blueprint
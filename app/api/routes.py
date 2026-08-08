# -*- coding: utf-8 -*-
import os
from flask import Blueprint, request, jsonify, send_file
from app.utils.logger import setup_logger
from config import settings
from app.services.notificacion_service import NotificacionService

# Importación de DTOs para validación
from app.schemas.persona import PersonaCreate, PersonaUpdate
from app.schemas.credito import CreditoCreate, ConsultaSaldoDiarioRequest, ReestructuracionCreate
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
    servicio_saldo_diario=None,       # <--- Se agregó la coma faltante
    servicio_reestructuracion=None
):
    """
    Inyecta los servicios y registra las rutas dentro de un Blueprint.
    Mantiene compatibilidad total con la lógica previa e integra el cálculo de saldo diario.
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
            logger.error(f"Error en POST /credito: {str(e)}")
            return jsonify({'error': f"Datos inválidos: {str(e)}"}), 400

    @api_blueprint.route('/creditos/saldo-diario', methods=['POST'])
    def consultar_saldo_diario():
        """
        Calcula el desglose de intereses y capital diario.
        """
        if not servicio_saldo_diario:
            return jsonify({"error": "El ServicioSaldoDiario no fue inicializado en el servidor"}), 500

        try:
            data = request.get_json()
            req = ConsultaSaldoDiarioRequest(**data)
        except Exception as e:
            logger.error(f"Error en validación POST /creditos/saldo-diario: {str(e)}")
            return jsonify({"error": "Parámetros de entrada inválidos", "detalle": str(e)}), 400

        try:
            resultado = servicio_saldo_diario.calcular_desglose_saldo_diario(
                credito_id=req.credito_id,
                tasa_anual=req.tasa_anual,
                tasa_mora_anual=req.tasa_mora_anual,
                fecha_corte=req.fecha_corte
            )
            return jsonify(resultado), 200
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 404
        except Exception as ex:
            logger.error(f"Error interno en POST /creditos/saldo-diario: {str(ex)}")
            return jsonify({"error": "Error interno del servidor", "detalle": str(ex)}), 500

    # --- RUTA DE REESTRUCTURACIÓN DE CRÉDITOS ---
    @api_blueprint.route('/credito/reestructurar', methods=['POST'])
    def reestructurar_credito():
        if not servicio_reestructuracion:
            return jsonify({"error": "El Servicio de Reestructuración no está inicializado"}), 500

        try:
            datos_validados = ReestructuracionCreate(**request.get_json())
            resultado, error = servicio_reestructuracion.reestructurar_credito(datos_validados)

            if error:
                return jsonify({'error': error}), 400

            return jsonify({
                'mensaje': 'Crédito reestructurado exitosamente',
                'datos': resultado
            }), 201

        except Exception as e:
            logger.error(f"Error en POST /credito/reestructurar: {str(e)}")
            return jsonify({'error': f"Datos de entrada inválidos: {str(e)}"}), 400

    # --- RUTAS DE PAGOS Y RECIBOS ---
    @api_blueprint.route('/pago', methods=['POST'])
    def registrar_pago():
        try:
            datos_validados = PagoCreate(**request.get_json())
            
            # Mantiene los 6 valores de retorno que espera tu frontend/Postman
            ruta, nombre, url, pago_obj, credito_obj, persona_obj = servicio_pagos.registrar_pago(datos_validados)            
            
            if not ruta:
                return jsonify({'error': nombre}), 400

            texto_sms = NotificacionService.generar_texto_recibo(
                pago_obj, 
                credito_obj, 
                persona_obj
            )
                
            return jsonify({
                'mensaje': 'Pago procesado exitosamente',
                'url_recibo': url,
                'nombre_archivo': nombre,
                'sms_copy_paste': texto_sms
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

    # --- DOCUMENTOS (FINIQUITOS Y ESTADO DE CUENTA) ---
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

    @api_blueprint.route('/credito/<int:credito_id>/estado-cuenta', methods=['GET'])
    def generar_estado_cuenta(credito_id):
        try:
            logger.info(f"Generando estado de cuenta para crédito ID: {credito_id}")
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

    # --- CRON / TAREAS PROGRAMADAS ---
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
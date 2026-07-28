# -*- coding: utf-8 -*-
import os
from flask import Blueprint, request, jsonify, send_file
from app.utils.logger import setup_logger
from config import settings
from app.services.notificacion_service import NotificacionService
from app.schemas.credito import ConsultaSaldoDiarioRequest

# Importaciones DTO
from app.schemas.persona import PersonaCreate, PersonaUpdate
from app.schemas.credito import CreditoCreate
from app.schemas.pago import PagoCreate

logger = setup_logger(__name__)


def init_routes(
    servicio_pagos, 
    servicio_personas, 
    servicio_creditos, 
    servicio_vendedores, 
    servicio_finiquitos, 
    servicio_estado_cuenta, 
    servicio_saldo_diario
):
    """
    Inyecta los 7 servicios y registra las rutas dentro del Blueprint 'api'.
    """
    api_blueprint = Blueprint('api', __name__)

    # -------------------------------------------------------------------------
    # SERVICIOS SECUNDARIOS / INFRAESTRUCTURA
    # -------------------------------------------------------------------------
    try:
        notificacion_service = NotificacionService(
            whatsapp_service=None,
            pdf_service=getattr(servicio_pagos, 'pdf_generator', None),
            base_url_pdf=getattr(settings, 'BASE_URL_PDF', '')
        )
    except Exception as e_notif_init:
        logger.warning(f"No se pudo inicializar NotificacionService: {str(e_notif_init)}")
        notificacion_service = None

    # -------------------------------------------------------------------------
    # RUTAS: SALDO DIARIO
    # -------------------------------------------------------------------------
    @api_blueprint.route('/creditos/saldo-diario', methods=['POST'])
    def consultar_saldo_diario():
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

    # -------------------------------------------------------------------------
    # RUTAS: FINIQUITOS
    # -------------------------------------------------------------------------
    @api_blueprint.route('/credito/<int:credito_id>/generar-finiquito', methods=['POST'])
    def generar_finiquito(credito_id):
        try:
            url_pdf, error = servicio_finiquitos.generar_finiquito_manual(credito_id)
            if error:
                return jsonify({'error': error}), 400
            return jsonify({'url_pdf': url_pdf}), 200
        except Exception as ex:
            logger.error(f"Error generando finiquito para crédito {credito_id}: {str(ex)}")
            return jsonify({'error': 'Error interno al generar finiquito', 'detalle': str(ex)}), 500

    # -------------------------------------------------------------------------
    # RUTAS: ESTADO DE CUENTA
    # -------------------------------------------------------------------------
    @api_blueprint.route('/credito/<int:credito_id>/estado-cuenta', methods=['GET'])
    def obtener_estado_cuenta(credito_id):
        try:
            estado_cuenta, error = servicio_estado_cuenta.generar_estado_cuenta(credito_id)
            if error:
                return jsonify({'error': error}), 404
            return jsonify(estado_cuenta), 200
        except Exception as ex:
            logger.error(f"Error al obtener estado de cuenta para crédito {credito_id}: {str(ex)}")
            return jsonify({'error': 'Error interno al obtener estado de cuenta'}), 500

    # -------------------------------------------------------------------------
    # RUTAS: PAGOS Y RECIBOS
    # -------------------------------------------------------------------------
    @api_blueprint.route('/pago', methods=['POST'])
    def registrar_pago():
        try:
            datos = request.get_json()
            pago_dto = PagoCreate(**datos)
            pago_creado, error = servicio_pagos.registrar_pago(pago_dto)

            if error:
                return jsonify({'error': error}), 400

            # Intento de notificación opcional
            if notificacion_service and hasattr(notificacion_service, 'notificar_pago_registrado'):
                try:
                    notificacion_service.notificar_pago_registrado(pago_creado)
                except Exception as e_notif:
                    logger.warning(f"Omisión de notificación para pago {pago_creado.id}: {str(e_notif)}")

            return jsonify({
                'mensaje': 'Pago registrado exitosamente',
                'pago': pago_creado.model_dump()
            }), 201

        except Exception as e:
            logger.error(f"Error en endpoint POST /pago: {str(e)}")
            return jsonify({'error': f'Error interno al procesar el pago: {str(e)}'}), 500

    @api_blueprint.route('/recibo/<path:filename>', methods=['GET'])
    def descargar_recibo(filename):
        try:
            filepath = os.path.join(settings.RECIBOS_DIR, filename)
            if not os.path.exists(filepath):
                return jsonify({'error': 'El archivo de recibo no existe'}), 404
            return send_file(filepath, mimetype='application/pdf')
        except Exception as e:
            logger.error(f"Error al servir recibo {filename}: {str(e)}")
            return jsonify({'error': 'Error interno al servir el archivo'}), 500

    # -------------------------------------------------------------------------
    # RUTAS: PERSONAS / CLIENTES
    # -------------------------------------------------------------------------
    @api_blueprint.route('/personas', methods=['GET'])
    def listar_personas():
        personas = servicio_personas.obtener_todas()
        return jsonify([p.model_dump() for p in personas]), 200

    @api_blueprint.route('/personas/<int:persona_id>', methods=['GET'])
    def obtener_persona(persona_id):
        persona = servicio_personas.obtener_por_id(persona_id)
        if not persona:
            return jsonify({'error': 'Persona no encontrada'}), 404
        return jsonify(persona.model_dump()), 200

    @api_blueprint.route('/personas', methods=['POST'])
    def crear_persona():
        try:
            datos = request.get_json()
            persona_dto = PersonaCreate(**datos)
            nueva_persona, error = servicio_personas.crear_persona(persona_dto)
            if error:
                return jsonify({'error': error}), 400
            return jsonify(nueva_persona.model_dump()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @api_blueprint.route('/personas/<int:persona_id>', methods=['PUT'])
    def actualizar_persona(persona_id):
        try:
            datos = request.get_json()
            persona_dto = PersonaUpdate(**datos)
            persona_actualizada, error = servicio_personas.actualizar_persona(persona_id, persona_dto)
            if error:
                return jsonify({'error': error}), 400
            return jsonify(persona_actualizada.model_dump()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    # -------------------------------------------------------------------------
    # RUTAS: CRÉDITOS
    # -------------------------------------------------------------------------
    @api_blueprint.route('/creditos', methods=['GET'])
    def listar_creditos():
        creditos = servicio_creditos.obtener_todos()
        return jsonify([c.model_dump() for c in creditos]), 200

    @api_blueprint.route('/creditos/<int:credito_id>', methods=['GET'])
    def obtener_credito(credito_id):
        credito = servicio_creditos.obtener_por_id(credito_id)
        if not credito:
            return jsonify({'error': 'Crédito no encontrado'}), 404
        return jsonify(credito.model_dump()), 200

    @api_blueprint.route('/creditos', methods=['POST'])
    def crear_credito():
        try:
            datos = request.get_json()
            credito_dto = CreditoCreate(**datos)
            nuevo_credito, error = servicio_creditos.crear_credito(credito_dto)
            if error:
                return jsonify({'error': error}), 400
            return jsonify(nuevo_credito.model_dump()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    # -------------------------------------------------------------------------
    # RUTAS: VENDEDORES
    # -------------------------------------------------------------------------
    @api_blueprint.route('/vendedores', methods=['GET'])
    def listar_vendedores():
        vendedores = servicio_vendedores.obtener_todos()
        return jsonify([v.model_dump() if hasattr(v, 'model_dump') else v for v in vendedores]), 200

    return api_blueprint
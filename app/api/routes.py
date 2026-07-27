# -*- coding: utf-8 -*-
import os
from flask import Blueprint, request, jsonify, send_file
from app.utils.logger import setup_logger
from config import settings
from app.services.notificacion_service import NotificacionService
from app.schemas.credito import ConsultaSaldoDiarioRequest  # Ya no se importa get_db_session ni la función suelta

# Importaciones DTO
from app.schemas.persona import PersonaCreate, PersonaUpdate
from app.schemas.credito import CreditoCreate
from app.schemas.pago import PagoCreate

# Servicios comunicación
from app.services.whatsapp_service import WhatsAppService, TwilioProvider

logger = setup_logger(__name__)

# Recibimos el séptimo servicio como argumento
def init_routes(servicio_pagos, servicio_personas, servicio_creditos, servicio_vendedores, servicio_finiquitos, servicio_estado_cuenta, servicio_saldo_diario):
    """
    Inyecta los servicios y registra las rutas dentro de un Blueprint.
    """
    api_blueprint = Blueprint('api', __name__)

    # ... (Sección de configuración de WhatsApp y otras rutas permanecen igual) ...

    # --- NUEVA RUTA CON SERVICIO INYECTADO ---
    @api_blueprint.route('/creditos/saldo-diario', methods=['POST'])
    def consultar_saldo_diario():
        try:
            data = request.get_json()
            req = ConsultaSaldoDiarioRequest(**data)
        except Exception as e:
            logger.error(f"Error en validación POST /creditos/saldo-diario: {str(e)}")
            return jsonify({"error": "Parámetros de entrada inválidos", "detalle": str(e)}), 400

        try:
            # Usamos directamente el servicio inyectado (él gestiona su propia sesión)
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

    # ... (Resto de tus rutas: /pago, /recibo, /generar-finiquito, etc.) ...

    return api_blueprint
import os
import datetime
from flask import Blueprint, request, jsonify, send_file
from app.services import ServicioPagos
from app.services import ServicioPersonas
from app.services import ServicioCreditos
from app.utils.logger import setup_logger

# Configurar logger
logger = setup_logger(__name__)

# Crear un Blueprint para las rutas de la API
api_blueprint = Blueprint('api', __name__)

# Referencia al servicio de pagos (se inicializará en app/__init__.py)
pago_service = None
persona_service = None
credito_service = None


def init_routes(servicio_pagos, servicio_personas, servicio_creditos):
    """
    Inicializa las rutas con el servicio de pagos, personas, creditos.
    
    Args:
        servicio_pagos (ServicioPagos): Servicio de gestion de pagos.
        servicio_personas (ServicioPersonas): Servicio de gestion de personas.
        servicio_creditos (ServicioCreditos): Servicio de gestion de creditos.
    """
    global pago_service
    global persona_service
    global credito_service
    # Asignar los servicios a las variables globales
    pago_service = servicio_pagos
    persona_service = servicio_personas
    credito_service = servicio_creditos
    logger.info("Rutas de la API inicializadas")
    return api_blueprint


@api_blueprint.route('/pago', methods=['POST'])
def registrar_pago():
    """
    Endpoint para registrar un nuevo pago.
    
    Returns:
        Response: Respuesta JSON con el resultado de la operacion.
    """
    try:
        datos = request.get_json()
        
        credito_id = datos.get('credito_id')
        fecha = datos.get('fecha', datetime.datetime.now().strftime('%Y-%m-%d'))
        monto = datos.get('monto')
        multa = datos.get('multa', 0)
        
        if not credito_id or not monto:
            return jsonify({'error': 'Faltan datos requeridos (credito_id, \
                            monto)'}), 400
        
        ruta_recibo, nombre_recibo = pago_service.registrar_pago(credito_id,
                                                                 fecha, monto,
                                                                 multa)
        
        if ruta_recibo:
            return jsonify({
                'mensaje': 'Pago registrado correctamente',
                'recibo': nombre_recibo,
                'ruta_recibo': ruta_recibo
            }), 201
        else:
            return jsonify({'error': nombre_recibo}), 400
    
    except Exception as e:
        logger.error(f"Error en endpoint /pago: {str(e)}")
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500


@api_blueprint.route('/recibo/<nombre_recibo>', methods=['GET'])
def obtener_recibo(nombre_recibo):
    """
    Endpoint para descargar un recibo generado.
    
    Args:
        nombre_recibo (str): Nombre del archivo de recibo.
        
    Returns:
        Response: Archivo PDF para descargar o respuesta de error.
    """
    try:
        # Obtener la ruta del directorio de recibos desde la configuracion
        from config import RECIBOS_DIR
        ruta_recibo = os.path.join(RECIBOS_DIR, nombre_recibo)
        
        if os.path.exists(ruta_recibo):
            return send_file(ruta_recibo, as_attachment=True)
        else:
            return jsonify({'error': 'Recibo no encontrado'}), 404
    
    except Exception as e:
        logger.error(f"Error en endpoint /recibo/{nombre_recibo}: {str(e)}")
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500
    
    
@api_blueprint.route('/persona', methods=['POST'])
def crear_persona():
    """
    Endpoint para registrar una nueva persona.
   
    Returns:
        Response: Respuesta JSON con el resultado de la operación.
    """
    try:
        datos = request.get_json()
        
        # Extraer datos de la persona
        nombres = datos.get('nombres')
        apellidos = datos.get('apellidos')
        fecha_nacimiento = datos.get('fecha_nacimiento')
        direccion = datos.get('direccion')
        telefono = datos.get('telefono')
        sexo = datos.get('sexo')
        
        # Validar datos requeridos
        if not nombres:
            return jsonify({
                'error': 'Faltan datos requeridos (nombres)'
            }), 400
        
        # Llamar al servicio para crear la persona
        resultado, error = persona_service.crear_persona(
            nombres=nombres,
            apellidos=apellidos,
            sexo=sexo,
            fecha_nacimiento=fecha_nacimiento,
            direccion=direccion,
            telefono=telefono,
        )
        
        # Comprobar resultado y devolver respuesta adecuada
        if resultado:
            # Convert SQLAlchemy object to dictionary for JSON serialization
            return jsonify({
                'mensaje': 'Persona registrada correctamente',
                'persona_id': resultado.persona_id,
                'datos': {
                    'nombres': resultado.nombres,
                    'apellidos': resultado.apellidos,
                    'fecha_nacimiento': str(resultado.fecha_nacimiento) if
                    resultado.fecha_nacimiento else None,
                    'direccion': resultado.direccion,
                    'telefono': resultado.telefono,
                    'sexo': resultado.sexo
                }
            }), 201
        else:
            # If error is a string, return it directly
            return jsonify({'error': error}), 400
    except Exception as e:
        logger.error(f"Error en endpoint /persona: {str(e)}")
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500    
    
    
@api_blueprint.route('/credito', methods=['POST'])
def crear_credito():
    """
    Endpoint para crear un nuevo credito.
   
    Returns:
        Response: Respuesta JSON con el resultado de la operación.
    """
    try:
        datos = request.get_json()
        
        # Extraer datos de la persona
        persona_id = datos.get('persona_id')
        total_credito_proyectado = datos.get('total_credito_proyectado')
        fecha = datos.get('fecha')
        cancelado = datos.get('cancelado')
        dia_pago = datos.get('dia_pago')
        cuota = datos.get('cuota')
        tasa_interes = datos.get('tasa_interes')
        monto_solicitado = datos.get('monto_solicitado')
        numero_cuotas = datos.get('numero_cuotas')
        comision_asistencia_financiera = datos.get('comision_asistencia_financiera') 
        comision_administrativa = datos.get('comision_administrativa')
        monto_colocado = datos.get('monto_colocado')
        monto_intereses = datos.get('monto_intereses')
        privado = datos.get('privado')
        observaciones = datos.get('observaciones')  
                
        # Llamar al servicio para crear la persona
        resultado, error = credito_service.crear_credito(
            persona_id=persona_id,
            total_credito_proyectado=total_credito_proyectado,
            fecha=fecha,
            cancelado=cancelado,
            dia_pago=dia_pago,
            cuota=cuota,
            tasa_interes=tasa_interes,
            monto_solicitado=monto_solicitado,
            numero_cuotas=numero_cuotas,
            comision_asistencia_financiera=comision_asistencia_financiera,
            comision_administrativa=comision_administrativa,
            monto_colocado=monto_colocado,
            monto_intereses=monto_intereses,
            privado=privado,
            observaciones=observaciones            
        )
        
        # Comprobar resultado y devolver respuesta adecuada
        if resultado:
            # Convert SQLAlchemy object to dictionary for JSON serialization
            return jsonify({
                'mensaje': 'Credito registrado correctamente',
                'credito_id': resultado.credito_id,
                'datos': {
                    'persona_id': resultado.persona_id,
                    'total_credito_proyectado': resultado.total_credito_proyectado,
                    'fecha': resultado.fecha,
                    'cancelado': resultado.cancelado,
                    'dia_pago': resultado.dia_pago,
                    'cuota': resultado.cuota,
                    'tasa_interes': resultado.tasa_interes,
                    'monto_solicitado': resultado.monto_solicitado,
                    'numero_cuotas': resultado.numero_cuotas,
                    'comision_asistencia_financiera': resultado.comision_asistencia_financiera,
                    'comision_administrativa': resultado.comision_administrativa,
                    'monto_colocado': resultado.monto_colocado,
                    'monto_intereses': resultado.monto_intereses,
                    'privado': resultado.privado,
                    'observaciones': resultado.observaciones                               
                }
            }), 201
        else:
            # If error is a string, return it directly
            return jsonify({'error': error}), 400
    except Exception as e:
        logger.error(f"Error en endpoint /credito: {str(e)}")
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500
"""
Rutas de la API relacionadas con la gestión de personas.
"""
from flask import request, jsonify
from app.utils.logger import setup_logger

# Configurar logger
logger = setup_logger(__name__)

def registrar_rutas_personas(blueprint, servicio_personas):
    """
    Registra las rutas relacionadas con la gestión de personas en el blueprint.
    
    Args:
        blueprint: Blueprint de Flask donde se registrarán las rutas.
        servicio_personas: Servicio para la gestión de personas.
    """
    # Ruta para crear una nueva persona
    @blueprint.route('/personas', methods=['POST'])
    def crear_persona():
        try:
            datos = request.json
            if not datos:
                return jsonify({'error': 'Datos no proporcionados'}), 400
                
            persona = servicio_personas.crear_persona(datos)
            return jsonify({'mensaje': 'Persona creada correctamente', 
                            'persona': persona}), 201
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
            
        except Exception as e:
            logger.error(f"Error al crear persona: {str(e)}")
            return jsonify({'error': 'Error interno del servidor'}), 500
    
    # Ruta para obtener una persona por su ID
    @blueprint.route('/personas/<int:id_persona>', methods=['GET'])
    def obtener_persona(id_persona):
        try:
            persona = servicio_personas.obtener_persona(id_persona)
            if not persona:
                return jsonify({'error': 'Persona no encontrada'}), 404
                
            return jsonify({'persona': persona}), 200
            
        except Exception as e:
            logger.error(f"Error al obtener persona {id_persona}: {str(e)}")
            return jsonify({'error': 'Error interno del servidor'}), 500
    
    # Ruta para buscar personas con filtros
    @blueprint.route('/personas', methods=['GET'])
    def buscar_personas():
        try:
            # Obtener parámetros de consulta
            filtros = {}
            if 'nombre' in request.args:
                filtros['nombre'] = request.args.get('nombre')
            if 'apellido' in request.args:
                filtros['apellido'] = request.args.get('apellido')
            if 'documento' in request.args:
                filtros['documento'] = request.args.get('documento')
            if 'activo' in request.args:
                filtros['activo'] = request.args.get('activo').lower() == 'true'
                
            # Obtener parámetros de paginación
            try:
                limite = int(request.args.get('limite', 100))
                pagina = int(request.args.get('pagina', 1))
            except ValueError:
                return jsonify({'error': 'Parámetros de paginación inválidos'}), 400
            
            # Obtener resultados
            personas = servicio_personas.buscar_personas(filtros, limite, 
                                                         pagina)
            total = servicio_personas.contar_personas(filtros)
            
            return jsonify({
                'personas': personas,
                'total': total,
                'pagina': pagina,
                'limite': limite,
                'paginas_totales': (total + limite - 1) // limite if limite > 0 else 0
            }), 200
            
        except Exception as e:
            logger.error(f"Error al buscar personas: {str(e)}")
            return jsonify({'error': 'Error interno del servidor'}), 500
    
    # Ruta para actualizar una persona
    @blueprint.route('/personas/<int:id_persona>', methods=['PUT'])
    def actualizar_persona(id_persona):
        try:
            datos = request.json
            if not datos:
                return jsonify({'error': 'Datos no proporcionados'}), 400
                
            actualizado = servicio_personas.actualizar_persona(id_persona, 
                                                               datos)
            if not actualizado:
                return jsonify({'error': 'No se pudo actualizar la persona'}), 404
                
            persona = servicio_personas.obtener_persona(id_persona)
            return jsonify({'mensaje': 'Persona actualizada correctamente', 
                            'persona': persona}), 200
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
            
        except Exception as e:
            logger.error(f"Error al actualizar persona {id_persona}: {str(e)}")
            return jsonify({'error': 'Error interno del servidor'}), 500
    
    # Ruta para eliminar (desactivar) una persona
    @blueprint.route('/personas/<int:id_persona>', methods=['DELETE'])
    def eliminar_persona(id_persona):
        try:
            eliminado = servicio_personas.eliminar_persona(id_persona)
            if not eliminado:
                return jsonify({'error': 'Persona no encontrada'}), 404
                
            return jsonify({'mensaje': 'Persona eliminada correctamente'}), 200
            
        except Exception as e:
            logger.error(f"Error al eliminar persona {id_persona}: {str(e)}")
            return jsonify({'error': 'Error interno del servidor'}), 500
    
    logger.info("Rutas de personas registradas correctamente")
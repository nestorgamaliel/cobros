# -*- coding: utf-8 -*-
from app.services.db_service import BaseDatos
from app.utils.logger import setup_logger



# Configurar logger
logger = setup_logger(__name__)


class ServicioPersonas:
    """Servicio para gestionar personas."""
    
    def __init__(self, db_service):
        """
        Inicializa el servicio de personas.
        
        Args:
            db_service (BaseDatos): Servicio de base de datos.
        """
        self.db = db_service
        logger.info("Servicio de personas inicializado")
    
    def crear_persona(self, nombres, apellidos, fecha_nacimiento=None, 
                      sexo=None, telefono=None, direccion=None):
        """
        Crea una nueva persona en la base de datos.
        
        Args:
            nombres (str): Nombres de la persona.
            apellidos (str): Apellidos de la persona.
            fecha_nacimiento (str/date, opcional): Fecha de nacimiento.
            sexo (str, opcional): Sexo de la persona ('M' o 'F').
            telefono (str, opcional): Número de teléfono.
            direccion (str, opcional): Dirección de residencia.
            
        Returns:
            tuple: (persona, None) en caso de éxito, o (None, mensaje_error) 
            en caso de error.
        """
        try:
            # Validaciones básicas
            if not nombres:
                return None, "Los nombres  son obligatorios"
            
            # Convertir fecha si viene como string
            if fecha_nacimiento and isinstance(fecha_nacimiento, str):
                try:
                    from datetime import datetime
                    fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
                except ValueError:
                    return None, "Formato de fecha incorrecto. Use YYYY-MM-DD"
            
            # Validar sexo si se proporciona
            if sexo and sexo not in ['M', 'F']:
                return None, "El sexo debe ser 'M' o 'F'"
                
            # Crear la persona
            persona = self.db.insertar_persona(
                nombres=nombres,
                apellidos=apellidos,
                fecha_nacimiento=fecha_nacimiento,
                sexo=sexo,
                telefono=telefono,
                direccion=direccion
            )
            
            logger.info(f"Persona creada correctamente. ID:\
                {persona.persona_id}")
            return persona, None
            
        except Exception as e:
            logger.error(f"Error al crear persona: {str(e)}")
            return None, f"Error: {str(e)}"
    
    def actualizar_persona(self, persona_id, **kwargs):
        """
        Actualiza los datos de una persona existente.
        
        Args:
            persona_id (int): ID de la persona a actualizar.
            **kwargs: Campos a actualizar (nombres, apellidos, etc.)
            
        Returns:
            tuple: (persona, None) en caso de éxito, o (None, mensaje_error) en caso de error.
        """
        try:
            # Obtener la persona
            persona = self.db.obtener_persona(persona_id)
            if not persona:
                return None, f"No se encontró la persona con ID: {persona_id}"
                
            # Convertir fecha si viene como string
            if 'fecha_nacimiento' in kwargs and \
                    isinstance(kwargs['fecha_nacimiento'], str):
                try:
                    from datetime import datetime
                    kwargs['fecha_nacimiento'] = datetime.strptime(
                        kwargs['fecha_nacimiento'], '%Y-%m-%d').date()
                except ValueError:
                    return None, "Formato de fecha incorrecto. Use YYYY-MM-DD"
            
            # Validar sexo si se proporciona
            if 'sexo' in kwargs and kwargs['sexo'] not in ['M', 'F']:
                return None, "El sexo debe ser 'M' o 'F'"
                
            # Actualizar la persona
            persona_actualizada = self.db.actualizar_persona(persona_id, 
                                                             **kwargs)
            
            logger.info(f"Persona actualizada correctamente. ID: {persona_id}")
            return persona_actualizada, None
            
        except Exception as e:
            logger.error(f"Error al actualizar persona: {str(e)}")
            return None, f"Error: {str(e)}"
    
    def listar_personas(self, filtros=None):
        """
        Obtiene un listado de personas según los filtros proporcionados.
        
        Args:
            filtros (dict, opcional): Filtros para la búsqueda.
            
        Returns:
            list: Lista de objetos Persona.
        """
        try:
            personas = self.db.listar_personas(filtros)
            return personas
        except Exception as e:
            logger.error(f"Error al listar personas: {str(e)}")
            raise
    
    def eliminar_persona(self, persona_id):
        """
        Elimina una persona de la base de datos.
        
        Args:
            persona_id (int): ID de la persona a eliminar.
            
        Returns:
            tuple: (True, None) en caso de éxito, o (False, mensaje_error) en \
                caso de error.
        """
        try:
            # Verificar si la persona existe
            persona = self.db.obtener_persona(persona_id)
            if not persona:
                return False, f"No se encontró la persona con ID: {persona_id}"
                
            # Verificar si tiene créditos asociados
            if persona.creditos and len(persona.creditos) > 0:
                return False, f"No se puede eliminar la persona porque tiene\
                    créditos asociados"
                
            # Eliminar la persona
            self.db.eliminar_persona(persona_id)
            
            logger.info(f"Persona eliminada correctamente. ID: {persona_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error al eliminar persona: {str(e)}")
            return False, f"Error: {str(e)}"
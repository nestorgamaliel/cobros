# -*- coding: utf-8 -*-
from app.services.db_service import BaseDatos
from app.utils.logger import setup_logger
from app.schemas.persona import PersonaCreate, PersonaUpdate
from typing import Optional, Dict, Any, Tuple, List

# Configurar logger
logger = setup_logger(__name__)

class ServicioPersonas:
    """Servicio para gestionar personas utilizando DTOs para validación."""
    
    def __init__(self, db_service: BaseDatos):
        """
        Inicializa el servicio de personas.
        
        Args:
            db_service (BaseDatos): Servicio de base de datos.
        """
        self.db = db_service
        logger.info("Servicio de personas inicializado con soporte Pydantic")
    
    def crear_persona(self, datos: PersonaCreate) -> Tuple[Optional[Any], Optional[str]]:
        """
        Crea una nueva persona en la base de datos.
        
        Args:
            datos (PersonaCreate): DTO con la información validada de la persona.
            
        Returns:
            tuple: (persona, None) en caso de éxito, o (None, mensaje_error) en caso de error.
        """
        try:
            # Pydantic ya validó nombres, fechas, sexo y DUI antes de llegar aquí.
            # .model_dump() convierte el DTO en el diccionario que espera el db_service.
            persona = self.db.insertar_persona(**datos.model_dump())
            
            logger.info(f"Persona creada correctamente. ID: {persona.persona_id}")
            return persona, None
            
        except Exception as e:
            logger.error(f"Error al crear persona: {str(e)}")
            return None, f"Error en base de datos: {str(e)}"
    
    def actualizar_persona(self, persona_id: int, datos: PersonaUpdate) -> Tuple[Optional[Any], Optional[str]]:
        """
        Actualiza los datos de una persona existente.
        
        Args:
            persona_id (int): ID de la persona a actualizar.
            datos (PersonaUpdate): DTO con los campos a actualizar (solo los presentes se procesan).
            
        Returns:
            tuple: (persona, None) en caso de éxito, o (None, mensaje_error) en caso de error.
        """
        try:
            # Verificar existencia
            persona = self.db.obtener_persona(persona_id)
            if not persona:
                return None, f"No se encontró la persona con ID: {persona_id}"
                
            # exclude_unset=True asegura que solo enviamos los campos que el usuario mandó en el JSON
            campos_a_actualizar = datos.model_dump(exclude_unset=True)
            
            if not campos_a_actualizar:
                return persona, "No se proporcionaron campos para actualizar"

            persona_actualizada = self.db.actualizar_persona(persona_id, **campos_a_actualizar)
            
            logger.info(f"Persona actualizada correctamente. ID: {persona_id}")
            return persona_actualizada, None
            
        except Exception as e:
            logger.error(f"Error al actualizar persona: {str(e)}")
            return None, f"Error en base de datos: {str(e)}"
    
    def listar_personas(self, filtros: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Obtiene un listado de personas según los filtros proporcionados.
        """
        try:
            return self.db.listar_personas(filtros)
        except Exception as e:
            logger.error(f"Error al listar personas: {str(e)}")
            raise
    
    def eliminar_persona(self, persona_id: int) -> Tuple[bool, Optional[str]]:
        """
        Elimina una persona de la base de datos verificando integridad.
        """
        try:
            persona = self.db.obtener_persona(persona_id)
            if not persona:
                return False, f"No se encontró la persona con ID: {persona_id}"
                
            # Mantenemos tu regla de negocio: no borrar si tiene créditos
            if persona.creditos and len(persona.creditos) > 0:
                return False, "No se puede eliminar: la persona tiene créditos asociados"
                
            self.db.eliminar_persona(persona_id)
            logger.info(f"Persona eliminada correctamente. ID: {persona_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error al eliminar persona: {str(e)}")
            return False, f"Error técnico: {str(e)}"
        
    def buscar_personas(self, filtros: Dict[str, Any], limite: int = 10, pagina: int = 1) -> Dict[str, Any]:
        """
        Busca personas según filtros con paginación.
        """
        try:
            if not filtros or not any(filtros.values()):
                return {
                    'success': False,
                    'error': 'Debe proporcionar al menos un criterio de búsqueda'
                }
            
            personas = self.db.buscar_personas(filtros, limite, pagina)
            total = self.db.contar_personas_filtradas(filtros)
            
            paginas_totales = (total + limite - 1) // limite if limite > 0 else 0
            
            return {
                'success': True,
                'personas': personas,
                'total': total,
                'paginas_totales': paginas_totales
            }
            
        except Exception as e:
            logger.error(f"Error al buscar personas: {str(e)}")
            return {'success': False, 'error': str(e)}
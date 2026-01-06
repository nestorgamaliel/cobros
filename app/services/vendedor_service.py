# -*- coding: utf-8 -*-
from app.services.db_service import BaseDatos
from app.utils.logger import setup_logger


# Configurar logger
logger = setup_logger(__name__)


class ServicioVendedores:
    """Servicio para gestionar vendedores."""
    
    def __init__(self, db_service):
        """
        Inicializa el servicio de vendedores.
        
        Args:
            db_service (BaseDatos): Servicio de base de datos.
        """
        self.db = db_service
        logger.info("Servicio de vendedores inicializado")
    
    def crear_vendedor(self, vendedor_id, nombre_vendedor):
        """
        Crea un nuevo vendedor en la base de datos.
        
        Args:
            vendedor_id (int): ID vendedor
            nombre_vendedor (str): Nombre vendedor
            
        Returns:
            tuple: (vendedor, None) en caso de éxito, o (None, mensaje_error) 
            en caso de error.
        """
        try:
            # Validaciones básicas
            if not nombre_vendedor:
                return None, "Nombre vendedor es obligatorios"

            if not vendedor_id:
                return None, "ID vendedor es obligatorios"
            
            # Crear el vendedor
            vendedor = self.db.insertar_vendedor(
                vendedor_id=vendedor_id,
                nombre_vendedor=nombre_vendedor
            )
            
            logger.info(f"Vendedor creado correctamente. ID:\
                {vendedor.vendedor_id}")
            return vendedor, None
            
        except Exception as e:
            logger.error(f"Error al crear vendedor: {str(e)}")
            return None, f"Error: {str(e)}"
    
    def actualizar_vendedor(self, vendedor_id, **kwargs):
        """
        Actualiza los datos de un vendedor existente.
        
        Args:
            vendedor_id (int): ID del vendedor a actualizar.
            **kwargs: Campos a actualizar (nombre_vendedor)
            
        Returns:
            tuple: (vendedor, None) en caso de éxito, o (None, mensaje_error) en caso de error.
        """
        try:
            # Obtener el vendedor
            vendedor = self.db.obtener_vendedor(vendedor_id)
            if not vendedor:
                return None, f"No se encontró vendedor con ID: {vendedor_id}"
                
            # Actualizar vendedor
            vendedor_actualizado = self.db.actualizar_vendedor(vendedor_id, 
                                                             **kwargs)
            
            logger.info(f"Vendedor actualizado correctamente. ID: {vendedor_id}")
            return vendedor_actualizado, None
            
        except Exception as e:
            logger.error(f"Error al actualizar vendedor: {str(e)}")
            return None, f"Error: {str(e)}"
    
    def listar_vendedores(self, filtros=None):
        """
        Obtiene un listado de vendedores según los filtros proporcionados.
        
        Args:
            filtros (dict, opcional): Filtros para la búsqueda.
            
        Returns:
            list: Lista de objetos Vendedor.
        """
        try:
            vendedores = self.db.listar_vendedores(filtros)
            return vendedores
        except Exception as e:
            logger.error(f"Error al listar vendedores: {str(e)}")
            raise
    
    def eliminar_vendedor(self, vendedor_id):
        """
        Elimina un vendedor de la base de datos.
        
        Args:
            vendedor_id (int): ID del vendedor a eliminar.
            
        Returns:
            tuple: (True, None) en caso de éxito, o (False, mensaje_error) en \
                caso de error.
        """
        try:
            # Verificar si vendedor existe
            vendedor = self.db.obtener_vendedor(vendedor_id)
            if not vendedor:
                return False, f"No se encontró vendedor con ID: {vendedor_id}"
                
            # Verificar si tiene créditos asociados
            if vendedor.creditos and len(vendedor.creditos) > 0:
                return False, f"No se puede eliminar vendedor porque tiene\
                    créditos asociados"
                
            # Eliminar la vendedor
            self.db.eliminar_vendedor(vendedor_id)
            
            logger.info(f"Vendedor eliminado correctamente. ID: {vendedor_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error al eliminar vendedor: {str(e)}")
            return False, f"Error: {str(e)}"
        
    def buscar_vendedores(self, filtros, limite=10, pagina=1):
            """
            Busca vendedores según los filtros proporcionados.
            
            Args:
                filtros (dict): Filtros de búsqueda (nombre_vendedor)
                limite (int): Límite de resultados por página
                pagina (int): Número de página
                
            Returns:
                dict: Diccionario con resultados de la búsqueda
            """
            try:
                logger.info(f"Buscando vendedores con filtros: {filtros}")
                
                # Validar filtros
                if not filtros or not any(filtros.values()):
                    return {
                        'success': False,
                        'error': 'Debe proporcionar al menos un criterio de búsqueda'
                    }
                
                # Obtener resultados del servicio de base de datos
                vendedores = self.db.buscar_vendedores(filtros, limite, pagina)
                total = self.db.contar_vendedores_filtradas(filtros)
                
                paginas_totales = (total + limite - 1) // limite if limite > 0 else 0
                
                logger.info(f"Encontradas {len(vendedores)} vendedores de un total de {total}")
                
                return {
                    'success': True,
                    'vendedores': vendedores,
                    'total': total,
                    'paginas_totales': paginas_totales
                }
                
            except Exception as e:
                logger.error(f"Error al buscar vendedores: {str(e)}")
                return {
                    'success': False,
                    'error': f'Error en la búsqueda: {str(e)}'
                }        
from app.services.db_service import BaseDatos
from app.services.pdf_service import GeneradorRecibos
from app.utils.logger import setup_logger
from sqlalchemy import text

# Configurar logger
logger = setup_logger(__name__)


class ServicioPagos:
    """Servicio para gestionar pagos y generar recibos."""
    
    def __init__(self, db_service, pdf_service):
        """
        Inicializa el servicio de pagos.
        
        Args:
            db_service (BaseDatos): Servicio de base de datos.
            pdf_service (GeneradorRecibos): Servicio de generacion de recibos.
        """
        self.db = db_service
        self.generador_recibos = pdf_service
        logger.info("Servicio de pagos inicializado")
        
    def registrar_pago(self, credito_id, fecha, monto, multa):
        """
        Registra un nuevo pago y genera el recibo correspondiente.
        
        Args:
            credito_id (int): ID del crédito al que corresponde el pago.
            fecha (str/date): Fecha del pago.
            monto (float): Monto del pago.
            multa (float): Monto de la multa, si aplica.
            
        Returns:
            tuple: (ruta_recibo, nombre_recibo) con las rutas del recibo 
            generado,
                   o (None, mensaje_error) en caso de error.
        """
        try:
            # Insertar el pago en la base de datos
            pago = self.db.insertar_pago(credito_id, fecha, monto, multa)
            
            # Obtener informacion relacionada
            credito = self.db.obtener_credito(credito_id)
            if not credito:
                logger.error(f"No se encontro el crédito con ID: {credito_id}")
                return None, "Error: Crédito no encontrado"
            
            persona = self.db.obtener_persona(credito.persona_id)                        
            if not persona:
                logger.error(f"No se encontro el persona con ID: {credito.persona_id}")
                return None, "Error: persona no encontrado"
                        
            # Obtener datos adicionales del crédito
            datos_credito = self.db.obtener_datos_credito(credito.credito_id)
        
            # Preparar los datos adicionales para el recibo
            datos_adicionales = {
                'ultima_fecha_pago': datos_credito.get('ultima_fecha_pago'),
                'saldo': datos_credito.get('saldo', 0),
                'dia_pago': datos_credito.get('dia_pago'),
                'cuota': datos_credito.get('cuota', 0),
            }                        
            
            # Generar el recibo de pago
            ruta_recibo, nombre_recibo = \
                self.generador_recibos.generar_recibo_pdf(pago, credito, 
                                                          persona, datos_adicionales)
            logger.info(f"Pago registrado correctamente. ID: {pago.pago_id}, \
                        Crédito: {credito_id}, Monto: {monto}")
            return ruta_recibo, nombre_recibo
            
        except Exception as e:
            logger.error(f"Error al registrar pago: {str(e)}")
            return None, f"Error: {str(e)}"
           

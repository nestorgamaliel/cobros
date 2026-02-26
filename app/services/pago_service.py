# -*- coding: utf-8 -*-
from app.services.db_service import BaseDatos
from app.services.pdf_service import GeneradorRecibos
from app.schemas.pago import PagoCreate
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ServicioPagos:
    """Servicio para gestionar pagos y generar recibos."""
    
    def __init__(self, db_service: BaseDatos, pdf_service: GeneradorRecibos):
        self.db = db_service
        self.generador_recibos = pdf_service
        logger.info("Servicio de pagos inicializado con DTOs")
        
    def registrar_pago(self, datos: PagoCreate):
        """
        Registra un pago, genera el PDF y actualiza la URL pública.
        """
        try:
            # 1. Insertar el pago usando la magia de los asteriscos
            # Pasamos los datos validados del DTO directamente a db_service
            pago = self.db.insertar_pago(**datos.model_dump())
            
            # 2. Obtener información para el recibo
            credito = self.db.obtener_credito(datos.credito_id)
            if not credito:
                return None, "Error: Crédito no encontrado", None
            
            persona = self.db.obtener_persona(credito.persona_id)
            datos_credito = self.db.obtener_datos_credito(credito.credito_id)
            
            # 3. Preparar datos adicionales para el PDF
            datos_adicionales = {
                'ultima_fecha_pago': datos_credito.get('ultima_fecha_pago'),
                'saldo': datos_credito.get('saldo', 0),
                'dia_pago': datos_credito.get('dia_pago'),
                'cuota': datos_credito.get('cuota', 0),
            }                        
            
            # 4. Generar y subir PDF (El pdf_service ya sube a GCS)
            ruta_local, nombre_archivo, url_publica = self.generador_recibos.generar_recibo_pdf(
                pago, credito, persona, datos_adicionales
            )

            # 5. Guardar la URL en la BD para futuras consultas
            if url_publica:
                self.db.actualizar_url_pago(pago.pago_id, datos.credito_id, url_publica)

            logger.info(f"Pago {pago.pago_id} procesado exitosamente")
            return ruta_local, nombre_archivo, url_publica
            
        except Exception as e:
            logger.error(f"Error crítico al registrar pago: {str(e)}")
            return None, f"Error: {str(e)}", None
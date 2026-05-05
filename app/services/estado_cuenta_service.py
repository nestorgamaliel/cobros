# app/services/estado_cuenta_service.py
from app.services.pdf_service import GeneradorEstadosCuenta
from app.models import Pago
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class EstadoCuentaService:
    def __init__(self, db_service):
        self.db = db_service
        # No instanciamos el generador aquí para ahorrar RAM al arrancar
        self._generador = None 

    @property
    def generador_pdf(self):
        """Lazy loading del generador para evitar Timeouts al inicio."""
        if self._generador is None:
            self._generador = GeneradorEstadosCuenta()
        return self._generador

    def generar_estado_cuenta_completo(self, credito_id):
        try:
            # 1. Obtener datos
            credito = self.db.obtener_credito(credito_id)
            if not credito:
                return None, f"Crédito {credito_id} no encontrado."

            persona = self.db.obtener_persona(credito.persona_id)
            
            # 2. Query optimizada (evitamos traer columnas innecesarias si es posible)
            pagos = (
                self.db.session.query(Pago)
                .filter(Pago.credito_id == credito_id)
                .order_by(Pago.fecha.asc())
                .all()
            )

            logger.info(f"Procesando {len(pagos)} pagos para el PDF...")

            # 3. Generación (Usamos la propiedad lazy)
            # Asegúrate que el método en pdf_service se llame así exactamente
            _, _, url_publica = self.generador_pdf.generar_estado_cuenta_pdf(
                persona=persona,
                credito=credito,
                pagos=pagos
            )

            return url_publica, None

        except Exception as e:
            logger.error(f"Fallo en generar_estado_cuenta_completo: {str(e)}")
            return None, str(e)
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
            # 1. Obtener datos básicos
            credito = self.db.obtener_credito(credito_id)
            if not credito:
                return None, f"Crédito {credito_id} no encontrado."

            persona = self.db.obtener_persona(credito.persona_id)
            
            # --- NUEVO: Obtener datos de la vista saldos_totales ---
            resumen_vistas = self.db.obtener_resumen_saldos_vista(credito_id)
            # Si el crédito está cancelado o en estado jurídico, la vista no lo devolverá (según su WHERE), 
            # por lo que definimos valores por defecto en ese escenario.
            if not resumen_vistas:
                resumen_vistas = {
                    "meses_pendientes": 0,
                    "nivel_mora": "Al día (o no aplica)",
                    "saldo_total": 0.0
                }
            # --------------------------------------------------------

            # 2. Query optimizada de pagos
            pagos = (
                self.db.session.query(Pago)
                .filter(Pago.credito_id == credito_id)
                .order_by(Pago.fecha.asc())
                .all()
            )

            logger.info(f"Procesando {len(pagos)} pagos para el PDF...")

            # 3. Generación (Pasamos 'resumen_vistas' como parámetro extra)
            _, _, url_publica = self.generador_pdf.generar_estado_cuenta_pdf(
                persona=persona,
                credito=credito,
                pagos=pagos,
                resumen_vistas=resumen_vistas  # <-- ENVIADO AL PDF
            )

            return url_publica, None

        except Exception as e:
            logger.error(f"Fallo en generar_estado_cuenta_completo: {str(e)}")
            return None, str(e)
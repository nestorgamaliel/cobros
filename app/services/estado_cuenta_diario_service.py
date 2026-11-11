# app/services/estado_cuenta_diario_service.py
from datetime import date
from app.services.pdf_service import GeneradorEstadoCuentaDiario
from app.services.saldo_diario_service import ServicioSaldoDiario
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class EstadoCuentaDiarioService:
    def __init__(self, db_service):
        self.db = db_service
        self._generador_pdf = None
        self._saldo_diario_service = None

    @property
    def generador_pdf(self):
        """Lazy loading del generador PDF para optimizar la memoria al arrancar."""
        if self._generador_pdf is None:
            self._generador_pdf = GeneradorEstadoCuentaDiario()
        return self._generador_pdf

    @property
    def saldo_diario_service(self):
        """Lazy loading del servicio de cálculo de saldo diario."""
        if self._saldo_diario_service is None:
            self._saldo_diario_service = ServicioSaldoDiario(self.db)
        return self._saldo_diario_service

    def generar_pdf_estado_cuenta_diario(
        self, 
        credito_id: int, 
        tasa_anual: float, 
        tasa_mora_anual: float = 0.05, 
        fecha_corte: date = None
    ):
        """
        Orquesta el cálculo de amortización diaria y la construcción del PDF.
        Returns: (url_publica, error_string)
        """
        try:
            # 1. Validar crédito
            credito = self.db.obtener_credito(credito_id)
            if not credito:
                return None, f"Crédito {credito_id} no encontrado."

            # 2. Obtener persona
            persona = self.db.obtener_persona(credito.persona_id)
            if not persona:
                return None, f"Persona asociada al crédito {credito_id} no encontrada."

            # 3. Calcular desglose diario
            desglose = self.saldo_diario_service.calcular_desglose_saldo_diario(
                credito_id=credito_id,
                tasa_anual=tasa_anual,
                tasa_mora_anual=tasa_mora_anual,
                fecha_corte=fecha_corte
            )

            # 4. Generar PDF
            logger.info(f"Generando PDF de saldo diario para crédito {credito_id}...")
            _, _, url_publica = self.generador_pdf.generar_pdf_saldo_diario(
                datos_desglose=desglose,
                persona=persona,
                credito=credito
            )

            return url_publica, None

        except Exception as e:
            logger.error(f"Fallo en generar_pdf_estado_cuenta_diario: {str(e)}")
            return None, str(e)
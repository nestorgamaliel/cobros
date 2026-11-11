# app/services/estado_cuenta_diario_service.py
import datetime
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
        if self._generador_pdf is None:
            self._generador_pdf = GeneradorEstadoCuentaDiario()
        return self._generador_pdf

    @property
    def saldo_diario_service(self):
        if self._saldo_diario_service is None:
            self._saldo_diario_service = ServicioSaldoDiario(self.db)
        return self._saldo_diario_service

    def generar_pdf_estado_cuenta_diario(
        self, 
        credito_id: int, 
        tasa_anual: float, 
        tasa_mora_anual: float = 0.05, 
        fecha_corte=None
    ):
        try:
            # Normalizar fecha_corte si viene como string ISO o datetime.date
            if isinstance(fecha_corte, str):
                fecha_corte = datetime.datetime.strptime(fecha_corte, "%Y-%m-%d").date()

            # 1. Obtener crédito
            credito = self.db.obtener_credito(credito_id)
            if not credito:
                return None, f"Crédito {credito_id} no encontrado en la base de datos."

            # 2. Obtener persona asociada
            persona_id = getattr(credito, 'persona_id', None)
            persona = self.db.obtener_persona(persona_id) if persona_id else None

            # 3. Calcular el desglose por saldo diario
            desglose = self.saldo_diario_service.calcular_desglose_saldo_diario(
                credito_id=credito_id,
                tasa_anual=float(tasa_anual),
                tasa_mora_anual=float(tasa_mora_anual),
                fecha_corte=fecha_corte
            )

            # 4. Generar el documento PDF
            logger.info(f"Generando documento PDF de saldo diario para crédito ID: {credito_id}")
            ruta_archivo, nombre_archivo, url_publica = self.generador_pdf.generar_pdf_saldo_diario(
                datos_desglose=desglose,
                persona=persona,
                credito=credito
            )

            return url_publica, None

        except Exception as e:
            logger.error(f"Fallo en generar_pdf_estado_cuenta_diario (Crédito {credito_id}): {str(e)}", exc_info=True)
            return None, str(e)
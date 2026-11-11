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

    def _extraer_valor(self, objeto, clave_attr, valor_defecto=None):
        """Helper universal para extraer valores de ORM, dict o tuplas."""
        if objeto is None:
            return valor_defecto
        if isinstance(objeto, dict):
            return objeto.get(clave_attr, valor_defecto)
        return getattr(objeto, clave_attr, valor_defecto)

    def generar_pdf_estado_cuenta_diario(
        self, 
        credito_id: int, 
        tasa_anual: float = 0.20, 
        tasa_mora_anual: float = 0.05, 
        fecha_corte=None
    ):
        try:
            # 1. Normalización de fecha_corte
            if isinstance(fecha_corte, str):
                try:
                    fecha_corte = datetime.datetime.strptime(fecha_corte, "%Y-%m-%d").date()
                except ValueError:
                    fecha_corte = datetime.date.today()
            elif not fecha_corte:
                fecha_corte = datetime.date.today()

            # 2. Obtener crédito de la BD
            credito = self.db.obtener_credito(credito_id)
            if not credito:
                return None, f"No se encontró el crédito con ID {credito_id}."

            # Extraer persona_id de forma segura
            persona_id = self._extraer_valor(credito, 'persona_id')
            persona = self.db.obtener_persona(persona_id) if persona_id else None

            # 3. Calcular desglose de saldo diario
            desglose = self.saldo_diario_service.calcular_desglose_saldo_diario(
                credito_id=credito_id,
                tasa_anual=float(tasa_anual or 0.20),
                tasa_mora_anual=float(tasa_mora_anual or 0.05),
                fecha_corte=fecha_corte
            )

            if not desglose:
                return None, "No se pudo generar el desglose de saldo diario."

            # 4. Generar el PDF
            logger.info(f"Generando documento PDF de saldo diario para crédito ID: {credito_id}")
            ruta_archivo, nombre_archivo, url_publica = self.generador_pdf.generar_pdf_saldo_diario(
                datos_desglose=desglose,
                persona=persona,
                credito=credito
            )

            return url_publica, None

        except Exception as e:
            logger.error(f"Error procesando crédito {credito_id} en EstadoCuentaDiarioService: {str(e)}", exc_info=True)
            return None, f"Error al generar el estado de cuenta por saldo diario: {str(e)}"
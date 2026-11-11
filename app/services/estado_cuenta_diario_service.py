# app/services/estado_cuenta_diario_service.py
import datetime
import traceback
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
    """Helper universal para extraer propiedades de objetos ORM, dicts o tuplas."""
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
      fecha_corte=None,
  ):
    """Orquesta el cálculo por saldo diario y la construcción del PDF con rastreo (Breadcrumbs)."""
    logger.info(
        f"=== [SERVICE BREADCRUMB A] Iniciando procesamiento para crédito"
        f" {credito_id} ==="
    )

    try:
      # 1. Normalización de fecha_corte
      logger.info(
          "[SERVICE BREADCRUMB B] Normalizando fecha de corte..."
          f" ({fecha_corte})"
      )
      if isinstance(fecha_corte, str):
        try:
          fecha_corte = datetime.datetime.strptime(
              fecha_corte, "%Y-%m-%d"
          ).date()
        except ValueError:
          fecha_corte = datetime.date.today()
      elif not fecha_corte:
        fecha_corte = datetime.date.today()

      # 2. Consultar Crédito en la BD
      logger.info(
          f"[SERVICE BREADCRUMB C] Obteniendo crédito {credito_id} desde BD..."
      )
      credito = self.db.obtener_credito(credito_id)
      logger.info(f"[SERVICE BREADCRUMB D] Crédito retornado: {credito}")

      if not credito:
        logger.error(
            f"[SERVICE BREADCRUMB ERROR] Crédito {credito_id} no existe"
        )
        return None, f"No se encontró el crédito con ID {credito_id}."

      # 3. Consultar Persona asociada
      logger.info("[SERVICE BREADCRUMB E] Extrayendo persona_id...")
      persona_id = self._extraer_valor(credito, "persona_id")
      logger.info(f"[SERVICE BREADCRUMB F] persona_id encontrado: {persona_id}")

      persona = self.db.obtener_persona(persona_id) if persona_id else None
      logger.info(f"[SERVICE BREADCRUMB G] Persona obtenida: {persona}")

      # 4. Cálculo de amortización diaria
      logger.info(
          "[SERVICE BREADCRUMB H] Calculando desglose de saldo diario con"
          " ServicioSaldoDiario..."
      )
      desglose = self.saldo_diario_service.calcular_desglose_saldo_diario(
          credito_id=credito_id,
          tasa_anual=float(tasa_anual or 0.20),
          tasa_mora_anual=float(tasa_mora_anual or 0.05),
          fecha_corte=fecha_corte,
      )
      logger.info(
          "[SERVICE BREADCRUMB I] Desglose retornado exitosamente."
          f" Claves/Tipo: {list(desglose.keys()) if isinstance(desglose, dict) else type(desglose)}"
      )

      if not desglose:
        return None, "No se pudo generar el desglose de saldo diario."

      # 5. Renderizado del PDF
      logger.info(
          "[SERVICE BREADCRUMB J] Invocando GeneradorEstadoCuentaDiario..."
      )
      ruta_archivo, nombre_archivo, url_publica = (
          self.generador_pdf.generar_pdf_saldo_diario(
              datos_desglose=desglose, persona=persona, credito=credito
          )
      )
      logger.info(
          f"[SERVICE BREADCRUMB K] PDF generado y almacenado: {url_publica}"
      )

      return url_publica, None

    except Exception as e:
      tb = traceback.format_exc()
      logger.error(
          f"=== [CRASH EXCEPCIÓN EN SERVICE para crédito {credito_id}]"
          f" ===\n{tb}"
      )
      raise e  # Re-lanzamos para que la ruta capture el traceback completo
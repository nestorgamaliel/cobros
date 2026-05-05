# app/services/estado_cuenta_service.py
from app.services.pdf_service import GeneradorEstadosCuenta
from app.models import Pago

class EstadoCuentaService:
    def __init__(self, db_service):
        """
        Inyectamos db_service para interactuar con SQLAlchemy
        y generador_pdf para crear el documento.
        """
        self.db = db_service
        self.generador_pdf = GeneradorEstadosCuenta()

    def generar_estado_cuenta_completo(self, credito_id):
        """
        Coordina la obtención de datos y la generación del PDF del historial.
        Retorna: (url_publica, None) si tiene éxito, (None, error) si falla.
        """
        try:
            # 1. Obtener el objeto Crédito
            credito = self.db.obtener_credito(credito_id)
            if not credito:
                return None, f"Crédito con ID {credito_id} no encontrado."

            # 2. Obtener la Persona asociada
            persona = self.db.obtener_persona(credito.persona_id)
            if not persona:
                return None, "No se encontró el cliente asociado a este crédito."

            # 3. Obtener pagos ORDENADOS cronológicamente
            pagos = (
                self.db.session.query(Pago)
                .filter_by(credito_id=credito_id)
                .order_by(Pago.fecha.asc())
                .all()
            )

            # 4. Generar el PDF y subirlo a GCS
            # Retorna: ruta_local, nombre_archivo, url_publica
            _, _, url_publica = self.generador_pdf.generar_estado_cuenta_pdf(
                persona=persona,
                credito=credito,
                pagos=pagos
            )

            return url_publica, None

        except Exception as e:
            return None, f"Error en EstadoCuentaService: {str(e)}"
from app.services.pdf_service import GeneradorFiniquitos

class FiniquitoService:
    def __init__(self, db_service):
        self.db = db_service
        self.generador_pdf = GeneradorFiniquitos()

    def generar_finiquito_manual(self, credito_id):
        try:
            # 1. Obtener datos necesarios
            datos = self.db.obtener_datos_credito(credito_id)
            if not datos:
                return None, "Crédito no encontrado"
            
            credito_obj = self.db.obtener_credito(credito_id)
            persona_obj = self.db.obtener_persona(credito_obj.persona_id)

            # 2. Generar el PDF y subir a GCS
            # Retorna: ruta_archivo, nombre_archivo, url_publica
            _, _, url_publica = self.generador_pdf.generar_finiquito_pdf(persona_obj, credito_obj)

            # 3. Guardar en la nueva tabla credito_finiquito
            self.db.insertar_registro_finiquito(
                credito_id=credito_id,
                url_documento=url_publica,
                monto_cancelado=datos['total_credito_proyectado']
            )

            return url_publica, None
        except Exception as e:
            return None, str(e)
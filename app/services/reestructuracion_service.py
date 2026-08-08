# -*- coding: utf-8 -*-
from datetime import date
from app.services.db_service import BaseDatos
from app.schemas.credito import ReestructuracionCreate
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ReestructuracionService:
    def __init__(self, db_service: BaseDatos):
        self.db = db_service
        logger.info("Servicio de Reestructuración inicializado correctamente")

    def reestructurar_credito(self, datos: ReestructuracionCreate):
        """
        Coordina la lógica de negocio para la reestructuración o consolidación de créditos.
        
        Recibe los datos validados desde Pydantic, calcula los valores derivados
        y ejecuta la transacción atómica en la base de datos.
        """
        try:
            # 1. Cálculo del monto de intereses proyectados
            monto_intereses = datos.total_credito_proyectado_nuevo - datos.monto_solicitado_nuevo
            if monto_intereses < 0:
                monto_intereses = 0

            # 2. Si no se especifica monto_colocado_nuevo, se asume igual al monto_solicitado_nuevo
            monto_colocado = (
                datos.monto_colocado_nuevo 
                if datos.monto_colocado_nuevo is not None 
                else datos.monto_solicitado_nuevo
            )

            # 3. Preparación del payload para el nuevo crédito
            payload_nuevo_credito = {
                'fecha': date.today(),
                'tasa_interes': datos.tasa_interes_nueva,
                'monto_solicitado': datos.monto_solicitado_nuevo,
                'numero_cuotas': datos.numero_cuotas_nuevo,
                'monto_colocado': monto_colocado,
                'monto_intereses': monto_intereses,
                'total_credito_proyectado': datos.total_credito_proyectado_nuevo,
                'cuota': datos.cuota_nueva,
                'dia_pago': datos.dia_pago_nuevo
            }

            # 4. Invocación de la transacción en la capa de datos
            nuevo_credito, reest_log = self.db.reestructurar_credito_transaccion(
                creditos_origen_ids=datos.creditos_origen_ids,
                datos_nuevo_credito=payload_nuevo_credito,
                observacion=datos.observacion
            )

            logger.info(
                f"Reestructuración exitosa: Créditos Origen {datos.creditos_origen_ids} -> "
                f"Nuevo Crédito #{nuevo_credito.credito_id} (Reestructuración ID: {reest_log.reestructuracion_id})"
            )

            # 5. Respuesta formateada para el cliente/frontend
            return {
                "nuevo_credito_id": nuevo_credito.credito_id,
                "creditos_origen_ids": datos.creditos_origen_ids,
                "reestructuracion_id": reest_log.reestructuracion_id,
                "fecha_reestructuracion": reest_log.fecha_reestructuracion.isoformat(),
                "monto_consolidado": float(nuevo_credito.monto_solicitado),
                "cuota_nueva": float(nuevo_credito.cuota),
                "total_proyectado": float(nuevo_credito.total_credito_proyectado)
            }, None

        except ValueError as ve:
            logger.warning(f"Error de validación o coincidencia en reestructuración: {str(ve)}")
            return None, str(ve)
        except Exception as e:
            logger.error(f"Error crítico durante la reestructuración: {str(e)}")
            return None, f"Error en procesamiento interno: {str(e)}"
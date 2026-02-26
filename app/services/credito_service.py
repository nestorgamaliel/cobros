# -*- coding: utf-8 -*-
from datetime import date, timedelta
import calendar
import os
from app.services.db_service import BaseDatos
from app.schemas.credito import CreditoCreate, CreditoUpdate
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ServicioCreditos:
    def __init__(self, db_service: BaseDatos, whatsapp_service=None):
        self.db = db_service
        self.whatsapp = whatsapp_service
        logger.info("Servicio de creditos inicializado con DTOs")
    
    def crear_credito(self, datos: CreditoCreate):
        """
        Crea un nuevo credito. Las validaciones ya fueron realizadas por Pydantic.
        """
        try:
            # Gracias a **kwargs en db_service, solo pasamos el dump del DTO
            credito = self.db.insertar_credito(**datos.model_dump())
            
            logger.info(f"Credito creado correctamente. ID: {credito.credito_id}")
            return credito, None
            
        except Exception as e:
            logger.error(f"Error al crear credito: {str(e)}")
            return None, f"Error en base de datos: {str(e)}"

    def actualizar_credito(self, credito_id: int, datos: CreditoUpdate):
        try:
            credito = self.db.actualizar_credito(credito_id, **datos.model_dump(exclude_unset=True))
            if not credito:
                return None, "Crédito no encontrado"
            return credito, None
        except Exception as e:
            logger.error(f"Error al actualizar credito: {str(e)}")
            return None, str(e)

    def enviar_reporte_diario_vencimientos(self):
        """
        Mantenemos tu lógica de negocio de WhatsApp intacta.
        """
        hoy = date.today()
        manana = hoy + timedelta(days=1)
        dias_a_consultar = {hoy.day, manana.day}
        
        ultimo_dia_mes = calendar.monthrange(hoy.year, hoy.month)[1]
        if hoy.day == ultimo_dia_mes:
            dias_a_consultar.update({28, 29, 30, 31, 1})

        dias_lista = tuple(dias_a_consultar)
        datos = self.db.obtener_cobros_dia(dias_lista)
        
        if not datos:
            mensaje = f"No hay cobros pendientes para hoy ({hoy.day}) y mañana ({manana.day})."
        else:
            mensaje = f" *REPORTE DE COBRANZA*\n Fecha: {hoy.strftime('%d/%m/%Y')}\n"
            mensaje += "--------------------------------------------\n\n"
            for fila in datos:
                mensaje += (f" *{fila['cliente']}*\n"
                            f" Cuota: ${fila['cuota']} | Día: {fila['dia_pago']}\n"
                            f" Obs: {fila['observacion'] or 'Sin obs.'}\n"
                            f"--------------------------------------------\n")

        admins_env = os.getenv("WHATSAPP_ADMINS", "")
        destinatarios = [n.strip() for n in admins_env.split(",") if n.strip()]
        
        if self.whatsapp and destinatarios:
            return self.whatsapp.enviar_reporte_grupal(mensaje, destinatarios)
        return None
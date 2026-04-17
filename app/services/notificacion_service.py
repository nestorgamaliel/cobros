# -*- coding: utf-8 -*-
import datetime
from app.utils.logger import setup_logger

# Inicializamos el logger para este servicio
logger = setup_logger(__name__)

class NotificacionService:
    """
    Servicio encargado de la gestión de mensajes y notificaciones 
    para los clientes de Lender Finanzas.
    """

    @staticmethod
    def generar_texto_recibo(pago, credito, persona):
        """
        Genera el cuerpo de texto formateado para enviar por SMS o WhatsApp.
        
        Args:
            pago: Objeto modelo con la información del pago.
            credito: Objeto modelo con la información del crédito.
            persona: Objeto modelo con los datos del cliente.
        
        Returns:
            str: Texto formateado para el mensaje.
        """
        try:
            # Aseguramos el formato de fecha, manejando si viene como objeto datetime
            fecha_pago = pago.fecha
            if isinstance(fecha_pago, (datetime.datetime, datetime.date)):
                fecha_str = fecha_pago.strftime('%d/%m/%Y')
            else:
                fecha_str = str(fecha_pago)

            # Construcción del cuerpo del mensaje (Formato solicitado)
            cuerpo = (
                f"Lender \n"
                f"Recibo: #{pago.pago_id}\n"
                f"Crédito: {credito.credito_id}\n"
                f"Fecha: {fecha_str}\n"
                f"Monto: ${pago.monto:,.2f}\n"
                f"Cliente: {persona.nombres} {persona.apellidos}\n"
                f"¡Gracias por su pago!"
            )
            
            logger.info(f"Texto de notificación generado exitosamente para el pago #{pago.pago_id}")
            return cuerpo

        except Exception as e:
            logger.error(f"Error al generar el texto de la notificación: {str(e)}")
            # Retornamos un texto genérico de emergencia para no romper el flujo
            return f"Lender Finanzas: Se ha registrado su pago #{pago.pago_id}. Gracias."

    @staticmethod
    def generar_texto_finiquito(persona, credito):
        """
        Opcional: Genera un texto corto para avisar que el finiquito está listo.
        """
        cuerpo = (
            f"Lender Finanzas\n"
            f"Estimado(a) {persona.nombres},\n"
            f"Su crédito {credito.credito_id} ha sido cancelado exitosamente. "
            f"Su finiquito legal ya está disponible. ¡Felicidades!"
        )
        return cuerpo
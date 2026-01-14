# -*- coding: utf-8 -*-
import os
from abc import ABC, abstractmethod
from twilio.rest import Client
from app.utils.logger import setup_logger

# Configurar logger para visibilidad en GCP Logs
logger = setup_logger(__name__)

# --- ABSTRACCIÓN ---
class WhatsAppProvider(ABC):
    @abstractmethod
    def enviar_mensaje(self, to_number: str, mensaje: str):
        """Contrato para enviar mensajes"""
        pass

# --- IMPLEMENTACIÓN TWILIO ---
class TwilioProvider(WhatsAppProvider):
    def __init__(self):
        self.sid = os.getenv("TWILIO_SID")
        self.token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        
        # Validación preventiva de configuración
        if not self.sid or not self.token:
            logger.error("Faltan las credenciales TWILIO_SID o TWILIO_AUTH_TOKEN en el entorno.")

    def enviar_mensaje(self, to_number: str, mensaje: str):
        try:
            client = Client(self.sid, self.token)
            
            # Limpiar número: quitar espacios y asegurar prefijo único
            clean_number = to_number.strip()
            if not clean_number.startswith("whatsapp:"):
                target = f"whatsapp:{clean_number}"
            else:
                target = clean_number

            message = client.messages.create(
                from_=self.from_number,
                body=mensaje,
                to=target
            )
            logger.info(f"Mensaje enviado exitosamente a {target}. SID: {message.sid}")
            return message.sid
        except Exception as e:
            logger.error(f"Error crítico en TwilioProvider enviando a {to_number}: {str(e)}")
            raise e

# --- IMPLEMENTACIÓN META (EJEMPLO FUTURO) ---
class MetaProvider(WhatsAppProvider):
    def enviar_mensaje(self, to_number: str, mensaje: str):
        # Esta clase queda lista para cuando decidas migrar a Meta
        # Solo necesitarás implementar la llamada POST a la Graph API
        logger.warning(f"MetaProvider: Simulación de envío a {to_number}. (No implementado)")
        return "meta_fake_id_123"

# --- SERVICIO PRINCIPAL ---
class WhatsAppService:
    def __init__(self, provider: WhatsAppProvider):
        """
        Inyectamos el proveedor (Twilio, Meta, etc.)
        """
        self.provider = provider

    def enviar_reporte_grupal(self, mensaje: str, destinatarios: list):
        """
        Envía el mismo mensaje a una lista de números (tú y tus compañeros).
        """
        resultados = []
        logger.info(f"Iniciando envío grupal a {len(destinatarios)} destinatarios.")
        
        for numero in destinatarios:
            if not numero: continue
            try:
                res = self.provider.enviar_mensaje(numero, mensaje)
                resultados.append(res)
            except Exception as e:
                # Si falla uno (ej. número mal escrito), intentamos el siguiente
                logger.error(f"Fallo individual al enviar a {numero}: {e}")
        
        return resultados
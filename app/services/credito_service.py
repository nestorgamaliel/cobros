# -*- coding: utf-8 -*-
from app.services.db_service import BaseDatos
from app.utils.logger import setup_logger


# Configurar logger
logger = setup_logger(__name__)


class ServicioCreditos:
    """Servicio para gestionar creditos."""
    
    def __init__(self, db_service):
        """
        Inicializa el servicio de creditos.
        
        Args:
            db_service (BaseDatos): Servicio de base de datos.
        """
        self.db = db_service
        logger.info("Servicio de creditos inicializado")
    
    def crear_credito(self, persona_id, 
                            fecha, 
                            tasa_interes, 
                            monto_solicitado, 
                            numero_cuotas, 
                            comision_asistencia_financiera, 
                            comision_administrativa, 
                            monto_colocado, 
                            monto_intereses,
                            total_credito_proyectado, 
                            cuota, 
                            dia_pago, 
                            cancelado, 
                            privado, 
                            observaciones):
        """
        Crea un nuevo credito en la base de datos.
        
        Args:
            
        Returns:
            tuple: (Credito, None) en caso de éxito, o (None, mensaje_error) 
            en caso de error.
        """
        try:
            # Validaciones básicas
            if tasa_interes and tasa_interes < 0:
                return None, "Tasa de interés no puede ser negativa"
            if monto_solicitado and monto_solicitado <= 0:
                return None, "Monto solicitado no puede ser negativa o cero"
            if numero_cuotas and numero_cuotas <= 0:
                return None, "Monto solicitado no puede ser negativa o cero"
            if comision_asistencia_financiera and comision_asistencia_financiera < 0:
                return None, "Comisión de asistencia financiera no puede ser negativa"
            if comision_administrativa and comision_administrativa < 0:
                return None, "Comisión administrativa no puede ser negativa"
            if monto_colocado and monto_colocado <= 0:  
                return None, "Monto colocado no puede ser negativa o cero"
            if monto_intereses and monto_intereses < 0:
                return None, "Monto de intereses no puede ser negativa"
            if total_credito_proyectado and total_credito_proyectado <= 0:
                return None, "Total de crédito proyectado no puede ser negativa o cero"
            if cuota and cuota <= 0:
                return None, "Cuota no puede ser negativa o cero"
            if dia_pago and dia_pago <= 0 or dia_pago > 31:
                return None, "Día de pago no puede ser negativo o mayor a 31"
            if cancelado and cancelado not in [0, 1]:
                return None, "Cancelado debe ser 0 o 1"
            if privado and privado not in [0, 1, 2]:
                return None, "Privado debe ser 0 o 1 o 2"
                
            
            # Convertir fecha si viene como string
            if fecha and isinstance(fecha, str):
                try:
                    from datetime import datetime
                    fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
                except ValueError:
                    return None, "Formato de fecha incorrecto. Use YYYY-MM-DD"
            
            # Crear la persona
            credito = self.db.insertar_credito(
                persona_id=persona_id,
                fecha=fecha,
                tasa_interes=tasa_interes,
                monto_solicitado=monto_solicitado,
                numero_cuotas=numero_cuotas,
                comision_asistencia_financiera=comision_asistencia_financiera,
                comision_administrativa=comision_administrativa,
                monto_colocado=monto_colocado,
                monto_intereses=monto_intereses,
                total_credito_proyectado=total_credito_proyectado,
                cuota=cuota,
                dia_pago=dia_pago,
                cancelado=cancelado,
                privado=privado,
                observaciones=observaciones                
            )
            
            logger.info(f"Credito creado correctamente. ID:\
                {credito.credito_id}")
            return credito, None
            
        except Exception as e:
            logger.error(f"Error al crear credito: {str(e)}")
            return None, f"Error: {str(e)}"
    
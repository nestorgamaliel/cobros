# app/services/saldo_diario_service.py
from datetime import datetime, date, timedelta
from app.models.models import Credito, Pago
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ServicioSaldoDiario:
    def __init__(self, db_service):
        self.db = db_service

    def calcular_desglose_saldo_diario(
        self,
        credito_id: int,
        tasa_anual: float,
        tasa_mora_anual: float = 0.05,
        fecha_corte: date = None
    ) -> dict:
        if not fecha_corte:
            fecha_corte = date.today()

        try:
            # 1. Consultar crédito usando la abstracción o query directa de tu db_service
            if hasattr(self.db, 'obtener_credito'):
                credito = self.db.obtener_credito(credito_id)
            else:
                credito = self.db.session.query(Credito).filter(Credito.id == credito_id).first()

            if not credito:
                raise ValueError(f"No se encontró el crédito con ID {credito_id}")

            monto_inicial = float(credito.monto_colocado)
            fecha_inicio = credito.fecha

            # Si es un string YYYY-MM-DD lo convertimos a objeto date
            if isinstance(fecha_inicio, str):
                fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            
            # 2. Consultar pagos registrados directamente con la sesión de db_service
            pagos_query = (
                self.db.session.query(Pago)
                .filter(Pago.credito_id == credito_id)
                .order_by(Pago.fecha.asc())
                .all()
            )

            # Filtrar los pagos que sean anteriores o iguales a la fecha de corte
            pagos = [
                p for p in pagos_query 
                if (p.fecha.date() if isinstance(p.fecha, datetime) else p.fecha) <= fecha_corte
            ]

            r_diario = tasa_anual / 365.0
            
            capital_vigente = monto_inicial
            fecha_anterior = fecha_inicio
            tramos = []

            # 3. Amortización tramo por tramo
            for p in pagos:
                p_fecha = p.fecha.date() if isinstance(p.fecha, datetime) else p.fecha
                dias_periodo = (p_fecha - fecha_anterior).days
                
                if dias_periodo > 0:
                    interes_generado = capital_vigente * r_diario * dias_periodo
                    monto_pago = float(p.monto)
                    
                    interes_cubierto = min(monto_pago, interes_generado)
                    abono_capital = max(0.0, monto_pago - interes_cubierto)
                    nuevo_capital = max(0.0, capital_vigente - abono_capital)

                    tramos.append({
                        "periodo": f"Del {fecha_anterior.strftime('%d-%b-%Y')} al {p_fecha.strftime('%d-%b-%Y')} ({dias_periodo} días)",
                        "fecha_inicio": fecha_anterior.isoformat(),
                        "fecha_fin": p_fecha.isoformat(),
                        "dias_transcurridos": dias_periodo,
                        "capital_inicial": round(capital_vigente, 2),
                        "tasa_anual_aplicada": round(tasa_anual * 100, 2),
                        "interes_generado": round(interes_generado, 2),
                        "pago_recibido": {
                            "fecha": p_fecha.isoformat(),
                            "monto": round(monto_pago, 2),
                            "cobertura_interes": round(interes_cubierto, 2),
                            "abono_capital": round(abono_capital, 2)
                        },
                        "capital_resultante": round(nuevo_capital, 2)
                    })
                    
                    capital_vigente = nuevo_capital
                    fecha_anterior = p_fecha

            # 4. Tramo actual acumulado
            dias_tramo_actual = (fecha_corte - fecha_anterior).days
            interes_tramo_actual = capital_vigente * r_diario * dias_tramo_actual

            tramo_actual = {
                "periodo": f"Del {fecha_anterior.strftime('%d-%b-%Y')} al {fecha_corte.strftime('%d-%b-%Y')} ({dias_tramo_actual} días acumulados)",
                "fecha_inicio": fecha_anterior.isoformat(),
                "fecha_fin": fecha_corte.isoformat(),
                "dias_transcurridos": dias_tramo_actual,
                "capital_vigente": round(capital_vigente, 2),
                "interes_generado": round(interes_tramo_actual, 2)
            }

            # Obtención del nombre del cliente
            nombre_cliente = "N/A"
            if hasattr(credito, 'persona') and credito.persona:
                nombre_cliente = f"{credito.persona.nombres} {credito.persona.apellidos}"
            elif hasattr(self.db, 'obtener_persona') and getattr(credito, 'persona_id', None):
                persona = self.db.obtener_persona(credito.persona_id)
                if persona:
                    nombre_cliente = f"{persona.nombres} {persona.apellidos}"

            return {
                "credito_id": credito_id,
                "cliente": nombre_cliente,
                "monto_otorgado": round(monto_inicial, 2),
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_corte": fecha_corte.isoformat(),
                "tasas_aplicadas": {
                    "tasa_anual_porcentaje": round(tasa_anual * 100, 2),
                    "tasa_mora_anual_porcentaje": round(tasa_mora_anual * 100, 2)
                },
                "desglose_tramos": tramos,
                "tramo_actual": tramo_actual,
                "resumen_saldo": {
                    "capital_pendiente": round(capital_vigente, 2),
                    "interes_acumulado_pendiente": round(interes_tramo_actual, 2),
                    "saldo_total_real": round(capital_vigente + interes_tramo_actual, 2)
                }
            }

        except Exception as e:
            logger.error(f"Error calculando saldo diario para crédito {credito_id}: {str(e)}")
            raise e
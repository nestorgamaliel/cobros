# listado_creditos_saldos.py
import pandas as pd
from datetime import date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app import create_app
from app.models.models import Credito, Pago
from config import settings

ARCHIVO_SALIDA = "creditos_daniel_saldo_real.csv"
TASA_ANUAL = 0.80
TASA_MORA = 0.05
FECHA_CORTE = date.today()

def calcular_saldo_directo(session, credito_id: int, tasa_anual: float, fecha_corte: date) -> float:
    """Calcula el saldo diario insoluto directamente en el script sin modificar servicios."""
    # 1. Obtener crédito filtrando por la clave primaria correcta (credito_id)
    credito = session.query(Credito).filter(Credito.credito_id == credito_id).first()
    if not credito:
        return 0.0

    monto_inicial = float(credito.monto_colocado)
    fecha_inicio = credito.fecha
    
    if hasattr(fecha_inicio, 'date'):
        fecha_inicio = fecha_inicio.date()

    # 2. Consultar pagos registrados
    pagos_query = (
        session.query(Pago)
        .filter(Pago.credito_id == credito_id)
        .order_by(Pago.fecha.asc())
        .all()
    )

    pagos = [
        p for p in pagos_query 
        if (p.fecha.date() if hasattr(p.fecha, 'date') else p.fecha) <= fecha_corte
    ]

    r_diario = tasa_anual / 365.0
    capital_vigente = monto_inicial
    fecha_anterior = fecha_inicio

    # 3. Aplicar amortización tramo por tramo
    for p in pagos:
        p_fecha = p.fecha.date() if hasattr(p.fecha, 'date') else p.fecha
        dias_periodo = (p_fecha - fecha_anterior).days
        
        if dias_periodo > 0:
            interes_generado = capital_vigente * r_diario * dias_periodo
            monto_pago = float(p.monto)
            
            interes_cubierto = min(monto_pago, interes_generado)
            abono_capital = max(0.0, monto_pago - interes_cubierto)
            capital_vigente = max(0.0, capital_vigente - abono_capital)
            fecha_anterior = p_fecha

    # 4. Tramo actual hasta la fecha de corte
    dias_tramo_actual = (fecha_corte - fecha_anterior).days
    interes_tramo_actual = capital_vigente * r_diario * dias_tramo_actual

    return round(capital_vigente + interes_tramo_actual, 2)


def generar_reporte_desde_sql():
    app = create_app()
    
    with app.app_context():
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        query = text("""
            SELECT credito_id, 
                   fecha_credito, 
                   nombres, 
                   apellidos, 
                   cuota,   
                   ultima_fecha_pago,
                   monto_otorgado
            FROM saldos_totales   
            WHERE nombre_vendedor LIKE '%Daniel%' 
            ORDER BY nombres, apellidos;
        """)
        
        print("Ejecutando consulta SQL en la base de datos...")
        
        try:
            resultado = session.execute(query)
            columnas = resultado.keys()
            filas = resultado.fetchall()
            
            df = pd.DataFrame(filas, columns=columnas)
            print(f"Se encontraron {len(df)} registros. Calculando saldo real diario...")
            
            saldos_reales = []
            
            for index, row in df.iterrows():
                c_id = int(row['credito_id'])
                try:
                    saldo_total = calcular_saldo_directo(
                        session=session,
                        credito_id=c_id,
                        tasa_anual=TASA_ANUAL,
                        fecha_corte=FECHA_CORTE
                    )
                    saldos_reales.append(saldo_total)
                    print(f"Crédito ID {c_id} ({row['nombres']} {row['apellidos']}): Saldo Real = ${saldo_total:.2f}")
                except Exception as e:
                    print(f"Error procesando crédito {c_id}: {str(e)}")
                    saldos_reales.append(0.0)
                    
            df['saldo_real_diario'] = saldos_reales
            df.to_csv(ARCHIVO_SALIDA, index=False, encoding='utf-8')
            
            print(f"\n¡Proceso completado con éxito!")
            print(f"Archivo generado: {ARCHIVO_SALIDA}")
            
        finally:
            session.close()

if __name__ == '__main__':
    generar_reporte_desde_sql()
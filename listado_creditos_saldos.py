# generar_reporte.py
import pandas as pd
from datetime import date
from sqlalchemy import text

from app import create_app
from app.services import get_db_service, get_saldo_diario_service

# Configuración de exportación
ARCHIVO_SALIDA = "creditos_daniel_saldo_real.csv"
TASA_ANUAL = 0.80     # 80% anual
TASA_MORA = 0.05      # 5% anual
FECHA_CORTE = date.today()

def generar_reporte_desde_sql():
    app = create_app()
    
    with app.app_context():
        db_service = get_db_service()
        servicio_saldo = get_saldo_diario_service()
        
        # 1. Consulta SQL enviada
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
        with db_service.session as session:
            # Ejecutar la consulta y cargar el resultado en un DataFrame
            resultado = session.execute(query)
            # Extraer nombres de columnas y registros
            columnas = resultado.keys()
            filas = resultado.fetchall()
            
            df = pd.DataFrame(filas, columns=columnas)
            
        print(f"Se encontraron {len(df)} registros. Calculando saldo real diario...")
        
        saldos_reales = []
        
        # 2. Iterar por cada crédito devuelto por el SQL
        for index, row in df.iterrows():
            credito_id = int(row['credito_id'])
            try:
                # Calcular saldo con tu servicio de saldos insolutos
                res = servicio_saldo.calcular_desglose_saldo_diario(
                    credito_id=credito_id,
                    tasa_anual=TASA_ANUAL,
                    tasa_mora_anual=TASA_MORA,
                    fecha_corte=FECHA_CORTE
                )
                saldo_total = res['resumen_saldo']['saldo_total_real']
                saldos_reales.append(saldo_total)
                print(f"Crédito ID {credito_id} ({row['nombres']} {row['apellidos']}): Saldo Real = ${saldo_total:.2f}")
            except Exception as e:
                print(f"Error procesando crédito {credito_id}: {str(e)}")
                saldos_reales.append(0.0)
                
        # 3. Agregar la columna con el saldo real al final del DataFrame
        df['saldo_real_diario'] = saldos_reales
        
        # 4. Guardar resultado final a CSV
        df.to_csv(ARCHIVO_SALIDA, index=False, encoding='utf-8')
        print(f"\n¡Proceso completado con éxito!")
        print(f"Archivo generado: {ARCHIVO_SALIDA}")

if __name__ == '__main__':
    generar_reporte_desde_sql()
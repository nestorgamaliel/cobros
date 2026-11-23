# -*- coding: utf-8 -*-
import os
import datetime
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from app import create_app, get_db_service, get_saldo_diario_service

def obtener_sesion(db_service):
    """Obtiene una sesión de SQLAlchemy adaptándose a la estructura de BaseDatos."""
    if hasattr(db_service, 'engine'):
        return Session(db_service.engine)
    elif hasattr(db_service, 'Session') and callable(db_service.Session):
        return db_service.Session()
    elif hasattr(db_service, 'session'):
        return db_service.session
    else:
        raise AttributeError("No se pudo determinar el método de sesión en BaseDatos")

def pedir_tasa(mensaje):
    """Solicita un valor numérico por consola con validación de entrada."""
    while True:
        try:
            val = input(mensaje).strip()
            num = float(val)
            if num < 0:
                print("  ❌ La tasa no puede ser negativa. Intenta de nuevo.")
                continue
            return num
        except ValueError:
            print("  ❌ Entrada inválida. Ingresa un número (ejemplo: 36.0 o 5.0).")

def generar_excel_creditos_privados():
    print("\n" + "="*60)
    print("    CONFIGURACIÓN DE PARÁMETROS PARA REPORTE DE SALDO DIARIO")
    print("="*60 + "\n")
    
    # 1. Prompts interactivos al inicio del script
    tasa_anual_usr = pedir_tasa("👉 Ingresa la Tasa de Interés Anual (%): ")
    tasa_mora_usr = pedir_tasa("👉 Ingresa la Tasa de Mora Anual (%): ")

    # 2. Inicialización del entorno e instancias
    app = create_app()
    db_service = get_db_service()
    saldo_diario_service = get_saldo_diario_service()
    
    with app.app_context():
        fecha_corte = datetime.date.today()
        print(f"\n=== PROCESANDO CRÉDITOS AL {fecha_corte.strftime('%d/%m/%Y')} ===")
        print(f"📊 Tasa Anual Aplicada a todos: {tasa_anual_usr:.2f}%")
        print(f"⚠️ Tasa Mora Aplicada a todos:  {tasa_mora_usr:.2f}%\n")
        
        # 3. Consulta SQL con CURRENT_DATE
        sql_query = text("""
            SELECT 
                CURRENT_DATE AS fecha_ejecucion,
                st.dui,
                st.persona_id,
                st.credito_id,
                st.nombres,
                st.apellidos,
                st.direccion,
                st.fecha_credito,
                st.monto_otorgado,
                st.cuota,
                st.numero_cuotas,
                st.meses_pendientes,
                p.telefono
            FROM saldos_totales st 
               left join persona p on (st.persona_id = p.persona_id)
            WHERE st.privado = 2 
               and st.meses_pendientes > 1
            ORDER BY st.meses_pendientes DESC;
        """)
        
        registros_procesados = []
        
        # 4. Procesamiento iterativo con la misma tasa para todos
        with obtener_sesion(db_service) as session:
            result = session.execute(sql_query)
            rows = result.mappings().all()
            
            print(f"Calculando {len(rows)} créditos con privado = 2...\n")
            
            for row in rows:
                credito_id = row['credito_id']
                
                interes_acumulado = 0.0
                capital_pendiente = 0.0
                saldo_total_real = 0.0
                
                try:
                    desglose = saldo_diario_service.calcular_desglose_saldo_diario(
                        credito_id=credito_id,
                        tasa_anual=tasa_anual_usr,
                        tasa_mora_anual=tasa_mora_usr,
                        fecha_corte=fecha_corte
                    )
                    
                    if isinstance(desglose, dict):
                        resumen = desglose.get("resumen_saldo", {})
                        interes_acumulado = float(resumen.get("interes_acumulado_pendiente", 0.0))
                        capital_pendiente = float(resumen.get("capital_pendiente", 0.0))
                        saldo_total_real = float(resumen.get("saldo_total_real", 0.0))
                        
                        print(f"📌 Crédito #{credito_id:<4} | Cap. Pend: ${capital_pendiente:>8,.2f} | Int. Acum: ${interes_acumulado:>8,.2f} | Total Real: ${saldo_total_real:>9,.2f}")

                except Exception as e:
                    print(f"⚠️ Error calculando saldo diario para crédito {credito_id}: {str(e)}")
                
                fecha_ejec_val = row.get('fecha_ejecucion')
                fecha_ejec_str = fecha_ejec_val.strftime('%Y-%m-%d') if fecha_ejec_val else fecha_corte.strftime('%Y-%m-%d')
                fecha_cred_str = row['fecha_credito'].strftime('%Y-%m-%d') if row['fecha_credito'] else None
                
                registro = {
                    "Fecha de Ejecución": fecha_ejec_str,
                    "DUI": row['dui'],
                    "Persona ID": row['persona_id'],
                    "Crédito ID": row['credito_id'],
                    "Nombres": row['nombres'],
                    "Apellidos": row['apellidos'],
                    "Dirección": row['direccion'],
                    "Telefono": row['telefono'],
                    "Fecha Crédito": fecha_cred_str,
                    "Monto Otorgado": float(row['monto_otorgado'] or 0.0),
                    "Cuota": float(row['cuota'] or 0.0),
                    "Número Cuotas": row['numero_cuotas'],
                    "Meses Pendientes": row['meses_pendientes'],
                    "Tasa Anual (%)": tasa_anual_usr,
                    "Tasa Mora (%)": tasa_mora_usr,
                    "Intereses Acumulados a la Fecha": interes_acumulado,
                    "Capital Pendiente": capital_pendiente,
                    "Saldo Total Real a la Fecha": saldo_total_real
                }
                registros_procesados.append(registro)
        
        # 5. Exportación a Excel
        df = pd.DataFrame(registros_procesados)
        nombre_archivo = f"reporte_creditos_privados_{fecha_corte.strftime('%Y%m%d')}.xlsx"
        
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="Saldos Privados", index=False)
            worksheet = writer.sheets["Saldos Privados"]
            
            header_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
            header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
            
            for col_num, col_name in enumerate(df.columns, 1):
                cell = worksheet.cell(row=1, column=col_num)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
                
                max_data_len = df[col_name].astype(str).str.len().max()
                max_len = max(int(max_data_len) if pd.notna(max_data_len) else 0, len(col_name)) + 4
                
                col_letter = get_column_letter(col_num)
                worksheet.column_dimensions[col_letter].width = max(max_len, 12)
                
                if col_name in ["Monto Otorgado", "Cuota", "Intereses Acumulados a la Fecha", "Capital Pendiente", "Saldo Total Real a la Fecha"]:
                    for row_num in range(2, len(df) + 2):
                        c = worksheet.cell(row=row_num, column=col_num)
                        c.number_format = '"$"#,##0.00'

        print(f"\n✅ Excel generado exitosamente: {os.path.abspath(nombre_archivo)}")
        return nombre_archivo

if __name__ == "__main__":
    generar_excel_creditos_privados()
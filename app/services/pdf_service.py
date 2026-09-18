# -*- coding: utf-8 -*-
import os
import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY
from num2words import num2words 
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from app.utils.logger import setup_logger
from app.utils.gcs_uploader import subir_archivo_a_gcs
from config import settings

logger = setup_logger(__name__)

class GeneradorDocumentos:
    """Clase base con configuración común para documentos PDF de Lender Finanzas."""
    
    def __init__(self, directorio_salida=None, logo_path=None):
        self.directorio_salida = directorio_salida or settings.RECIBOS_DIR
        if not os.path.exists(self.directorio_salida):
            os.makedirs(self.directorio_salida)
        
        self.logo_path = logo_path if logo_path else settings.LOGO_PATH
        logger.info(f"Servicio de PDF inicializado en: {self.directorio_salida}")

    def _subir_a_gcs(self, ruta_local, nombre_archivo, carpeta):
        """Método interno para subir el archivo generado a Google Cloud."""
        bucket_name = settings.GCS_BUCKET_NAME
        destino = f"{carpeta}/{nombre_archivo}"
        url_publica = subir_archivo_a_gcs(ruta_local, destino, bucket_name)
        logger.info(f"Archivo subido a {carpeta}: {url_publica}")
        return url_publica

    def _monto_a_letras(self, monto):
        """Convierte números a formato legal en español."""
        enteros = int(monto)
        centavos = int(round((monto - enteros) * 100))
        letras = num2words(enteros, lang='es').upper()
        return f"{letras} {centavos:02d}/100 DÓLARES DE LOS ESTADOS UNIDOS DE AMÉRICA"
    
    def obtener_configuracion_sucursal(self, privado):
            """Devuelve el logo y el firmante según el tipo de crédito."""
            if privado == 2:
                return {
                    "logo": os.path.join(os.path.dirname(self.logo_path), "Lenser_logo.png"),
                    "firmante_nombre": "Jazmin Hernandez",
                    "firmante_cargo": "Gerente Operaciones",
                    "ancho": 1.5
                }
            # Configuración por defecto
            return {
                "logo": self.logo_path,
                "firmante_nombre": "Evelyn García",
                "firmante_cargo": "Gerente Operaciones",
                "ancho": 2.5
            }



class GeneradorRecibos(GeneradorDocumentos):
    """Especializada en generar recibos de pago."""
    
    def generar_recibo_pdf(self, pago, credito, persona, datos_adicionales=None):
        config = self.obtener_configuracion_sucursal(credito.privado)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()
        
        right_style = ParagraphStyle('RightStyle', parent=styles['Normal'], alignment=TA_RIGHT)
        elements = []
        
        if os.path.exists(config["logo"]):
            logo = Image(config["logo"], width=config["ancho"]*inch, height=1*inch)
            elements.append(logo)
        
        elements.append(Paragraph(f"<b>RECIBO DE PAGO #{pago.pago_id}</b>", styles['Title']))
        elements.append(Spacer(1, 20))
        
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y")
        elements.append(Paragraph(f"<b>Fecha de emisión:</b> {fecha_actual}", right_style))
        elements.append(Spacer(1, 20))
        
        persona_info = [["INFORMACIÓN DEL CLIENTE"], [f"Nombre: {persona.nombres} {persona.apellidos}"], [f"DUI: {persona.dui}"], [f"Teléfono: {persona.telefono}"]]
        t_persona = Table(persona_info, colWidths=[450])
        t_persona.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('ALIGN', (0, 0), (-1, 0), 'CENTER'), ('BOX', (0, 0), (-1, -1), 1, colors.black)]))
        elements.append(t_persona)
        elements.append(Spacer(1, 20))
        
        fecha_credito = getattr(credito, 'fecha', datetime.datetime.now()).strftime('%d/%m/%Y')
        credito_info = [
            ["INFORMACIÓN DEL CRÉDITO"],
            [f"Crédito ID: {credito.credito_id}", f"Fecha de inicio: {fecha_credito}"],
            [f"Monto total: ${credito.total_credito_proyectado:,.2f}", f"Día de pago: {credito.dia_pago}"],
            [f"Cuota: ${credito.cuota:,.2f}", ""]
        ]
        t_credito = Table(credito_info, colWidths=[225, 225])
        t_credito.setStyle(TableStyle([('BACKGROUND', (0, 0), (1, 0), colors.lightgrey), ('SPAN', (0, 0), (1, 0)), ('ALIGN', (0, 0), (1, 0), 'CENTER'), ('GRID', (0, 1), (1, -1), 1, colors.black), ('BOX', (0, 0), (1, -1), 1, colors.black)]))
        elements.append(t_credito)
        elements.append(Spacer(1, 20))
        
        saldo = datos_adicionales.get('saldo', 0) if datos_adicionales else 0
        pago_info = [["DETALLE DEL PAGO ACTUAL"], [f"Fecha de pago: {pago.fecha.strftime('%d/%m/%Y')}", f"Monto pagado: ${pago.monto:,.2f}"]]
        if pago.intereses: pago_info.append(["", f"Intereses: ${pago.intereses:,.2f}"])
        if pago.multa: pago_info.append(["", f"Mora/Multa: ${pago.multa:,.2f}"])
        pago_info.append(["", f"Saldo pendiente: ${saldo:,.2f}"])
        
        t_pago = Table(pago_info, colWidths=[225, 225])
        t_pago.setStyle(TableStyle([('BACKGROUND', (0, 0), (1, 0), colors.lightgrey), ('SPAN', (0, 0), (1, 0)), ('ALIGN', (0, 0), (1, 0), 'CENTER'), ('GRID', (0, 1), (1, -1), 1, colors.black)]))
        elements.append(t_pago)
        elements.append(Spacer(1, 40))
        
        elements.append(Table([["________________________"], [f"{config['firmante_nombre']} | {config['firmante_cargo']}"]], colWidths=[450], style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        
        doc.build(elements)
        nombre_archivo = f"recibo_pago_{pago.pago_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        
        with open(ruta_archivo, 'wb') as f:
            f.write(buffer.getvalue())
        
        url_publica = self._subir_a_gcs(ruta_archivo, nombre_archivo, "recibos")
        return ruta_archivo, nombre_archivo, url_publica

class GeneradorFiniquitos(GeneradorDocumentos):
    """Especializada en generar finiquitos legales para Lender Finanzas."""

    def generar_finiquito_pdf(self, persona, credito, datos_firmante=None):
        config = self.obtener_configuracion_sucursal(credito.privado)
        """Genera el PDF legal del finiquito con firma digital, lo guarda localmente y lo sube a GCS."""
        
        if datos_firmante is None:
            # CORRECCIÓN: La 'f' va fuera de las comillas para que sea un f-string válido
            datos_firmante = {
                "nombre": f"{config['firmante_nombre']}",
                "cargo": f"{config['firmante_cargo']}",
                "dui": "02248960-2"
            }

        # Configuración de la firma
        ruta_firma = os.path.join(os.path.dirname(config["logo"]), "FirmaLegal.png")

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter, 
            leftMargin=inch, 
            rightMargin=inch, 
            topMargin=inch, 
            bottomMargin=inch
        )
        styles = getSampleStyleSheet()
        
        # Estilo legal justificado
        legal_style = ParagraphStyle(
            'LegalBody', 
            parent=styles['Normal'], 
            fontSize=11, 
            leading=16, 
            alignment=TA_JUSTIFY
        )
        
        elements = []

        # Logo de la empresa
        if os.path.exists(self.logo_path):
            logo = Image(self.logo_path, width=2.5*inch, height=0.8*inch)
            elements.append(logo)
            elements.append(Spacer(1, 30))

        elements.append(Paragraph("<b>A QUIEN INTERESE:</b>", styles['Normal']))
        elements.append(Spacer(1, 20))

        # Lógica de género
        sexo_val = getattr(persona, 'sexo', 'M').upper()
        tratamiento = "la señora" if sexo_val == 'F' else "el señor"

        monto_letras = self._monto_a_letras(credito.total_credito_proyectado)
        
        # CORRECCIÓN: Extracción de variables limpias para evitar conflictos 
        # de comillas simples/dobles dentro del f-string del cuerpo
        nombre_firmante_limpio = datos_firmante['nombre'].replace("<b>", "").replace("</b>", "")
        cargo_firmante = datos_firmante['cargo']
        dui_firmante = datos_firmante['dui']
        nombre_cliente = f"{persona.nombres} {persona.apellidos}"
        dui_cliente = persona.dui
        id_credito = credito.credito_id

        # CORRECCIÓN: Se agrega la 'f' al inicio de las comillas triples para procesar las variables
        cuerpo = f"""
        {nombre_firmante_limpio}, mayor de edad, Abogado y Notario, de este domicilio, 
        con Documento Único de Identidad número {dui_firmante}, en calidad de {cargo_firmante} 
        de <b>LENDER FINANZAS</b>, hace constar que {tratamiento} <b>{nombre_cliente}</b>, 
        identificado con su Documento Único de Identidad número <b>{dui_cliente}</b> ha cancelado el crédito 
        registrado bajo el código <b>{id_credito}</b>.
        """
        
        elements.append(Paragraph(cuerpo, legal_style))
        elements.append(Spacer(1, 15))

        # Pie de fecha
        hoy = datetime.datetime.now()
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        pie_fecha = f"""
        Por tal razón se extiende el presente <b>FINIQUITO</b>, en el distrito de San Salvador, Municipio de San Salvador Centro, 
        Departamento de San Salvador, a los {hoy.day} días del mes de {meses[hoy.month-1]} del año {hoy.year}.
        """
        
        elements.append(Paragraph(pie_fecha, legal_style))
        
        # Espacio antes de la firma
        elements.append(Spacer(1, 45))
        
        if os.path.exists(ruta_firma):
            img_firma = Image(ruta_firma, width=2.2*inch, height=0.8*inch)
            logger.info("Firma cargada correctamente en el PDF.")
        else:
            img_firma = Image(ruta_firma, width=1.6*inch, height=0.8*inch)
            logger.warning(f"ADVERTENCIA: No se encontró la firma en {ruta_firma}")

        # Tabla de firma estructurada
        firma_info = [
            [img_firma],                                     # Imagen de la firma
            ["________________________"],                    # Línea
            [f"{nombre_firmante_limpio}"],                    # Nombre
            [f"{cargo_firmante} | LENDER FINANZAS"]          # Cargo (Variable limpia utilizada aquí también)
        ]
        
        t_firma = Table(firma_info, colWidths=[350])
        t_firma.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 2), (0, 2), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (0, 0), -12), # Acerca la imagen a la línea
            ('TOPPADDING', (0, 1), (0, 1), 0),      # Elimina espacio superior de la línea
            ('BOTTOMPADDING', (0, 1), (0, 1), 2),   # Espacio pequeño entre línea y nombre
        ]))
        elements.append(t_firma)

        # Construcción del PDF
        doc.build(elements)
        
        # Gestión de archivos y subida
        nombre_archivo = f"finiquito_{id_credito}_{hoy.strftime('%Y%m%d%H%M%S')}.pdf"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        
        with open(ruta_archivo, 'wb') as f:
            f.write(buffer.getvalue())
        
        url_publica = self._subir_a_gcs(ruta_archivo, nombre_archivo, "finiquitos")
        
        return ruta_archivo, nombre_archivo, url_publica
    

class GeneradorEstadosCuenta(GeneradorDocumentos):
    """Especializada en generar estados de cuenta detallados para Lender Finanzas."""
    
    def generar_estado_cuenta_pdf(self, persona, credito, pagos, resumen_vistas=None):
            config = self.obtener_configuracion_sucursal(credito.privado)

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
            styles = getSampleStyleSheet()
            
            # Estilo para el pie de página
            if 'PiePagina' not in styles:
                styles.add(ParagraphStyle(
                    name='PiePagina',
                    fontSize=8,
                    leading=10,
                    alignment=1, 
                    textColor=colors.grey,
                    fontName='Helvetica-Oblique'
                ))
            
            elements = []

            # 1. Logo y Título
            if os.path.exists(config["logo"]):
                logo = Image(config["logo"], width=config["ancho"]*inch, height=1*inch)
                elements.append(logo)
            
            elements.append(Paragraph("<b>ESTADO DE CUENTA DETALLADO</b>", styles['Title']))
            elements.append(Spacer(1, 10))

            # 2. Encabezado de Datos
            comisiones_totales = float(getattr(credito, 'comision_asistencia_financiera', 0) + 
                                    getattr(credito, 'comision_administrative', 0))
            
            info_data = [
                [f"ID PERSONA: {persona.persona_id}", f"ID CRÉDITO: {credito.credito_id}"],
                [f"CLIENTE: {persona.nombres} {persona.apellidos}", f"DUI: {persona.dui}"],
                [f"FECHA DEL CRÉDITO: {credito.fecha.strftime('%d/%m/%Y') if credito.fecha else '-'}", f"MONTO PROYECTADO: ${credito.total_credito_proyectado:,.2f}"],
                [f"MONTO OTORGADO: ${credito.monto_colocado:,.2f}", f"CUOTA: ${credito.cuota:,.2f}"],
                [f"NÚMERO DE CUOTAS: {credito.numero_cuotas}", f"DÍA DE PAGO: {credito.dia_pago}"],
                [f"MONTO COMISIONES: ${comisiones_totales:,.2f}", ""]
            ]
            
            t_info = Table(info_data, colWidths=[3.5*inch, 3.5*inch])
            t_info.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), 'Helvetica'), 
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ('FONTNAME', (0,0), (1,0), 'Helvetica-Bold'),
            ]))
            elements.append(t_info)
            elements.append(Spacer(1, 20))
            
            # 3. Tabla de Movimientos
            tabla_data = [["FECHA", "DESCRIPCIÓN", "MONTO", "EXTEMPORÁNEO"]]
            
            total_abonado_acumulado = 0 # Solo capital/monto
            for p in pagos:
                monto_pago = float(p.monto)
                valor_extemporaneo = float(getattr(p, 'multa', 0) + getattr(p, 'intereses', 0))
                
                # Solo acumulamos el monto del abono (sin extemporáneo)
                total_abonado_acumulado += monto_pago
                
                tabla_data.append([
                    p.fecha.strftime("%d/%m/%Y") if p.fecha else "-",
                    f"PAGO RECIBO #{p.pago_id}",
                    f"${monto_pago:,.2f}",
                    f"${valor_extemporaneo:,.2f}"
                ])

            t_movs = Table(tabla_data, colWidths=[1.0*inch, 3.0*inch, 1.5*inch, 1.5*inch])
            t_movs.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(t_movs)

            # 4. Resumen Final (Matemática interna existente)
            elements.append(Spacer(1, 15))
            monto_proyectado = float(credito.total_credito_proyectado)
            saldo_pendiente = max(monto_proyectado - total_abonado_acumulado, 0)
            
            resumen_data = [
                ["", "TOTAL ABONADO:", f"${total_abonado_acumulado:,.2f}"],
                ["", "SALDO PENDIENTE:", f"${saldo_pendiente:,.2f}"]
            ]
            
            # --- INTEGRACIÓN NUEVA: Agregar datos de la vista al final del resumen ---
            if resumen_vistas:
                m_pendientes = resumen_vistas.get("meses_pendientes", 0)
                n_mora = resumen_vistas.get("nivel_mora", "Al día")
                s_total_vista = resumen_vistas.get("saldo_total", 0.0)
                
                resumen_data.append(["", "MESES PENDIENTES:", f"{m_pendientes} mes(es)"])
                resumen_data.append(["", "NIVEL DE MORA:", f"{n_mora}"])
            # ------------------------------------------------------------------------

            t_resumen = Table(resumen_data, colWidths=[4.0*inch, 1.5*inch, 1.5*inch])
            t_resumen.setStyle(TableStyle([
                ('ALIGN', (1, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (1, 0), (2, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (1, 0), (2, -1), 9),
                # Le damos un color sutil a las filas nuevas para que se diferencien de la matemática base
                ('TEXTCOLOR', (1, 2), (2, -1), colors.HexColor('#2C3E50')) if resumen_vistas else ('TEXTCOLOR', (1, 0), (2, -1), colors.black),
            ]))
            elements.append(t_resumen)

            # 5. Pie de Página (Línea + Fecha de Emisión)
            elements.append(Spacer(1, 40)) 
            elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey, spaceBefore=10, spaceAfter=5))
            
            fecha_emision = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            pie_texto = f"Este documento es un estado de cuenta informativo emitido el {fecha_emision}"
            elements.append(Paragraph(pie_texto, styles['PiePagina']))

            # 6. Construcción y Guardado
            doc.build(elements)
            nombre_archivo = f"estado_cuenta_{credito.credito_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M')}.pdf"
            ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
            
            with open(ruta_archivo, 'wb') as f:
                f.write(buffer.getvalue())
            
            url_publica = self._subir_a_gcs(ruta_archivo, nombre_archivo, "estados_cuenta")
            return ruta_archivo, nombre_archivo, url_publica
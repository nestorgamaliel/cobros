# -*- coding: utf-8 -*-
import os
import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from num2words import num2words # Recuerda agregar num2words a tu requirements.txt

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


class GeneradorRecibos(GeneradorDocumentos):
    """Especializada en generar recibos de pago."""
    
    def generar_recibo_pdf(self, pago, credito, persona, datos_adicionales=None):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()
        
        right_style = ParagraphStyle('RightStyle', parent=styles['Normal'], alignment=TA_RIGHT)
        elements = []
        
        # Logo
        if os.path.exists(self.logo_path):
            logo = Image(self.logo_path, width=2.5*inch, height=1*inch)
            elements.append(logo)
        
        elements.append(Paragraph(f"<b>RECIBO DE PAGO #{pago.pago_id}</b>", styles['Title']))
        elements.append(Spacer(1, 20))
        
        # Fecha emisión
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y")
        elements.append(Paragraph(f"<b>Fecha de emisión:</b> {fecha_actual}", right_style))
        elements.append(Spacer(1, 20))
        
        # Tabla Persona
        persona_info = [["INFORMACIÓN DEL CLIENTE"], [f"Nombre: {persona.nombres} {persona.apellidos}"], [f"DUI: {persona.dui}"], [f"Teléfono: {persona.telefono}"]]
        t_persona = Table(persona_info, colWidths=[450])
        t_persona.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('ALIGN', (0, 0), (-1, 0), 'CENTER'), ('BOX', (0, 0), (-1, -1), 1, colors.black)]))
        elements.append(t_persona)
        elements.append(Spacer(1, 20))
        
        # Tabla Crédito
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
        
        # Detalle de Pago
        saldo = datos_adicionales.get('saldo', 0) if datos_adicionales else 0
        pago_info = [["DETALLE DEL PAGO ACTUAL"], [f"Fecha de pago: {pago.fecha.strftime('%d/%m/%Y')}", f"Monto pagado: ${pago.monto:,.2f}"]]
        if pago.intereses: pago_info.append(["", f"Intereses: ${pago.intereses:,.2f}"])
        if pago.multa: pago_info.append(["", f"Mora/Multa: ${pago.multa:,.2f}"])
        pago_info.append(["", f"Saldo pendiente: ${saldo:,.2f}"])
        
        t_pago = Table(pago_info, colWidths=[225, 225])
        t_pago.setStyle(TableStyle([('BACKGROUND', (0, 0), (1, 0), colors.lightgrey), ('SPAN', (0, 0), (1, 0)), ('ALIGN', (0, 0), (1, 0), 'CENTER'), ('GRID', (0, 1), (1, -1), 1, colors.black)]))
        elements.append(t_pago)
        elements.append(Spacer(1, 40))
        
        # Firma
        elements.append(Table([["________________________"], ["Evelyn García | Gerente Operaciones"]], colWidths=[450], style=[('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        
        # Generación de archivo
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
        if datos_firmante is None:
            datos_firmante = {
                "nombre": "EVELYN YANETH GARCIA BAIRES",
                "cargo": "Gerente Legal",
                "dui": "02248960-2"
            }

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
        
        # AJUSTE 1: Alineación Justificada (alignment=4) para ambos lados
        legal_style = ParagraphStyle(
            'LegalBody', 
            parent=styles['Normal'], 
            fontSize=11, 
            leading=16, 
            alignment=4  
        )
        
        elements = []

        # Logo de cabecera
        if os.path.exists(self.logo_path):
            logo = Image(self.logo_path, width=2.5*inch, height=0.8*inch)
            elements.append(logo)
            elements.append(Spacer(1, 30))

        elements.append(Paragraph("<b>A QUIEN INTERESE:</b>", styles['Normal']))
        elements.append(Spacer(1, 20))

        # AJUSTE 3: Lógica basada en el campo 'sexo' (F/M)
        # Se determina si es "la señora" o "el señor" dinámicamente
        genero_val = getattr(persona, 'sexo', 'M').upper()
        tratamiento = "la señora" if genero_val == 'F' else "el señor"

        # AJUSTE 2 & 4: Negritas en DUI/Código y limpieza de nombres
        monto_letras = self._monto_a_letras(credito.total_credito_proyectado)
        
        # Limpiamos posibles etiquetas HTML que vengan en el string del nombre
        nombre_firmante_limpio = datos_firmante['nombre'].replace("<b>", "").replace("</b>", "")

        cuerpo = f"""
        {nombre_firmante_limpio}, mayor de edad, Abogado y Notario, de este domicilio, 
        con Documento Único de Identidad número {datos_firmante['dui']}, en calidad de {datos_firmante['cargo']} 
        de <b>LENDER FINANZAS</b>, hace constar que {tratamiento} <b>{persona.nombres} {persona.apellidos}</b>, 
        identificado con su Documento Único de Identidad número <b>{persona.dui}</b>, ha cancelado la cantidad de 
        <b>{monto_letras} (${credito.total_credito_proyectado:,.2f})</b>, correspondiente al crédito registrado 
        bajo el código <b>{credito.credito_id}</b>.
        """
        
        elements.append(Paragraph(cuerpo, legal_style))
        elements.append(Spacer(1, 15))

        # Fecha de emisión legal
        hoy = datetime.datetime.now()
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        pie_fecha = f"""
        Por tal razón se extiende el presente <b>FINIQUITO</b>, en el distrito de San Salvador, Municipio de San Salvador Centro, 
        Departamento de San Salvador, a los {hoy.day} días del mes de {meses[hoy.month-1]} del año {hoy.year}.
        """
        
        elements.append(Paragraph(pie_fecha, legal_style))
        
        # Sección de firmas centrada
        elements.append(Spacer(1, 80))
        
        # AJUSTE 4: Firma limpia sin etiquetas de texto visibles
        firma_info = [
            ["________________________"],
            [f"<b>{nombre_firmante_limpio}</b>"],
            [f"{datos_firmante['cargo']} | LENDER FINANZAS"]
        ]
        
        t_firma = Table(firma_info, colWidths=[350])
        t_firma.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold')
        ]))
        elements.append(t_firma)

        doc.build(elements)
        
        # Generación de archivo y subida
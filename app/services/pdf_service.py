import os
import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from app.utils.logger import setup_logger
from app.utils.gcs_uploader import subir_archivo_a_gcs
import config
# Configurar logger
logger = setup_logger(__name__)


class GeneradorRecibos:
    """Servicio para generar recibos en formato PDF."""
    
    def __init__(self, directorio_salida=None, logo_path=None):
        """
        Inicializa el generador de recibos.
        
        Args:
            directorio_salida (str, opcional): Directorio donde se guardarán
                los recibos.
                Por defecto, usa el directorio configurado en config.py.
            logo_path (str, opcional): Ruta del archivo del logo.
                Por defecto, usa el logo configurado en config.py.
        """
        if directorio_salida is None:
            directorio_salida = config.RECIBOS_DIR
            
        self.directorio_salida = directorio_salida
        if not os.path.exists(directorio_salida):
            os.makedirs(directorio_salida)
        
        # Configurar ruta del logo
        self.logo_path = logo_path if logo_path else config.LOGO_PATH
            
        logger.info(f"Servicio de generacion de recibos inicializado \
                    (directorio: {directorio_salida})")
    
    def generar_recibo_pdf(self, pago, credito, persona,
                           datos_adicionales=None):
        """
        Genera un recibo de pago en formato PDF.
        
        Args:
            pago (Pago): Objeto Pago con la informacion del pago.
            credito (Credito): Objeto Credito asociado al pago.
            persona (Persona): Objeto Persona asociado al crédito.
            datos_adicionales (dict, opcional): Diccionario con datos 
            adicionales del estado del crédito.
                Ej: {'ultima_fecha_pago': datetime, 'saldo': float, 'dia_pago'
                : int, 'cuota': float}
            
        Returns:
            tuple: (ruta_archivo, nombre_archivo) con las rutas del archivo 
            generado.
        """
        # Crear un buffer para el PDF
        buffer = BytesIO()
        
        # Crear el documento PDF
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Obtener estilos
        styles = getSampleStyleSheet()
        
        # Crear estilo para centrar
        center_style = ParagraphStyle(
            'CenteredStyle',
            parent=styles['Normal'],
            alignment=TA_CENTER
        )
        
        # Crear estilo para alinear a la derecha
        right_style = ParagraphStyle(
            'RightStyle',
            parent=styles['Normal'],
            alignment=TA_RIGHT
        )
        
        # Lista para almacenar los elementos del PDF
        elements = []
        
        # Agregar logo si existe
        if os.path.exists(self.logo_path):
            logo = Image(self.logo_path)
            logo.drawHeight = 1*inch
            logo.drawWidth = 2.5*inch
            elements.append(logo)
        
        # Título del recibo
        titulo = Paragraph(f"<b>RECIBO DE PAGO #{pago.pago_id}\
            </b>", styles['Title'])
        elements.append(titulo)
        elements.append(Spacer(1, 20))
        
        # Fecha del recibo
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y")
        fecha_texto = Paragraph(f"<b>Fecha de emisión:</b> {fecha_actual}", 
                                right_style)
        elements.append(fecha_texto)
        elements.append(Spacer(1, 20))
        
        # Información del cliente
        persona_info = [
            ["INFORMACIÓN DEL CLIENTE"],
            [f"Nombre: {persona.nombres} {persona.apellidos}"],
            [f"Dirección: {persona.direccion}"],
            [f"Teléfono: {persona.telefono}"]
        ]
        
        t_persona = Table(persona_info, colWidths=[450])
        t_persona.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(t_persona)
        elements.append(Spacer(1, 20))
        
        # Información del crédito
        fecha_credito = getattr(credito, 'fecha', datetime.datetime.now()).strftime('%d/%m/%Y')
        
        # Obtener datos adicionales del crédito si están disponibles
        dia_pago = credito.dia_pago
        cuota = credito.cuota 
        
        credito_info = [
            ["INFORMACIÓN DEL CRÉDITO"],
            [f"Crédito ID: {credito.credito_id}", f"Fecha de inicio: \
                            {fecha_credito}"],
            [f"Monto total: ${credito.total_credito_proyectado:,.2f}", f"Día \
                de pago: {dia_pago}"],
            [f"Cuota mensual: ${cuota:,.2f}", ""]
        ]
        
        t_credito = Table(credito_info, colWidths=[225, 225])
        t_credito.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('SPAN', (0, 0), (1, 0)),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (1, -1), colors.white),
            ('BOX', (0, 0), (1, -1), 1, colors.black),
            ('GRID', (0, 1), (1, -1), 1, colors.black),
        ]))
        
        elements.append(t_credito)
        elements.append(Spacer(1, 20))
        
        # Información del pago actual
        fecha_formateada = pago.fecha.strftime('%d/%m/%Y')
        
        # Obtener información del estado actual
        ultima_fecha_pago = 'N/A'
        saldo = 0
        
        if datos_adicionales:
            if datos_adicionales.get('ultima_fecha_pago'):
                ultima_fecha_pago = \
                    datos_adicionales['ultima_fecha_pago'].strftime('%d/%m/%Y')
            saldo = datos_adicionales.get('saldo', 0)
            
        logger.info(pago)
        pago_info = [
            ["DETALLE DEL PAGO ACTUAL"],
            [f"Fecha de pago: {fecha_formateada}", f"Monto pagado: ${pago.monto:,.2f}"],
        ]
        # Agregar fila de multa, si aplica
        if pago.multa:
            pago_info.append(["", f"Pago extemporaneo: ${pago.multa:,.2f}"])

        # Continuar con el resto de la información
        pago_info.append([f"Última fecha de pago: {ultima_fecha_pago}", f"Saldo pendiente: ${saldo:,.2f}"])


        
        t_pago = Table(pago_info, colWidths=[225, 225])
        t_pago.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('SPAN', (0, 0), (1, 0)),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (1, -1), colors.white),
            ('BOX', (0, 0), (1, -1), 1, colors.black),
            ('GRID', (0, 1), (1, -1), 1, colors.black),
        ]))
        
        elements.append(t_pago)
        elements.append(Spacer(1, 40))
        
        # Sección para firmas
        elementos_firma = [
            ["________________________"],
            ["Evelyn García | Gerente Operaciones"],
        ]
        
        t_firmas = Table(elementos_firma, colWidths=[225, 225])
        t_firmas.setStyle(TableStyle([
            ('ALIGN', (0, 0), (1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 1), (1, 1), 'Helvetica'),
            ('FONTNAME', (0, 3), (0, 4), 'Helvetica'),
            ('TOPPADDING', (0, 0), (1, 0), 40),  # Espacio para firmar
        ]))
        
        elements.append(t_firmas)
        elements.append(Spacer(1, 40))
        
        # Pie de página
        fecha_hora_actual = \
            datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        pie = Paragraph(f"<i>Este recibo fue generado el \
            {fecha_hora_actual}</i>", styles['Normal'])
        elements.append(pie)
        
        # Construir el PDF
        doc.build(elements)
        
        # Guardar el PDF en un archivo
        nombre_archivo = f"recibo_pago_{pago.pago_id}\
            _{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        
        with open(ruta_archivo, 'wb') as f:
            f.write(buffer.getvalue())
        
        buffer.close()
        logger.info(f"Recibo generado correctamente: {ruta_archivo}")
        logger.info("Subiendo recibo a Google Cloud Storage...")
        
        # Dentro de tu método generar_recibo_pdf, justo antes del return:
        bucket_name = config.GCS_BUCKET_NAME  # define esto en config.py
        destino = f"recibos/{nombre_archivo}"
        url_publica = subir_archivo_a_gcs(ruta_archivo, destino, bucket_name)

        logger.info(f"PDF subido correctamente: {url_publica}")
        return ruta_archivo, nombre_archivo, url_publica

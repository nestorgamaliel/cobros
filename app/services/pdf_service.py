import os
import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from app.utils.logger import setup_logger
import config

# Configurar logger
logger = setup_logger(__name__)


class GeneradorRecibos:
    """Servicio para generar recibos en formato PDF."""
    
    def __init__(self, directorio_salida=None):
        """
        Inicializa el generador de recibos.
        
        Args:
            directorio_salida (str, opcional): Directorio donde se guardarán los recibos.
                Por defecto, usa el directorio configurado en config.py.
        """
        if directorio_salida is None:
            directorio_salida = config.RECIBOS_DIR
            
        self.directorio_salida = directorio_salida
        if not os.path.exists(directorio_salida):
            os.makedirs(directorio_salida)
            
        logger.info(f"Servicio de generacion de recibos inicializado \
            (directorio: {directorio_salida})")
    
    def generar_recibo_pdf(self, pago, credito, persona):
        """
        Genera un recibo de pago en formato PDF.
        
        Args:
            pago (Pago): Objeto Pago con la informacion del pago.
            credito (Credito): Objeto Credito asociado al pago.
            persona (Persona): Objeto Persona asociado al crédito.
            
        Returns:
            tuple: (ruta_archivo, nombre_archivo) con las rutas del archivo \
                generado.
        """
        # Crear un buffer para el PDF
        buffer = BytesIO()
        
        # Crear el documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Título del recibo
        titulo = Paragraph(f"<b>RECIBO DE PAGO #{pago.pago_id}</b>", styles['Title'])
        elements.append(titulo)
        elements.append(Spacer(1, 20))
        
        # Informacion del persona
        persona_info = [
            ["INFORMACIoN DEL CLIENTE"],
            [f"Nombre: {persona.nombres} {persona.apellidos}"],
            [f"Direccion: {persona.direccion}"],
            [f"Teléfono: {persona.telefono}"]
        ]
        
        t_persona = Table(persona_info, colWidths=[400])
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
        
        # Informacion del pago
        fecha_formateada = pago.fecha.strftime('%d/%m/%Y')
        pago_info = [
            ["DETALLE DEL PAGO"],
            [f"Fecha: {fecha_formateada}", f"Monto: ${pago.monto:.2f}"],
            [f"Crédito ID: {credito.credito_id}", f"Monto total del crédito: \
                ${credito.total_credito_proyectado:,.2f}"]
        ]
        
        logger.info(pago_info)
        
        t_pago = Table(pago_info, colWidths=[200, 200])
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
        
        # Pie de página
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        pie = Paragraph(f"<i>Este recibo fue generado el {fecha_actual}</i>",
                        styles['Normal'])
        elements.append(pie)
        
        # Construir el PDF
        doc.build(elements)
        
        # Guardar el PDF en un archivo
        nombre_archivo = f"recibo_pago_{pago.pago_id}_{
            datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        ruta_archivo = os.path.join(self.directorio_salida, nombre_archivo)
        
        with open(ruta_archivo, 'wb') as f:
            f.write(buffer.getvalue())
        
        buffer.close()
        logger.info(f"Recibo generado correctamente: {ruta_archivo}")
        
        return ruta_archivo, nombre_archivo
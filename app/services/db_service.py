# -*- coding: utf-8 -*-
import datetime
import calendar
from datetime import date, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import Base, Persona, Credito, Pago, Vendedor
from app.utils.logger import setup_logger

# Configurar logger
logger = setup_logger(__name__)


class BaseDatos:
    """Servicio para interactuar con la base de datos."""
    
    def __init__(self, db_url):
        """
        Inicializa la conexion a la base de datos.
        
        Args:
            db_url (str): URL de conexion a la base de datos.
        """
        logger.info(db_url)
        self.engine = create_engine(db_url, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.session = self.Session()
        logger.info("Servicio de base de datos inicializado")        
        
        
    def crear_tablas(self):
        """Crea las tablas en la base de datos si no existen."""
        Base.metadata.create_all(self.engine)
        logger.info("Tablas creadas correctamente")
        
    def comprobar_conexion(self):
        """
        Comprueba si la conexion a la base de datos está activa.
        
        Returns:
            bool: True si la conexion está activa, False en caso contrario.
        """
        try:
            # Ejecuta una consulta sencilla para verificar la conexion
            self.session.execute(text('SELECT 1'))
            logger.info("Conexion a la base de datos establecida \
                correctamente")
            return True
        except Exception as e:
            logger.error(f"Error al conectar con la base de datos: {str(e)}")
            return False
        
    def insertar_pago(self, credito_id, fecha, monto, multa, intereses):
        """
        Inserta un nuevo pago en la base de datos.
        
        Args:
            credito_id (int): ID del crédito al que corresponde el pago.
            fecha (str/date): Fecha del pago.
            monto (float): Monto del pago.
            multa (float): Pago adicional por extemporalidad.
            intereses (float): Monto de intereses, cuando no paga a "capital"
            
        Returns:
            Pago: Objeto Pago insertado.
        """
        try:
            # Convertir la fecha si viene como string
            if isinstance(fecha, str):
                fecha = datetime.datetime.strptime(fecha, '%Y-%m-%d').date()
                
            nuevo_pago = Pago(credito_id=credito_id, fecha=fecha, monto=monto,
                              multa=multa, intereses=intereses)
            self.session.add(nuevo_pago)
            self.session.commit()
            logger.info(f"Pago insertado correctamente con ID:\
                {nuevo_pago.pago_id}")
            return nuevo_pago
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al insertar pago: {str(e)}")
            raise
    
    def obtener_pago(self, pago_id):
        """
        Obtiene un pago por su ID.
        
        Args:
            pago_id (int): ID del pago a obtener.
            
        Returns:
            Pago: Objeto Pago encontrado o None si no existe.
        """
        return self.session.query(Pago).filter_by(pago_id=pago_id).first()
    
    def obtener_credito(self, credito_id):
        """
        Obtiene un crédito por su ID.
        
        Args:
            credito_id (int): ID del crédito a obtener.
            
        Returns:
            Credito: Objeto Credito encontrado o None si no existe.
        """
        return self.session.query(Credito).filter_by(credito_id=credito_id).first()
    
    def obtener_persona(self, persona_id):
        """
        Obtiene un persona por su ID.
        
        Args:
            persona_id (int): ID del persona a obtener.
            
        Returns:
            persona: Objeto Persona encontrado o None si no existe.
        """
        return self.session.query(Persona).filter_by(persona_id=persona_id).first()        

    def obtener_vendedor(self, vendedor_id):
        """
        Obtiene un vendedor por su ID.
        
        Args:
            vendedor_id (int): ID del vendedor a obtener.
            
        Returns:
            vendedor: Objeto Vendedor encontrado o None si no existe.
        """
        return self.session.query(Vendedor).filter_by(vendedor_id=vendedor_id).first()        



    def obtener_datos_credito(self, credito_id):
        """
        Obtiene los datos completos del crédito incluyendo 
        información de pagos y saldos.
        
        Args:
            credito_id (int): ID del crédito.
            
        Returns:
            dict: Diccionario con la información del crédito.
        """
        # SQL query directa para obtener todos los datos necesarios
        # en una sola consulta
        sql = text("""
            SELECT a.credito_id,
                   b.nombres || ' ' || b.apellidos AS cliente,
                   a.fecha AS fecha_credito,
                   a.total_credito_proyectado,
                   a.dia_pago,
                   a.cuota,
                   c.ultima_fecha_pago,
                   a.vendedor_id,
                   (a.total_credito_proyectado - COALESCE(c.pagado, 0)) AS saldo
            FROM credito a
            LEFT JOIN persona b ON (a.persona_id = b.persona_id)
            LEFT JOIN (
                SELECT credito_id,
                       SUM(monto) AS pagado,
                       MAX(fecha) AS ultima_fecha_pago
                FROM pago
                GROUP BY credito_id
            ) c ON (a.credito_id = c.credito_id)
            WHERE a.credito_id = :credito_id
        """)
        
        try:
            result = self.session.execute(sql, {"credito_id": credito_id}).fetchone()
            
            if not result:
                raise ValueError(f"No se encontró información para el crédito ID {credito_id}")
            
            # Convertir el resultado a diccionario
            datos = {
                'credito_id': result.credito_id,
                'cliente': result.cliente,
                'fecha_credito': result.fecha_credito,
                'total_credito_proyectado': result.total_credito_proyectado,
                'dia_pago': result.dia_pago,
                'cuota': result.cuota,
                'ultima_fecha_pago': result.ultima_fecha_pago,
                'vendedor_id': result.vendedor_id,
                'saldo': result.saldo if result.saldo is not None else result.total_credito_proyectado
            }
            
            logger.info(f"Datos del crédito {credito_id} obtenidos correctamente")
            return datos
            
        except Exception as e:
            logger.error(f"Error al obtener datos del crédito {credito_id}: {str(e)}")
            raise                
        
    def insertar_persona(self,
                         nombres,
                         apellidos,
                         fecha_nacimiento,
                         sexo,
                         telefono,
                         direccion,
                         dui):
        """
        Inserta una nueva persona en la base de datos.
        
        Args:
            nombres,
            apellidos,
            fecha_nacimiento,
            sexo,
            telefono,
            direccion):

        Returns:
            Pago: Objeto Pago insertado.
        """
        try:
            # Convertir la fecha si viene como string
            if isinstance(fecha_nacimiento, str):
                fecha_nacimiento = datetime.datetime.strptime(fecha_nacimiento,
                                                              '%Y-%m-%d').date()
                
            nueva_persona = Persona(nombres=nombres,
                                    apellidos=apellidos,
                                    fecha_nacimiento=fecha_nacimiento,
                                    sexo=sexo,
                                    telefono=telefono,
                                    direccion=direccion,
                                    dui=dui)
            self.session.add(nueva_persona)
            self.session.commit()    
            logger.info(f"Persona insertada correctamente con ID:\
                {nueva_persona.persona_id}")
            return nueva_persona
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al insertar persona: {str(e)}")
            raise
        
    def insertar_vendedor(self,
                         vendedor_id,
                         nombre_vendedor):
        """
        Inserta un nuevo vendedor en la base de datos.
        
        Args:
            vendedor_id
            nombre_vendedor):

        Returns:
            Vendedor: Objeto Vendedor insertado.
        """
        try:
            nuevo_vendedor = Vendedor(vendedor_id=vendedor_id,
                                    nombre_vendedor=nombre_vendedor)
            self.session.add(nuevo_vendedor)
            self.session.commit()    
            logger.info(f"Vendedor insertado correctamente con ID:\
                {nuevo_vendedor.vendedor_id}")
            return nuevo_vendedor
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al insertar vendedor: {str(e)}")
            raise


    def insertar_credito(self,
                         persona_id,
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
                         observaciones,
                         vendedor_id):
        """
        Inserta un nuevo credito en la base de datos.
        
        Args:

        Returns:
            Credito: Objeto Credito insertado.
        """
        try:
            # Convertir la fecha si viene como string
            if isinstance(fecha, str):
                fecha = datetime.datetime.strptime(fecha,
                                                   '%Y-%m-%d').date()
                
            nuevo_credito = Credito(
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
                                    observaciones=observaciones,
                                    vendedor_id=vendedor_id                                    
                                    )
            self.session.add(nuevo_credito)
            self.session.commit()    
            logger.info(f"Credito insertado correctamente con ID:\
                {nuevo_credito.credito_id}")
            return nuevo_credito
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al insertar credito: {str(e)}")
            raise
        
        
    def cerrar(self):
        """Cierra la sesion de la base de datos."""
        self.session.close()
        logger.info("Sesion de base de datos cerrada")
        

    def buscar_personas(self, filtros, limite=10, pagina=1):
            """
            Busca personas en la base de datos según los filtros.
            
            Args:
                filtros (dict): Filtros de búsqueda
                limite (int): Límite de resultados
                pagina (int): Número de página
                
            Returns:
                list: Lista de objetos Persona
            """
            try:
                from app.models.models import Persona
                from sqlalchemy import and_
                
                # Construir query base usando self.session
                query = self.session.query(Persona)
                
                # Aplicar filtros
                filtros_aplicados = []
                
                # Búsqueda exacta por DUI
                if filtros.get('dui'):
                    filtros_aplicados.append(Persona.dui == filtros['dui'])
                
                # Búsqueda parcial por nombres (case-insensitive)
                if filtros.get('nombres'):
                    filtros_aplicados.append(
                        Persona.nombres.ilike(f"%{filtros['nombres']}%")
                    )
                
                # Búsqueda parcial por apellidos (case-insensitive)
                if filtros.get('apellidos'):
                    filtros_aplicados.append(
                        Persona.apellidos.ilike(f"%{filtros['apellidos']}%")
                    )
                
                # Aplicar todos los filtros
                if filtros_aplicados:
                    query = query.filter(and_(*filtros_aplicados))
                
                # Ordenar resultados
                query = query.order_by(Persona.nombres, Persona.apellidos)
                
                # Aplicar paginación
                offset = (pagina - 1) * limite
                personas = query.offset(offset).limit(limite).all()
                
                return personas
                
            except Exception as e:
                logger.error(f"Error en búsqueda de personas: {str(e)}")
                raise

    def contar_personas_filtradas(self, filtros):
        """
        Cuenta el total de personas que coinciden con los filtros.
        
        Args:
            filtros (dict): Filtros de búsqueda
            
        Returns:
            int: Número total de personas que coinciden
        """
        try:
            from app.models.models import Persona
            from sqlalchemy import and_
            
            # Construir query base usando self.session
            query = self.session.query(Persona)
            
            # Aplicar los mismos filtros que en buscar_personas
            filtros_aplicados = []
            
            if filtros.get('dui'):
                filtros_aplicados.append(Persona.dui == filtros['dui'])
            
            if filtros.get('nombres'):
                filtros_aplicados.append(
                    Persona.nombres.ilike(f"%{filtros['nombres']}%")
                )
            
            if filtros.get('apellidos'):
                filtros_aplicados.append(
                    Persona.apellidos.ilike(f"%{filtros['apellidos']}%")
                )
            
            # Aplicar filtros y contar
            if filtros_aplicados:
                query = query.filter(and_(*filtros_aplicados))
            
            total = query.count()
            return total
            
        except Exception as e:
            logger.error(f"Error al contar personas: {str(e)}")
            raise


def obtener_cobros_dia(self, dias_lista):
        """
        Ejecuta el query de fin de mes para Chalchuapa filtrando por días específicos.
        
        Args:
            dias_lista (tuple): Ejemplo (13, 14)
            
        Returns:
            list: Lista de diccionarios con la información de cobranza.
        """
        # Tu query SQL optimizado con parámetros :dias
        sql = text("""
            SELECT DISTINCT 
               a.nombres || ' ' || a.apellidos AS cliente, 
               a.cuota, 
               a.dia_pago, 
               a.nombre_vendedor AS vendedor, 
               b.observacion 
            FROM saldos_totales a
               LEFT JOIN credito_gestion b ON (a.credito_id = b.credito_id)
            WHERE ((a.dia_pago IN :dias) OR (EXTRACT(DAY FROM b.fecha_promesa) IN :dias))
            AND a.privado = 2
            ORDER BY a.dia_pago DESC
        """)
        
        try:
            # Ejecutamos pasando la tupla de días
            result = self.session.execute(sql, {"dias": dias_lista}).fetchall()
            
            # Convertimos cada fila en un diccionario para que sea fácil de leer en el servicio
            cobros = []
            for row in result:
                cobros.append({
                    'cliente': row.cliente,
                    'cuota': row.cuota,
                    'dia_pago': row.dia_pago,
                    'vendedor': row.vendedor,
                    'observacion': row.observacion if row.observacion else "Sin obs."
                })
            
            logger.info(f"Se obtuvieron {len(cobros)} registros para el reporte de WhatsApp")
            return cobros
            
        except Exception as e:
            logger.error(f"Error al obtener cobranza de Chalchuapa: {str(e)}")
            return []
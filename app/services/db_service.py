# -*- coding: utf-8 -*-
import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import Base, Persona, Credito, Pago
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
        
    def insertar_pago(self, credito_id, fecha, monto, multa):
        """
        Inserta un nuevo pago en la base de datos.
        
        Args:
            credito_id (int): ID del crédito al que corresponde el pago.
            fecha (str/date): Fecha del pago.
            monto (float): Monto del pago.
            multa (float): Pago adicional por extemporalidad.
            
        Returns:
            Pago: Objeto Pago insertado.
        """
        try:
            # Convertir la fecha si viene como string
            if isinstance(fecha, str):
                fecha = datetime.datetime.strptime(fecha, '%Y-%m-%d').date()
                
            nuevo_pago = Pago(credito_id=credito_id, fecha=fecha, monto=monto,
                              multa=multa)
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
                         direccion):
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
                                    direccion=direccion)
            self.session.add(nueva_persona)
            self.session.commit()    
            logger.info(f"Persona insertada correctamente con ID:\
                {nueva_persona.persona_id}")
            return nueva_persona
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al insertar persona: {str(e)}")
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
                         observaciones):
        """
        Inserta un nuevo credito en la base de datos.
        
        Args:

        Returns:
            Pago: Objeto Pago insertado.
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
                                    observaciones=observaciones                                    
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
        
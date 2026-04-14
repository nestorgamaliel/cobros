from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric, DateTime, Boolean, func
from sqlalchemy.orm import relationship, declarative_base
import datetime


Base = declarative_base()

class Persona(Base):
    __tablename__ = 'persona'
    
    # Subimos a Integer para soportar más de 32k personas
    persona_id = Column(Integer, primary_key=True)
    nombres = Column(String(100))
    apellidos = Column(String(100))
    direccion = Column(String(255))
    telefono = Column(String(20))
    fecha_nacimiento = Column(Date)
    sexo = Column(String(1)) # M/F
    dui = Column(String(20), unique=True) # Unique para evitar duplicados
    
    municipio_id = Column(Integer) 
    departamento_id = Column(Integer)
    
    # Auditoría
    fum = Column(DateTime, server_default=func.now(), onupdate=func.now())

    creditos = relationship("Credito", back_populates="persona")

class Credito(Base):
    __tablename__ = 'credito'
    
    credito_id = Column(Integer, primary_key=True)
    persona_id = Column(Integer, ForeignKey('persona.persona_id'))
    vendedor_id = Column(Integer, ForeignKey('vendedor.vendedor_id'))
    
    # Estandarizamos a Numeric(10, 2) para dinero
    total_credito_proyectado = Column(Numeric(10, 2))
    fecha = Column(Date)
    cancelado = Column(Boolean, default=False) # <-- Cambiado a Boolean
    dia_pago = Column(Integer, default=30)
    cuota = Column(Numeric(10, 2))
    tasa_interes = Column(Numeric(10, 2))
    monto_solicitado = Column(Numeric(10, 2))
    numero_cuotas = Column(Integer)
    comision_asistencia_financiera = Column(Numeric(10, 2), default=0.00)
    comision_administrativa = Column(Numeric(10, 2), default=0.00)
    monto_colocado = Column(Numeric(10, 2))
    monto_intereses = Column(Numeric(10, 2), default=0.00)
    
    privado = Column(Integer) # 0 o 1
    observaciones = Column(String(500)) 
    estado_juridico = Column(Integer)
    fum = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    pagos = relationship("Pago", back_populates="credito")
    persona = relationship("Persona", back_populates="creditos")

class Pago(Base):
    __tablename__ = 'pago'
    
    pago_id = Column(Integer, primary_key=True)
    # Llave compuesta o simple? Si pago_id es único en toda la tabla, quita primary_key=True de credito_id
    credito_id = Column(Integer, ForeignKey('credito.credito_id'), primary_key=True)
    fecha = Column(Date)
    monto = Column(Numeric(10, 2))
    multa = Column(Numeric(10, 2), default=0.00)
    intereses = Column(Numeric(10, 2), default=0.00)
    url_recibo = Column(String(255))
    monto_comision = Column(Numeric(10, 2), default=0.00)
    fum = Column(DateTime, server_default=func.now(), onupdate=func.now())

    credito = relationship("Credito", back_populates="pagos")

class Vendedor(Base):
    __tablename__ = 'vendedor'
    
    vendedor_id = Column(Integer, primary_key=True)
    nombre_vendedor = Column(String(100))
    fum = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Vendedor(vendedor_id={self.vendedor_id}, nombre_vendedor='{self.nombre_vendedor}')>"


class CreditoComision(Base):
    __tablename__ = 'credito_comision'
    
    credito_comision_id = Column(Integer, primary_key=True)
    credito_id = Column(Integer, ForeignKey('credito.credito_id'), nullable=False)
    porcentaje_comision = Column(Numeric(5, 2), nullable=False)
    monto_total_comision = Column(Numeric(10, 2), nullable=False)
    tipo_comision_id = Column(Integer, nullable=False, default=1)
    fum = Column(DateTime, server_default=func.now(), onupdate=func.now())   
    credito = relationship("Credito", backref="comision")


class Finiquito(Base):
    __tablename__ = 'credito_finiquito'
    
    credito_id = Column(Integer, ForeignKey('credito.credito_id'), nullable=False)
    finiquito_id = Column(Integer, primary_key=True)
    fecha_generacion = Column(DateTime, default=datetime.datetime.now)
    url_documento = Column(String(500), nullable=False)
    firmante = Column(String(200)) # Guardamos quién firmó en ese momento   
    monto_cancelado = Column(Numeric(10, 2), nullable=False)    
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Base para los modelos de SQLAlchemy
Base = declarative_base()


class Persona(Base):
    """Modelo para la tabla Persona"""
    __tablename__ = 'persona'
    
    persona_id = Column(Integer, primary_key=True)
    nombres = Column(String)
    apellidos = Column(String)
    direccion = Column(String)
    telefono = Column(String)
    fecha_nacimiento = Column(Date)
    sexo = Column(String)

    # Relacion con Credito
    creditos = relationship("Credito", back_populates="persona")
    
    def __repr__(self):
        return f"<Persona(persona_id={self.persona_id}, nombres='{self.nombres}',\
            apellidos='{self.apellidos}')>"


class Credito(Base):
    """Modelo para la tabla credito."""
    __tablename__ = 'credito'
    
    credito_id = Column(Integer, primary_key=True)
    persona_id = Column(Integer, ForeignKey('persona.persona_id'))
    total_credito_proyectado = Column(Float)
    fecha = Column(Date)
    cancelado = Column(String)
    dia_pago = Column(Integer)
    cuota = Column(Float)
    tasa_interes = Column(Float)
    monto_solicitado = Column(Float)
    numero_cuotas = Column(Integer)
    comision_asistencia_financiera = Column(Float) 
    comision_administrativa = Column(Float)
    monto_colocado = Column(Float)
    monto_intereses = Column(Float)
    privado = Column(Integer) 
    observaciones = Column(Integer)    
    
    # Relaciones
    pagos = relationship("Pago", back_populates="credito")
    persona = relationship("Persona", back_populates="creditos")
    
    def __repr__(self):
        return f"<Credito(credito_id={self.credito_id},\
            persona_id={self.persona_id},\
            total_credito_proyectado={self.total_credito_proyectado})>"


class Pago(Base):
    """Modelo para la tabla pago."""
    __tablename__ = 'pago'
    
    pago_id = Column(Integer, primary_key=True)
    credito_id = Column(Integer, ForeignKey('credito.credito_id'))
    fecha = Column(Date)
    monto = Column(Float)
    
    # Relacion con Credito
    credito = relationship("Credito", back_populates="pagos")
    
    def __repr__(self):
        return f"<Pago(pago_id={self.pago_id}, credito_id={self.credito_id}, \
            monto={self.monto})>"
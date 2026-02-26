from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional
from decimal import Decimal

class CreditoBase(BaseModel):
    persona_id: int
    vendedor_id: int
    fecha: date
    tasa_interes: Decimal = Field(ge=0)
    monto_solicitado: Decimal = Field(gt=0)
    numero_cuotas: int = Field(gt=0)
    comision_asistencia_financiera: Decimal = Field(default=0.00, ge=0)
    comision_administrativa: Decimal = Field(default=0.00, ge=0)
    monto_colocado: Decimal = Field(gt=0)
    monto_intereses: Decimal = Field(default=0.00, ge=0)
    total_credito_proyectado: Decimal = Field(gt=0)
    cuota: Decimal = Field(gt=0)
    dia_pago: int = Field(ge=1, le=31)
    cancelado: bool = False
    privado: int = Field(default=0, ge=0, le=2)
    observaciones: Optional[str] = None
    estado_juridico: Optional[int] = 0

class CreditoCreate(CreditoBase):
    pass

class CreditoUpdate(CreditoBase):
    # Todos opcionales para permitir actualizaciones parciales
    persona_id: Optional[int] = None
    vendedor_id: Optional[int] = None
    fecha: Optional[date] = None
    monto_solicitado: Optional[Decimal] = None
    cancelado: Optional[bool] = None

class CreditoDTO(CreditoBase):
    credito_id: int
    
    class Config:
        from_attributes = True
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional
from decimal import Decimal
from .base import BaseSchema # Importas tu nueva base
from typing import List


class CreditoBase(BaseSchema):
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


class ConsultaSaldoDiarioRequest(BaseModel):
    credito_id: int = Field(..., description="ID único del crédito registrado")
    tasa_anual: float = Field(..., description="Tasa de interés anual fija (ej. 0.80 para 80%)")
    tasa_mora_anual: float = Field(..., description="Tasa de interés de mora anual (ej. 0.05 para 5%)")
    fecha_corte: Optional[date] = Field(None, description="Fecha de corte opcional (YYYY-MM-DD), por defecto hoy")        

class ReestructuracionCreate(BaseModel):
    creditos_origen_ids: List[int] = Field(..., min_items=1, description="Lista de IDs de créditos que se consolidarán/reestructurarán")
    tasa_interes_nueva: Decimal = Field(..., ge=0)
    numero_cuotas_nuevo: int = Field(..., gt=0)
    dia_pago_nuevo: int = Field(..., ge=1, le=31)
    monto_solicitado_nuevo: Decimal = Field(..., gt=0)
    cuota_nueva: Decimal = Field(..., gt=0)
    total_credito_proyectado_nuevo: Decimal = Field(..., gt=0)
    observacion: Optional[str] = None
    monto_colocado_nuevo: Optional[Decimal] = None    
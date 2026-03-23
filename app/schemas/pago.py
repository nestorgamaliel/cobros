from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
from decimal import Decimal
from .base import BaseSchema # Importas tu nueva base

class PagoBase(BaseSchema):
    credito_id: int
    fecha: date
    monto: Decimal = Field(ge=0, description="Monto destinado a capital")
    multa: Decimal = Field(default=0.00, ge=0)
    intereses: Decimal = Field(default=0.00, ge=0)
    monto_comision: Decimal = Field(default=0.00, ge=0)

class PagoCreate(PagoBase):
    pass

class PagoDTO(PagoBase):
    pago_id: int
    url_recibo: Optional[str] = None
    
    class Config:
        from_attributes = True
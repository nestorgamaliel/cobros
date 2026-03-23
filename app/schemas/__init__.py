from .base import BaseSchema
from .pago import PagoBase, PagoCreate, PagoDTO
from .credito import CreditoBase
from .persona import PersonaBase

# Esto permite que otros archivos vean estas clases fácilmente
__all__ = [
    "BaseSchema",
    "PagoBase",
    "PagoCreate",
    "PagoDTO",
    "CreditoBase",
    "PersonaBase"
]
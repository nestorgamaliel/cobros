from pydantic import BaseModel, Field, EmailStr
from datetime import date, datetime
from typing import Optional

# DTO Base: Atributos compartidos
class PersonaBase(BaseModel):
    nombres: str = Field(..., min_length=2, max_length=100)
    apellidos: str = Field(..., min_length=2, max_length=100)
    direccion: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=20)
    fecha_nacimiento: Optional[date] = None
    sexo: Optional[str] = Field(None, pattern="^[MF]$") # Solo acepta M o F
    dui: str = Field(..., min_length=9, max_length=10)
    municipio_id: Optional[int] = None
    departamento_id: Optional[int] = None

# DTO para Creación: Lo que recibes del Frontend
class PersonaCreate(PersonaBase):
    pass # Generalmente es igual al Base para nuevos registros

# DTO para Actualización: Todo es opcional para permitir cambios parciales (PATCH)
class PersonaUpdate(PersonaBase):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    dui: Optional[str] = None

# DTO de Salida (Lectura): Lo que la API devuelve
class PersonaDTO(PersonaBase):
    persona_id: int
    fum: datetime # Fecha de última modificación para el cliente

    class Config:
        from_attributes = True # Clave para que Pydantic lea modelos de SQLAlchemy
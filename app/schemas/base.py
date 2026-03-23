from pydantic import BaseModel, field_validator
from datetime import date
from typing import Any

class BaseSchema(BaseModel):
    """
    Clase base con validación de fecha global para el proyecto.
    """
    @field_validator('*', mode='before')
    @classmethod
    def validar_formato_fechas_global(cls, v: Any, info: Any) -> Any:
        # Verificamos si el valor es una cadena y si el campo esperado es una fecha
        # Pydantic v2 guarda el tipo de campo en el core_schema dentro de info
        if isinstance(v, str) and "-" in v:
            # Intentamos detectar si el campo en el modelo es de tipo 'date'
            field_name = info.field_name
            field_info = cls.model_fields.get(field_name)
            
            # Si el campo existe y su tipo es (o contiene) date
            if field_info and 'date' in str(field_info.annotation).lower():
                try:
                    return date.fromisoformat(v)
                except ValueError:
                    raise ValueError(
                        f'Formato de fecha inválido en "{field_name}". '
                        f'Se esperaba "YYYY-MM-DD" (ejemplo: 1958-02-28)'
                    )
        return v

    class Config:
        from_attributes = True
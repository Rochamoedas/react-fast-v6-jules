# src/application/dtos/response/field_response.py
from pydantic import BaseModel

from typing import Any # Added for type hinting

class FieldResponse(BaseModel):
    field_name: str
    field_code: str

    @classmethod
    def from_entity(cls, entity: Any) -> "FieldResponse": # Use "Any" for entity type hinting
        return cls(
            field_name=entity.field_name,
            field_code=entity.field_code,
        )

from pydantic import BaseModel
from typing import Optional, Any

class WellResponse(BaseModel):
    well_code: str
    well_name: str # Added well_name
    field_name: str
    field_code: str

    @classmethod
    def from_entity(cls, entity: Any) -> "WellResponse": # Use "Any" for entity type hinting
        return cls(
            well_code=entity.well_code,
            well_name=entity.well_name,
            field_name=entity.field_name,
            field_code=entity.field_code,
        )

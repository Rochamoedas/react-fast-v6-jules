from datetime import date
from pydantic import BaseModel
from typing import Optional, Any

class ProductionResponse(BaseModel):
    reference_date: date
    oil_prod: float
    gas_prod: float
    water_prod: float
    well_code: str

    @classmethod
    def from_entity(cls, entity: Any) -> "ProductionResponse": # Use "Any" for entity type hinting
        # This assumes 'entity' has attributes matching the fields in ProductionResponse
        return cls(
            reference_date=entity.reference_date,
            oil_prod=entity.oil_prod,
            gas_prod=entity.gas_prod,
            water_prod=entity.water_prod,
            well_code=entity.well_code,
        )

# src/application/dtos/response/oil_price_response.py
from datetime import date
from pydantic import BaseModel

class OilPriceResponse(BaseModel):
    reference_date: date
    field_name: str
    field_code: str
    price: float

    @classmethod
    def from_entity(cls, entity: Any) -> "OilPriceResponse": # Use "Any" for entity type hinting
        # This assumes 'entity' has attributes matching the fields in OilPriceResponse
        return cls(
            reference_date=entity.reference_date,
            field_name=entity.field_name,
            field_code=entity.field_code,
            price=entity.price,
        )

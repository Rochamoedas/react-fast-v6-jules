# src/application/dtos/response/exchange_rate_response.py
from datetime import date
from pydantic import BaseModel

from typing import Any # Added for type hinting

class ExchangeRateResponse(BaseModel):
    reference_date: date
    rate: float

    @classmethod
    def from_entity(cls, entity: Any) -> "ExchangeRateResponse": # Use "Any" for entity type hinting
        return cls(
            reference_date=entity.reference_date,
            rate=entity.rate,
        )

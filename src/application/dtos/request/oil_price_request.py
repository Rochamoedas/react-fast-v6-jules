# src/application/dtos/request/oil_price_request.py
from datetime import date
from pydantic import BaseModel, Field

class OilPriceRequest(BaseModel):
    reference_date: date
    field_name: str
    field_code: str
    price: float = Field(..., gt=0, description="Oil price in USD/bbl, must be positive")

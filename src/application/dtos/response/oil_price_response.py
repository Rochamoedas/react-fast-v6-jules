# src/application/dtos/response/oil_price_response.py
from datetime import date
from pydantic import BaseModel

class OilPriceResponse(BaseModel):
    reference_date: date
    field_name: str
    field_code: str
    price: float

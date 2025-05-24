# src/application/dtos/response/exchange_rate_response.py
from datetime import date
from pydantic import BaseModel

class ExchangeRateResponse(BaseModel):
    reference_date: date
    rate: float

# src/application/dtos/request/exchange_rate_request.py
from datetime import date
from pydantic import BaseModel, Field

class ExchangeRateRequest(BaseModel):
    reference_date: date
    rate: float = Field(..., gt=0, description="Exchange rate, must be positive")

from datetime import date
from pydantic import BaseModel, Field

class ExchangeRate(BaseModel):
    reference_date: date
    rate: float = Field(gt=0, description="Exchange rate, must be positive")

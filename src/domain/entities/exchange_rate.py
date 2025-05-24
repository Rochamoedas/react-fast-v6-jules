from datetime import date
from pydantic import BaseModel

class ExchangeRate(BaseModel):
    reference_date: date
    rate: float

from datetime import date
from pydantic import BaseModel

class OilPrice(BaseModel):
    reference_date: date
    field_name: str
    field_code: str
    price: float

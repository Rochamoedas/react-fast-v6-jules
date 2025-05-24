from datetime import date
from pydantic import BaseModel, Field

class OilPrice(BaseModel):
    reference_date: date
    field_name: str
    field_code: str
    price: float = Field(gt=0, description="Price, must be positive")

from datetime import date
from pydantic import BaseModel

class Production(BaseModel):
    reference_date: date
    oil_prod: float
    gas_prod: float
    water_prod: float
    well_code: str

from datetime import date
from pydantic import BaseModel

class ProductionRequest(BaseModel):
    reference_date: date
    oil_prod: float
    gas_prod: float
    water_prod: float
    well_code: str # Assuming well_code is used to link production to a well

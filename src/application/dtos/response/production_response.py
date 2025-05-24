from datetime import date
from pydantic import BaseModel
from typing import Optional, Any

class ProductionResponse(BaseModel):
    reference_date: date
    oil_prod: float
    gas_prod: float
    water_prod: float
    well_code: str
    # id: Optional[Any] = None # If we decide to expose a database ID

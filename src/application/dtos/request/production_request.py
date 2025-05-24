from datetime import date
from pydantic import BaseModel, Field

class ProductionRequest(BaseModel):
    reference_date: date
    oil_prod: float = Field(..., ge=0, description="Oil production in barrels, must be non-negative")
    gas_prod: float = Field(..., ge=0, description="Gas production in Mcf, must be non-negative")
    water_prod: float = Field(..., ge=0, description="Water production in barrels, must be non-negative")
    well_code: str # Assuming well_code is used to link production to a well

from datetime import date
from pydantic import BaseModel, Field

class Production(BaseModel):
    reference_date: date
    oil_prod: float = Field(ge=0, description="Oil production, must be non-negative")
    gas_prod: float = Field(ge=0, description="Gas production, must be non-negative")
    water_prod: float = Field(ge=0, description="Water production, must be non-negative")
    well_code: str

from pydantic import BaseModel, Field

class ProductionValue(BaseModel):
    oil_prod: float = Field(ge=0, description="Oil production, must be non-negative")
    gas_prod: float = Field(ge=0, description="Gas production, must be non-negative")
    water_prod: float = Field(ge=0, description="Water production, must be non-negative")

from pydantic import BaseModel, Field

class PriceVO(BaseModel):
    value: float = Field(gt=0, description="Price, must be positive")

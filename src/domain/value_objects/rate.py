from pydantic import BaseModel, Field

class RateVO(BaseModel):
    value: float = Field(gt=0, description="Exchange rate, must be positive")

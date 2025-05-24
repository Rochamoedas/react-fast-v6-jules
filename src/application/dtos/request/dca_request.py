# src/application/dtos/request/dca_request.py
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field

class DCARequest(BaseModel):
    well_code: str = Field(..., description="The code of the well for analysis.")
    start_date: Optional[date] = Field(None, description="Optional start date for production data to consider.")
    end_date: Optional[date] = Field(None, description="Optional end date for production data to consider.")
    model_type: str = Field("exponential", description="Type of decline curve model ('exponential' or 'hyperbolic').")
    forecast_duration: int = Field(365, description="Duration of the forecast in days.")

    class Config:
        schema_extra = {
            "example": {
                "well_code": "WELL-001",
                "start_date": "2022-01-01",
                "end_date": "2023-01-01",
                "model_type": "hyperbolic",
                "forecast_duration": 730
            }
        }

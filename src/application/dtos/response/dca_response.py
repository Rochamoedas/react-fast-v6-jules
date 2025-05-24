# src/application/dtos/response/dca_response.py
from typing import List, Dict
from pydantic import BaseModel, Field

class DCAResponse(BaseModel):
    well_code: str = Field(..., description="The code of the well analyzed.")
    model_type: str = Field(..., description="Type of decline curve model used ('exponential' or 'hyperbolic').")
    
    time_actual: List[float] = Field(..., description="Actual time data points (e.g., days).")
    rate_actual: List[float] = Field(..., description="Actual rate data points corresponding to time_actual.")
    
    time_fitted: List[float] = Field(..., description="Time data points for the fitted curve (typically same as time_actual).")
    rate_fitted: List[float] = Field(..., description="Fitted rate data points corresponding to time_fitted.")
    
    time_forecast: List[float] = Field(..., description="Time data points for the forecast period.")
    rate_forecast: List[float] = Field(..., description="Forecasted rate data points corresponding to time_forecast.")
    
    parameters: Dict[str, float] = Field(..., description="Fitted model parameters (e.g., qi, Di, b).")
    rmse: float = Field(..., description="Root Mean Squared Error between actual and fitted rates.")

    class Config:
        schema_extra = {
            "example": {
                "well_code": "WELL-001",
                "model_type": "hyperbolic",
                "time_actual": [0, 30, 60, 90, 120, 150, 180],
                "rate_actual": [1000, 850, 700, 600, 500, 450, 400],
                "time_fitted": [0, 30, 60, 90, 120, 150, 180],
                "rate_fitted": [1000.0, 855.1, 710.2, 605.3, 510.4, 455.5, 400.1],
                "time_forecast": [210, 240, 270, 300, 330, 360],
                "rate_forecast": [350.0, 310.5, 280.2, 250.8, 220.3, 190.7],
                "parameters": {"qi": 1000.0, "Di": 0.02, "b": 0.5},
                "rmse": 10.5
            }
        }

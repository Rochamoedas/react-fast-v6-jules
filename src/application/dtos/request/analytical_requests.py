# src/application/dtos/request/analytical_requests.py
from typing import List, Dict
from pydantic import BaseModel, Field

class AggregationRequest(BaseModel):
    group_by_fields: List[str] = Field(..., example=["well_code"])
    aggregation_functions: Dict[str, str] = Field(..., example={"oil_prod": "sum", "gas_prod": "mean"})

    class Config:
        schema_extra = {
            "example": {
                "group_by_fields": ["well_code", "reference_date.month"],
                "aggregation_functions": {"oil_prod": "avg", "gas_prod": "sum"}
            }
        }

# src/domain/aggregates/field_production.py
from typing import List
from pydantic import BaseModel
from src.domain.entities.production import Production

class FieldProduction(BaseModel):
    """
    Represents the aggregated production data for a specific field.
    """
    field_code: str
    productions: List[Production]

    def calculate_total_oil_production_kbd(self) -> float:
        """
        Calculates the total oil production for the field in thousand barrels per day (KBD).
        Assumes individual production records' oil_prod is in barrels per month.
        Uses an average of 30 days per month for conversion.
        """
        if not self.productions:
            return 0.0

        total_monthly_oil_production_bbl = sum(p.oil_prod for p in self.productions)
        
        # Convert barrels per month to barrels per day (assuming 30 days per month)
        total_daily_oil_production_bbl = total_monthly_oil_production_bbl / 30.0
        
        # Convert barrels per day to thousand barrels per day (KBD)
        total_daily_oil_production_kbd = total_daily_oil_production_bbl / 1000.0
        
        return total_daily_oil_production_kbd

    class Config:
        # Pydantic configuration to allow arbitrary types if needed later,
        # though not strictly necessary for current attributes.
        arbitrary_types_allowed = True

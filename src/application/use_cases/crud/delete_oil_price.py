# src/application/use_cases/crud/delete_oil_price.py
from typing import Any
from datetime import date
from src.domain.interfaces.repository import IOilPriceRepository
from src.core.exceptions import NotFoundError 
from .base import DeleteUseCase 

# IdentifierType is Any as base execute is overridden for composite key.
class DeleteOilPriceUseCase(DeleteUseCase[IOilPriceRepository, Any]):
    def __init__(self, oil_price_repository: IOilPriceRepository):
        super().__init__(oil_price_repository)

    def execute(self, field_code: str, reference_date: date) -> None:
        """
        Deletes an oil price record by composite key. Overrides base execute.
        Raises NotFoundError if the record does not exist.
        """
        key_values = {"field_code": field_code, "reference_date": reference_date}
        
        existing_entity = self.repository.get_by_composite_key(key_values)
        if not existing_entity:
            raise NotFoundError(f"Oil price entry with field_code '{field_code}' and reference_date '{reference_date}' not found.")
            
        self.repository.delete_by_composite_key(key_values)

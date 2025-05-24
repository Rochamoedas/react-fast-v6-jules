# src/application/use_cases/crud/delete_production.py
from typing import Any
from datetime import date
from src.domain.interfaces.repository import IProductionRepository
from src.core.exceptions import NotFoundError # Assuming you have a NotFoundError
from .base import DeleteUseCase # Import the base class

# IdentifierType is Any as base execute is overridden for composite key.
class DeleteProductionUseCase(DeleteUseCase[IProductionRepository, Any]):
    def __init__(self, production_repository: IProductionRepository):
        super().__init__(production_repository)

    def execute(self, well_code: str, reference_date: date) -> None:
        """
        Deletes a production record by composite key. Overrides base execute.
        Raises NotFoundError if the record does not exist.
        """
        key_values = {"well_code": well_code, "reference_date": reference_date}
        
        existing_entity = self.repository.get_by_composite_key(key_values)
        if not existing_entity:
            raise NotFoundError(f"Production entry with well_code '{well_code}' and reference_date '{reference_date}' not found.")
            
        self.repository.delete_by_composite_key(key_values)

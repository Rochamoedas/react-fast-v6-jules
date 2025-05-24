# src/application/use_cases/crud/delete_production.py
from typing import Any
from src.domain.interfaces.repository import IProductionRepository

class DeleteProductionUseCase:
    def __init__(self, production_repository: IProductionRepository):
        self.production_repository = production_repository

    def execute(self, production_id: Any) -> None:
        """
        Deletes a production record by its ID.
        """
        # Assumes IProductionRepository has a delete method that accepts production_id.
        # If ProductionDuckDBRepository.delete is inherited from DuckDBGenericRepository,
        # it needs to be implemented to call super().delete(production_id, self.pk_name).
        self.production_repository.delete(production_id)

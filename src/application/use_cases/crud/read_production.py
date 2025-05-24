# src/application/use_cases/crud/read_production.py
from typing import Optional, Any
from src.application.dtos.response.production_response import ProductionResponse
from src.domain.interfaces.repository import IProductionRepository

class ReadProductionUseCase:
    def __init__(self, production_repository: IProductionRepository):
        self.production_repository = production_repository

    def execute(self, production_id: Any) -> Optional[ProductionResponse]:
        """
        Retrieves a production record by its ID.
        'production_id' type is Any to accommodate various ID types (int, UUID, etc.)
        """
        # Assumes IProductionRepository has a method get_by_id or similar.
        # ProductionDuckDBRepository defines get_by_id(self, production_id: Any)
        production_entity = self.production_repository.get_by_id(production_id)
        
        if production_entity:
            return ProductionResponse(**production_entity.model_dump())
        return None

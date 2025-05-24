# src/application/use_cases/crud/update_production.py
from typing import Optional, Any
from src.application.dtos.request.production_request import ProductionRequest
from src.application.dtos.response.production_response import ProductionResponse
from src.domain.interfaces.repository import IProductionRepository
# from src.domain.entities.production import Production # For type hinting if needed

class UpdateProductionUseCase:
    def __init__(self, production_repository: IProductionRepository):
        self.production_repository = production_repository

    def execute(self, production_id: Any, production_request_dto: ProductionRequest) -> Optional[ProductionResponse]:
        """
        Updates an existing production record.
        """
        existing_production_entity = self.production_repository.get_by_id(production_id)
        
        if not existing_production_entity:
            return None # Production record not found

        update_data = production_request_dto.model_dump(exclude_unset=True)
        
        updated_production_entity = existing_production_entity.model_copy(update=update_data)
        
        persisted_production_entity = self.production_repository.update(updated_production_entity)
        
        return ProductionResponse(**persisted_production_entity.model_dump())

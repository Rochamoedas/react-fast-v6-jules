# src/application/use_cases/crud/create_production.py
from src.domain.entities.production import Production
from src.application.dtos.request.production_request import ProductionRequest
from src.application.dtos.response.production_response import ProductionResponse
from src.domain.interfaces.repository import IProductionRepository

class CreateProductionUseCase:
    def __init__(self, production_repository: IProductionRepository):
        self.production_repository = production_repository

    def execute(self, production_request_dto: ProductionRequest) -> ProductionResponse:
        """
        Creates a new production record.
        """
        production_entity = Production(**production_request_dto.model_dump())
        
        created_production_entity = self.production_repository.add(production_entity)
        
        return ProductionResponse(**created_production_entity.model_dump())

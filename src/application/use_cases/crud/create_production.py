# src/application/use_cases/crud/create_production.py
from src.domain.entities.production import Production
from src.application.dtos.request.production_request import ProductionRequest
from src.application.dtos.response.production_response import ProductionResponse
from src.domain.interfaces.repository import IProductionRepository
from .base import CreateUseCase # Import the base class

class CreateProductionUseCase(CreateUseCase[Production, ProductionRequest, ProductionResponse, IProductionRepository]):
    def __init__(self, production_repository: IProductionRepository):
        super().__init__(production_repository, Production, ProductionResponse)

    def execute(self, production_request_dto: ProductionRequest) -> ProductionResponse:
        """
        Creates a new production record. Leverages the base class execute method.
        Assumes no pre-existence check is needed here based on current file content.
        If a pre-existence check (e.g., by well_code and reference_date) was required, 
        this method would need to implement it.
        """
        # ProductionResponse has from_entity from previous subtask.
        return super().execute(production_request_dto)

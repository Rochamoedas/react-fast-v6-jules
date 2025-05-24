# src/application/use_cases/crud/read_production.py
from typing import Optional, Any
from datetime import date
from src.application.dtos.response.production_response import ProductionResponse
from src.domain.interfaces.repository import IProductionRepository
from src.domain.entities.production import Production # Ensure entity is imported
from .base import ReadUseCase # Import the base class

# For composite keys, IdentifierType in ReadUseCase might not be directly applicable
# if the base execute expects a single ID. We override execute entirely here.
class ReadProductionUseCase(ReadUseCase[Production, ProductionResponse, IProductionRepository, Any]): # Any for IdentifierType
    def __init__(self, production_repository: IProductionRepository):
        super().__init__(production_repository, ProductionResponse)

    def execute(self, well_code: str, reference_date: date) -> Optional[ProductionResponse]:
        """
        Retrieves a production record by its composite key (well_code, reference_date).
        This method overrides the base class execute method.
        """
        production_entity = self.repository.get_by_well_code_and_date(well_code, reference_date)
        
        if production_entity:
            # Use self.response_dto_type from base class
            return self.response_dto_type.from_entity(production_entity)
        return None

# src/application/use_cases/crud/update_production.py
from typing import Optional, Any
from datetime import date
from src.application.dtos.request.production_request import ProductionRequest
from src.application.dtos.response.production_response import ProductionResponse
from src.domain.interfaces.repository import IProductionRepository
from src.domain.entities.production import Production
from .base import UpdateUseCase # Import the base class

# IdentifierType is Any as base execute is overridden for composite key.
class UpdateProductionUseCase(UpdateUseCase[Production, ProductionRequest, ProductionResponse, IProductionRepository, Any]):
    def __init__(self, production_repository: IProductionRepository):
        super().__init__(production_repository, Production, ProductionResponse)

    def execute(self, well_code: str, reference_date: date, production_request_dto: ProductionRequest) -> Optional[ProductionResponse]:
        """
        Updates an existing production record by composite key. Overrides base execute.
        """
        key_values = {"well_code": well_code, "reference_date": reference_date}
        
        existing_entity = self.repository.get_by_well_code_and_date(well_code, reference_date)
        if not existing_entity:
            return None 

        # Create entity for update, ensuring keys from path are authoritative
        entity_to_update = self.entity_type(
            well_code=well_code, 
            reference_date=reference_date, 
            oil_prod=production_request_dto.oil_prod,
            gas_prod=production_request_dto.gas_prod,
            water_prod=production_request_dto.water_prod
        )
        
        persisted_entity = self.repository.update_by_composite_key(
            entity_to_update, 
            key_values
        )
        
        if persisted_entity:
            return self.response_dto_type.from_entity(persisted_entity)
        return None

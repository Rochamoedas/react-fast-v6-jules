# src/application/use_cases/crud/update_oil_price.py
from typing import Optional, Any
from datetime import date
from src.application.dtos.request.oil_price_request import OilPriceRequest
from src.application.dtos.response.oil_price_response import OilPriceResponse
from src.domain.interfaces.repository import IOilPriceRepository
from src.domain.entities.oil_price import OilPrice 
from .base import UpdateUseCase 

# IdentifierType is Any as base execute is overridden for composite key.
class UpdateOilPriceUseCase(UpdateUseCase[OilPrice, OilPriceRequest, OilPriceResponse, IOilPriceRepository, Any]):
    def __init__(self, oil_price_repository: IOilPriceRepository):
        super().__init__(oil_price_repository, OilPrice, OilPriceResponse)

    def execute(self, field_code: str, reference_date: date, oil_price_request_dto: OilPriceRequest) -> Optional[OilPriceResponse]:
        """
        Updates an existing oil price record by composite key. Overrides base execute.
        """
        key_values = {"field_code": field_code, "reference_date": reference_date}

        existing_entity = self.repository.get_by_field_code_and_date(field_code, reference_date)
        if not existing_entity:
            return None

        entity_to_update = self.entity_type(
            field_code=field_code, 
            reference_date=reference_date,
            field_name=oil_price_request_dto.field_name, 
            price=oil_price_request_dto.price
        )
        
        persisted_entity = self.repository.update_by_composite_key(
            entity_to_update,
            key_values
        )
        
        if persisted_entity:
            return self.response_dto_type.from_entity(persisted_entity)
        return None

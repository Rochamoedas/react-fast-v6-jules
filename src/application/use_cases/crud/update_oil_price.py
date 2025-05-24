# src/application/use_cases/crud/update_oil_price.py
from typing import Optional, Any
from src.application.dtos.request.oil_price_request import OilPriceRequest
from src.application.dtos.response.oil_price_response import OilPriceResponse
from src.domain.interfaces.repository import IOilPriceRepository
# from src.domain.entities.oil_price import OilPrice # For type hinting if needed

class UpdateOilPriceUseCase:
    def __init__(self, oil_price_repository: IOilPriceRepository):
        self.oil_price_repository = oil_price_repository

    def execute(self, price_id: Any, oil_price_request_dto: OilPriceRequest) -> Optional[OilPriceResponse]:
        """
        Updates an existing oil price record.
        """
        existing_oil_price_entity = self.oil_price_repository.get_by_id(price_id)
        
        if not existing_oil_price_entity:
            return None # Oil price record not found

        update_data = oil_price_request_dto.model_dump(exclude_unset=True)
        
        updated_oil_price_entity = existing_oil_price_entity.model_copy(update=update_data)
        
        persisted_oil_price_entity = self.oil_price_repository.update(updated_oil_price_entity)
        
        return OilPriceResponse(**persisted_oil_price_entity.model_dump())

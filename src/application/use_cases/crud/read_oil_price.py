# src/application/use_cases/crud/read_oil_price.py
from typing import Optional, Any
from src.application.dtos.response.oil_price_response import OilPriceResponse
from src.domain.interfaces.repository import IOilPriceRepository

class ReadOilPriceUseCase:
    def __init__(self, oil_price_repository: IOilPriceRepository):
        self.oil_price_repository = oil_price_repository

    def execute(self, price_id: Any) -> Optional[OilPriceResponse]:
        """
        Retrieves an oil price record by its ID.
        """
        # Assumes IOilPriceRepository has a method get_by_id or similar.
        # OilPriceDuckDBRepository defines get_by_id(self, price_id: Any)
        oil_price_entity = self.oil_price_repository.get_by_id(price_id)
        
        if oil_price_entity:
            return OilPriceResponse(**oil_price_entity.model_dump())
        return None

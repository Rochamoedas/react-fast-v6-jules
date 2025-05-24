# src/application/use_cases/crud/create_oil_price.py
from src.domain.entities.oil_price import OilPrice
from src.application.dtos.request.oil_price_request import OilPriceRequest
from src.application.dtos.response.oil_price_response import OilPriceResponse
from src.domain.interfaces.repository import IOilPriceRepository

class CreateOilPriceUseCase:
    def __init__(self, oil_price_repository: IOilPriceRepository):
        self.oil_price_repository = oil_price_repository

    def execute(self, oil_price_request_dto: OilPriceRequest) -> OilPriceResponse:
        """
        Creates a new oil price record.
        """
        oil_price_entity = OilPrice(**oil_price_request_dto.model_dump())
        
        created_oil_price_entity = self.oil_price_repository.add(oil_price_entity)
        
        return OilPriceResponse(**created_oil_price_entity.model_dump())

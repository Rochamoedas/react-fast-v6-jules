# src/application/use_cases/crud/create_oil_price.py
from src.domain.entities.oil_price import OilPrice
from src.application.dtos.request.oil_price_request import OilPriceRequest
from src.application.dtos.response.oil_price_response import OilPriceResponse
from src.domain.interfaces.repository import IOilPriceRepository
from .base import CreateUseCase # Import the base class

class CreateOilPriceUseCase(CreateUseCase[OilPrice, OilPriceRequest, OilPriceResponse, IOilPriceRepository]):
    def __init__(self, oil_price_repository: IOilPriceRepository):
        super().__init__(oil_price_repository, OilPrice, OilPriceResponse)

    def execute(self, oil_price_request_dto: OilPriceRequest) -> OilPriceResponse:
        """
        Creates a new oil price record. Leverages the base class execute method.
        """
        # Assumes OilPriceResponse.from_entity is available.
        return super().execute(oil_price_request_dto)

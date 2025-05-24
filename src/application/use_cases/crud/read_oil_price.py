# src/application/use_cases/crud/read_oil_price.py
from typing import Optional, Any 
from datetime import date
from src.application.dtos.response.oil_price_response import OilPriceResponse
from src.domain.interfaces.repository import IOilPriceRepository
from src.domain.entities.oil_price import OilPrice # Ensure entity is imported
from .base import ReadUseCase # Import the base class

# IdentifierType is Any as base execute is overridden for composite key.
class ReadOilPriceUseCase(ReadUseCase[OilPrice, OilPriceResponse, IOilPriceRepository, Any]): 
    def __init__(self, oil_price_repository: IOilPriceRepository):
        super().__init__(repository=oil_price_repository, response_dto_type=OilPriceResponse)

    def execute(self, field_code: str, reference_date: date) -> Optional[OilPriceResponse]:
        """
        Retrieves an oil price record by its composite key (field_code, reference_date).
        This method overrides the base class execute method because the identifier is composite.
        """
        oil_price_entity = self.repository.get_by_field_code_and_date(field_code, reference_date)
        
        if oil_price_entity:
            # self.response_dto_type is available from the base class
            return self.response_dto_type.from_entity(oil_price_entity)
        return None

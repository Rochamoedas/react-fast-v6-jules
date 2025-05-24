# src/application/use_cases/crud/list_oil_price.py
from typing import List, Optional 
from datetime import date
from src.domain.interfaces.repository import IOilPriceRepository
from src.application.dtos.response.oil_price_response import OilPriceResponse
from src.domain.entities.oil_price import OilPrice
from .base import ListUseCase 

class ListOilPriceUseCase(ListUseCase[OilPrice, OilPriceResponse, IOilPriceRepository]):
    def __init__(self, oil_price_repository: IOilPriceRepository):
        super().__init__(oil_price_repository, OilPriceResponse)

    def execute(self, field_code: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[OilPriceResponse]:
        """
        Lists oil price entries with specific filtering logic. Overrides base execute.
        """
        entries: List[OilPrice]
        if start_date and end_date:
            if field_code:
                filters = {"field_code": field_code, "start_date": start_date, "end_date": end_date}
                entries = self.repository.list(filters=filters) 
            else:
                entries = self.repository.find_by_date_range(start_date, end_date)
        elif field_code:
            entries = self.repository.find_by_field_code(field_code)
        else:
            entries = self.repository.list()
        
        return [self.response_dto_type.from_entity(entry) for entry in entries]

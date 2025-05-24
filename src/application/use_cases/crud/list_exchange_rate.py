# src/application/use_cases/crud/list_exchange_rate.py
from typing import List, Optional
from datetime import date
from src.domain.interfaces.repository import IExchangeRateRepository
from src.application.dtos.response.exchange_rate_response import ExchangeRateResponse
from src.domain.entities.exchange_rate import ExchangeRate
from .base import ListUseCase # Import the base class

class ListExchangeRateUseCase(ListUseCase[ExchangeRate, ExchangeRateResponse, IExchangeRateRepository]):
    def __init__(self, exchange_rate_repository: IExchangeRateRepository):
        super().__init__(exchange_rate_repository, ExchangeRateResponse)

    def execute(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[ExchangeRateResponse]:
        """
        Lists exchange rate entries with specific filtering for date ranges.
        Overrides the base execute method.
        """
        entries: List[ExchangeRate]
        if start_date and end_date:
            entries = self.repository.find_by_date_range(start_date, end_date)
        else:
            entries = self.repository.list()
        
        # Use self.response_dto_type from base class for DTO conversion
        # (ExchangeRateResponse should have from_entity)
        return [self.response_dto_type.from_entity(entry) for entry in entries]

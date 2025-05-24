# src/application/use_cases/crud/read_exchange_rate.py
from typing import Optional, Any
from src.application.dtos.response.exchange_rate_response import ExchangeRateResponse
from src.domain.interfaces.repository import IExchangeRateRepository

class ReadExchangeRateUseCase:
    def __init__(self, exchange_rate_repository: IExchangeRateRepository):
        self.exchange_rate_repository = exchange_rate_repository

    def execute(self, rate_id: Any) -> Optional[ExchangeRateResponse]:
        """
        Retrieves an exchange rate record by its ID.
        """
        # Assumes IExchangeRateRepository has a method get_by_id or similar.
        # ExchangeRateDuckDBRepository defines get_by_id(self, rate_id: Any)
        exchange_rate_entity = self.exchange_rate_repository.get_by_id(rate_id)
        
        if exchange_rate_entity:
            return ExchangeRateResponse(**exchange_rate_entity.model_dump())
        return None

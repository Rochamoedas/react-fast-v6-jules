# src/application/use_cases/crud/read_exchange_rate.py
from typing import Optional 
from datetime import date 
from src.application.dtos.response.exchange_rate_response import ExchangeRateResponse
from src.domain.interfaces.repository import IExchangeRateRepository
from src.domain.entities.exchange_rate import ExchangeRate 
from .base import ReadUseCase 

class ReadExchangeRateUseCase(ReadUseCase[ExchangeRate, ExchangeRateResponse, IExchangeRateRepository, date]):
    def __init__(self, exchange_rate_repository: IExchangeRateRepository):
        super().__init__(exchange_rate_repository, ExchangeRateResponse)

    def execute(self, rate_id: date) -> Optional[ExchangeRateResponse]:
        """
        Retrieves an exchange rate record by its ID (reference_date).
        Leverages the base class execute method.
        """
        return super().execute(rate_id)

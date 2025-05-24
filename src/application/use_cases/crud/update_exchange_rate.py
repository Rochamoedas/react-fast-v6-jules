# src/application/use_cases/crud/update_exchange_rate.py
from typing import Optional
from datetime import date # Import date
from src.application.dtos.request.exchange_rate_request import ExchangeRateRequest
from src.application.dtos.response.exchange_rate_response import ExchangeRateResponse
from src.domain.interfaces.repository import IExchangeRateRepository
from src.domain.entities.exchange_rate import ExchangeRate 
from .base import UpdateUseCase 

class UpdateExchangeRateUseCase(UpdateUseCase[ExchangeRate, ExchangeRateRequest, ExchangeRateResponse, IExchangeRateRepository, date]):
    def __init__(self, exchange_rate_repository: IExchangeRateRepository):
        super().__init__(exchange_rate_repository, ExchangeRate, ExchangeRateResponse)

    def execute(self, rate_id: date, exchange_rate_request_dto: ExchangeRateRequest) -> Optional[ExchangeRateResponse]:
        """
        Updates an existing exchange rate record.
        rate_id is the reference_date.
        Leverages the base class execute method.
        """
        # Base UpdateUseCase.execute handles get_by_id(rate_id), model_copy, update, and DTO conversion.
        return super().execute(rate_id, exchange_rate_request_dto)

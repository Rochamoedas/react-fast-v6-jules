# src/application/use_cases/crud/create_exchange_rate.py
from src.domain.entities.exchange_rate import ExchangeRate
from src.application.dtos.request.exchange_rate_request import ExchangeRateRequest
from src.application.dtos.response.exchange_rate_response import ExchangeRateResponse
from src.domain.interfaces.repository import IExchangeRateRepository
from .base import CreateUseCase 

class CreateExchangeRateUseCase(CreateUseCase[ExchangeRate, ExchangeRateRequest, ExchangeRateResponse, IExchangeRateRepository]):
    def __init__(self, exchange_rate_repository: IExchangeRateRepository):
        super().__init__(exchange_rate_repository, ExchangeRate, ExchangeRateResponse)

    def execute(self, exchange_rate_request_dto: ExchangeRateRequest) -> ExchangeRateResponse:
        """
        Creates a new exchange rate record. Leverages the base class execute method.
        """
        return super().execute(exchange_rate_request_dto)

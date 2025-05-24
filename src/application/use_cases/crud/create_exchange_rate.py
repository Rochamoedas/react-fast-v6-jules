# src/application/use_cases/crud/create_exchange_rate.py
from src.domain.entities.exchange_rate import ExchangeRate
from src.application.dtos.request.exchange_rate_request import ExchangeRateRequest
from src.application.dtos.response.exchange_rate_response import ExchangeRateResponse
from src.domain.interfaces.repository import IExchangeRateRepository

class CreateExchangeRateUseCase:
    def __init__(self, exchange_rate_repository: IExchangeRateRepository):
        self.exchange_rate_repository = exchange_rate_repository

    def execute(self, exchange_rate_request_dto: ExchangeRateRequest) -> ExchangeRateResponse:
        """
        Creates a new exchange rate record.
        """
        exchange_rate_entity = ExchangeRate(**exchange_rate_request_dto.model_dump())
        
        created_exchange_rate_entity = self.exchange_rate_repository.add(exchange_rate_entity)
        
        return ExchangeRateResponse(**created_exchange_rate_entity.model_dump())

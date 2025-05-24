# src/application/use_cases/crud/update_exchange_rate.py
from typing import Optional, Any
from src.application.dtos.request.exchange_rate_request import ExchangeRateRequest
from src.application.dtos.response.exchange_rate_response import ExchangeRateResponse
from src.domain.interfaces.repository import IExchangeRateRepository
# from src.domain.entities.exchange_rate import ExchangeRate # For type hinting if needed

class UpdateExchangeRateUseCase:
    def __init__(self, exchange_rate_repository: IExchangeRateRepository):
        self.exchange_rate_repository = exchange_rate_repository

    def execute(self, rate_id: Any, exchange_rate_request_dto: ExchangeRateRequest) -> Optional[ExchangeRateResponse]:
        """
        Updates an existing exchange rate record.
        """
        existing_exchange_rate_entity = self.exchange_rate_repository.get_by_id(rate_id)
        
        if not existing_exchange_rate_entity:
            return None # Exchange rate record not found

        update_data = exchange_rate_request_dto.model_dump(exclude_unset=True)
        
        updated_exchange_rate_entity = existing_exchange_rate_entity.model_copy(update=update_data)
        
        persisted_exchange_rate_entity = self.exchange_rate_repository.update(updated_exchange_rate_entity)
        
        return ExchangeRateResponse(**persisted_exchange_rate_entity.model_dump())

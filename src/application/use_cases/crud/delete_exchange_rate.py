# src/application/use_cases/crud/delete_exchange_rate.py
from typing import Any
from src.domain.interfaces.repository import IExchangeRateRepository

class DeleteExchangeRateUseCase:
    def __init__(self, exchange_rate_repository: IExchangeRateRepository):
        self.exchange_rate_repository = exchange_rate_repository

    def execute(self, rate_id: Any) -> None:
        """
        Deletes an exchange rate record by its ID.
        """
        # Assumes IExchangeRateRepository has a delete method that accepts rate_id.
        # If ExchangeRateDuckDBRepository.delete is inherited from DuckDBGenericRepository,
        # it needs to be implemented to call super().delete(rate_id, self.pk_name).
        self.exchange_rate_repository.delete(rate_id)

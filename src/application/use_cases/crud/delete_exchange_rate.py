# src/application/use_cases/crud/delete_exchange_rate.py
from datetime import date # Import date
from src.domain.interfaces.repository import IExchangeRateRepository
from src.core.exceptions import NotFoundError # Assuming NotFoundError is in core.exceptions
from .base import DeleteUseCase # Import the base class

class DeleteExchangeRateUseCase(DeleteUseCase[IExchangeRateRepository, date]):
    def __init__(self, exchange_rate_repository: IExchangeRateRepository):
        super().__init__(exchange_rate_repository)

    def execute(self, rate_id: date) -> None:
        """
        Deletes an exchange rate record by its ID (reference_date).
        Overrides base to include pre-existence check.
        Raises NotFoundError if the record does not exist.
        """
        # Check if the entity exists before attempting deletion
        # For ExchangeRate, rate_id is the reference_date which is the ID.
        existing_entity = self.repository.get_by_id(rate_id)
        if not existing_entity:
            raise NotFoundError(f"Exchange rate with ID {rate_id} not found.")
            
        # Call super().execute() which calls self.repository.delete(entity_id)
        super().execute(rate_id)

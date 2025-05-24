# src/application/use_cases/crud/delete_oil_price.py
from typing import Any
from src.domain.interfaces.repository import IOilPriceRepository

class DeleteOilPriceUseCase:
    def __init__(self, oil_price_repository: IOilPriceRepository):
        self.oil_price_repository = oil_price_repository

    def execute(self, price_id: Any) -> None:
        """
        Deletes an oil price record by its ID.
        """
        # Assumes IOilPriceRepository has a delete method that accepts price_id.
        # If OilPriceDuckDBRepository.delete is inherited from DuckDBGenericRepository,
        # it needs to be implemented to call super().delete(price_id, self.pk_name).
        self.oil_price_repository.delete(price_id)

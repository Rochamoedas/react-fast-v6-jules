import logging
from typing import List, Dict, Any

from src.domain.services.data_service import DataService
from src.domain.interfaces.repository import (
    IProductionRepository, 
    IOilPriceRepository, 
    IExchangeRateRepository
)
from src.domain.entities.production import Production
from src.domain.entities.oil_price import OilPrice
from src.domain.entities.exchange_rate import ExchangeRate

class JoinTablesUseCase:
    def __init__(
        self,
        production_repo: IProductionRepository,
        oil_price_repo: IOilPriceRepository,
        exchange_rate_repo: IExchangeRateRepository,
        data_service: DataService,
    ):
        self.production_repo = production_repo
        self.oil_price_repo = oil_price_repo
        self.exchange_rate_repo = exchange_rate_repo
        self.data_service = data_service
        self.logger = logging.getLogger(__name__)

    def execute(self) -> List[Dict[str, Any]]:
        """
        Fetches data from production, oil price, and exchange rate repositories,
        joins them using DataService, and returns the combined data.
        """
        self.logger.info("Executing JoinTablesUseCase.")

        production_data: List[Production] = []
        oil_price_data: List[OilPrice] = []
        exchange_rate_data: List[ExchangeRate] = []

        # Fetch Production Data
        try:
            production_data = self.production_repo.list()
            if production_data is None:
                self.logger.warning("Production repository returned None, treating as empty list.")
                production_data = []
            self.logger.info(f"Fetched {len(production_data)} production records.")
        except Exception as e:
            self.logger.error(f"Error fetching production data: {e}", exc_info=True)
            # If primary data (production) fails to load, cannot proceed effectively.
            return []

        # If no production data, joins will be empty or meaningless for a production-centric view
        if not production_data:
            self.logger.info("No production data available; returning empty list from JoinTablesUseCase.")
            return []

        # Fetch Oil Price Data
        try:
            oil_price_data = self.oil_price_repo.list()
            if oil_price_data is None:
                self.logger.warning("Oil price repository returned None, treating as empty list.")
                oil_price_data = []
            self.logger.info(f"Fetched {len(oil_price_data)} oil price records.")
        except Exception as e:
            self.logger.error(f"Error fetching oil price data: {e}", exc_info=True)
            # Proceeding without price data is possible; DataService's join handles empty lists.
            self.logger.warning("Proceeding with join operation without oil price data due to fetch error.")
            oil_price_data = [] 

        # Fetch Exchange Rate Data
        try:
            exchange_rate_data = self.exchange_rate_repo.list()
            if exchange_rate_data is None:
                self.logger.warning("Exchange rate repository returned None, treating as empty list.")
                exchange_rate_data = []
            self.logger.info(f"Fetched {len(exchange_rate_data)} exchange rate records.")
        except Exception as e:
            self.logger.error(f"Error fetching exchange rate data: {e}", exc_info=True)
            # Proceeding without exchange rate data is possible.
            self.logger.warning("Proceeding with join operation without exchange rate data due to fetch error.")
            exchange_rate_data = []

        # Join data using DataService
        joined_data: List[Dict[str, Any]] = []
        try:
            joined_data = self.data_service.join_data(
                production_data, 
                oil_price_data, 
                exchange_rate_data
            )
            self.logger.info(f"DataService returned {len(joined_data)} joined records.")
        except Exception as e:
            self.logger.error(f"Error joining data using DataService: {e}", exc_info=True)
            return [] # Return empty if join operation itself fails

        self.logger.info(f"JoinTablesUseCase finished, returning {len(joined_data)} joined items.")
        return joined_data

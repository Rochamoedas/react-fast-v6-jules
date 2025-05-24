import logging
from typing import List, Dict, Any, Optional, Type, Union

from pydantic import ValidationError

from src.domain.interfaces.external_api import IExternalAPI
from src.domain.interfaces.repository import (
    IProductionRepository, IOilPriceRepository, IExchangeRateRepository
)
from src.domain.entities.production import Production
from src.domain.entities.oil_price import OilPrice
from src.domain.entities.exchange_rate import ExchangeRate
# Assuming BaseEntity or a common model type for type hinting if needed, else Union of entities.
AnyEntity = Union[Production, OilPrice, ExchangeRate]
AnyRepository = Union[IProductionRepository, IOilPriceRepository, IExchangeRateRepository]


class ScheduleFetchDataUseCase:
    def __init__(self, 
                 api_adapter: IExternalAPI, 
                 production_repo: Optional[IProductionRepository] = None, 
                 oil_price_repo: Optional[IOilPriceRepository] = None,
                 exchange_rate_repo: Optional[IExchangeRateRepository] = None
                 ):
        self.api_adapter = api_adapter
        self.production_repo = production_repo
        self.oil_price_repo = oil_price_repo
        self.exchange_rate_repo = exchange_rate_repo
        self.logger = logging.getLogger(__name__)

    def execute(self, source_name: str, params: Optional[Dict[str, Any]] = None) -> None:
        """
        Fetches data from an external source and stores it in the appropriate repository.
        """
        self.logger.info(f"Executing ScheduleFetchDataUseCase for source: '{source_name}' with params: {params}")

        # 1. Fetch data from the external API
        raw_data_list: Optional[List[Dict[str, Any]]] = None
        try:
            raw_data_list = self.api_adapter.fetch_data(source_name, params if params else {})
            if raw_data_list is None or not isinstance(raw_data_list, list):
                self.logger.warning(
                    f"API adapter returned None or non-list for source '{source_name}'. Treating as empty."
                )
                raw_data_list = []
            self.logger.info(f"Fetched {len(raw_data_list)} raw items from API for source '{source_name}'.")
        except Exception as e:
            self.logger.error(f"Error fetching data from API for source '{source_name}': {e}", exc_info=True)
            return

        if not raw_data_list:
            self.logger.info(f"No data fetched from API for source '{source_name}'. Processing ends.")
            return

        # 2. Determine the target repository and entity type based on source_name
        entity_model_type: Optional[Type[AnyEntity]] = None
        target_repo: Optional[AnyRepository] = None

        if source_name == "production_data":
            entity_model_type = Production
            target_repo = self.production_repo
        elif source_name == "oil_price":
            entity_model_type = OilPrice
            target_repo = self.oil_price_repo
        elif source_name == "exchange_rate":
            entity_model_type = ExchangeRate
            target_repo = self.exchange_rate_repo
        # Extend with more sources/entities as needed

        if not entity_model_type or not target_repo:
            self.logger.error(
                f"Unknown source_name '{source_name}' or its repository is not configured/injected. Aborting."
            )
            return

        # 3. Convert fetched data to domain entities and save to repository
        items_processed = 0
        items_added_successfully = 0
        items_failed_validation = 0
        items_failed_to_add = 0

        for item_data in raw_data_list:
            items_processed += 1
            entity_instance: Optional[AnyEntity] = None
            try:
                entity_instance = entity_model_type(**item_data)
            except ValidationError as ve:
                self.logger.warning(
                    f"Validation error for item in '{source_name}': {ve.errors()}. Data: {item_data}",
                    exc_info=False # Usually, stack trace for VE is not needed unless debugging Pydantic itself
                )
                items_failed_validation += 1
                continue
            except Exception as e_other_validation: # Catch other potential errors during instantiation
                 self.logger.warning(
                    f"Non-Pydantic validation error for item in '{source_name}': {e_other_validation}. Data: {item_data}",
                    exc_info=True
                )
                 items_failed_validation += 1
                 continue


            try:
                target_repo.add(entity_instance) # Assuming repo.add()
                items_added_successfully += 1
            except Exception as dbe: 
                self.logger.error(
                    f"Error adding entity to repository for source '{source_name}': {dbe}. "
                    f"Entity: {entity_instance.model_dump_json() if entity_instance else 'None'}", 
                    exc_info=True
                )
                items_failed_to_add += 1
        
        self.logger.info(
            f"Finished processing for source '{source_name}'. "
            f"Total items fetched: {len(raw_data_list)}. "
            f"Items processed: {items_processed}. "
            f"Successfully added: {items_added_successfully}. "
            f"Validation failures: {items_failed_validation}. "
            f"Repository add failures: {items_failed_to_add}."
        )

import logging
from typing import List, Dict, Any

from src.domain.services.data_service import DataService
from src.domain.interfaces.repository import IProductionRepository
from src.domain.entities.production import Production # For type hinting data from repository

class AggregateProductionUseCase:
    def __init__(self, production_repo: IProductionRepository, data_service: DataService):
        self.production_repo = production_repo
        self.data_service = data_service
        self.logger = logging.getLogger(__name__)

    def execute(self, group_by_fields: List[str], aggregation_functions: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Fetches, aggregates, and returns production data.
        """
        self.logger.info(
            f"Executing AggregateProductionUseCase with group_by_fields: {group_by_fields} "
            f"and aggregation_functions: {aggregation_functions}"
        )

        all_production_entities: List[Production] = []
        try:
            # Fetch all production data from the repository
            all_production_entities = self.production_repo.list()
            if all_production_entities is None: # Handle repository returning None explicitly
                self.logger.warning("Production repository returned None, treating as empty list.")
                all_production_entities = []
            self.logger.info(f"Fetched {len(all_production_entities)} production records from repository.")
        except Exception as e:
            self.logger.error(f"Error fetching production data from repository: {e}", exc_info=True)
            return [] # Return empty list on error

        if not all_production_entities:
            self.logger.info("No production data available from the repository to aggregate.")
            return []

        # Aggregate the production data using the DataService
        aggregated_data: List[Dict[str, Any]] = []
        try:
            aggregated_data = self.data_service.aggregate_production(
                all_production_entities, 
                group_by_fields, 
                aggregation_functions
            )
            self.logger.info(f"DataService returned {len(aggregated_data)} aggregated records/groups.")
        except Exception as e:
            self.logger.error(f"Error aggregating production data using DataService: {e}", exc_info=True)
            return [] 

        self.logger.info(f"AggregateProductionUseCase finished, returning {len(aggregated_data)} aggregated items.")
        return aggregated_data

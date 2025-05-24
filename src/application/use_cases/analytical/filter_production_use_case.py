import logging
from typing import List, Dict, Any
from src.domain.services.data_service import DataService
from src.domain.interfaces.repository import IProductionRepository
from src.domain.entities.production import Production # For type hinting
from src.application.dtos.response.production_response import ProductionResponse

class FilterProductionUseCase:
    def __init__(self, data_service: DataService, production_repo: IProductionRepository):
        self.data_service = data_service
        self.production_repo = production_repo
        self.logger = logging.getLogger(__name__)

    def execute(self, criteria: Dict[str, Any]) -> List[ProductionResponse]:
        """
        Fetches, filters, and converts production data based on given criteria.
        """
        self.logger.info(f"Executing FilterProductionUseCase with criteria: {criteria}")

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
            self.logger.info("No production data available from the repository to filter.")
            return []

        # Filter the production data using the DataService
        filtered_entities: List[Production] = []
        try:
            filtered_entities = self.data_service.filter_production(all_production_entities, criteria)
            self.logger.info(f"Filtered data down to {len(filtered_entities)} records.")
        except Exception as e:
            self.logger.error(f"Error filtering production data using DataService: {e}", exc_info=True)
            # Depending on desired behavior, could return partial data or empty on filter error
            return [] 

        # Convert filtered Production entities to ProductionResponse DTOs
        response_dtos: List[ProductionResponse] = []
        try:
            response_dtos = [ProductionResponse(**entity.model_dump()) for entity in filtered_entities]
            self.logger.info(f"Successfully converted {len(response_dtos)} entities to DTOs.")
        except Exception as e:
            self.logger.error(f"Error converting Production entities to DTOs: {e}", exc_info=True)
            # If conversion fails for some entities, this could lead to partial data.
            # For simplicity, returning empty list if any conversion error occurs.
            return []
            
        self.logger.info(f"FilterProductionUseCase finished, returning {len(response_dtos)} DTOs.")
        return response_dtos

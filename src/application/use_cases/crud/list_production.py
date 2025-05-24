# src/application/use_cases/crud/list_production.py
from typing import List, Optional, Dict, Any # Keep Dict, Any for filters if base execute is used
from datetime import date
from src.domain.interfaces.repository import IProductionRepository
from src.application.dtos.response.production_response import ProductionResponse
from src.domain.entities.production import Production
from .base import ListUseCase # Import the base class

class ListProductionUseCase(ListUseCase[Production, ProductionResponse, IProductionRepository]):
    def __init__(self, production_repository: IProductionRepository):
        super().__init__(production_repository, ProductionResponse)

    def execute(self, well_code: Optional[str] = None, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[ProductionResponse]:
        """
        Lists production entries with specific filtering logic for well_code and date ranges.
        Overrides the base execute method.
        """
        entries: List[Production]
        if start_date and end_date:
            if well_code:
                # The base ListUseCase.execute takes a single 'filters' dict.
                # This specific logic needs to call appropriate repository methods.
                # This structure was from previous subtask, assuming repo has these.
                filters = {"well_code": well_code, "start_date": start_date, "end_date": end_date}
                entries = self.repository.list(filters=filters) 
            else:
                entries = self.repository.find_by_date_range(start_date, end_date)
        elif well_code:
            entries = self.repository.find_by_well_code(well_code)
        else:
            entries = self.repository.list()
        
        # Use self.response_dto_type from base class for DTO conversion
        return [self.response_dto_type.from_entity(entry) for entry in entries]

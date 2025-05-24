from typing import Optional
from src.application.dtos.response.well_response import WellResponse
from src.domain.interfaces.repository import IWellRepository
from src.domain.entities.well import Well # Ensure Well is imported
from .base import ReadUseCase # Import the base class

class ReadWellUseCase(ReadUseCase[Well, WellResponse, IWellRepository, str]):
    def __init__(self, well_repository: IWellRepository):
        # Pass response_dto_type to the base class constructor
        super().__init__(well_repository, WellResponse)

    def execute(self, well_code: str) -> Optional[WellResponse]:
        """
        Retrieves a well by its code. This overrides the base execute
        to use get_by_well_code.
        """
        well_entity = self.repository.get_by_well_code(well_code)
        
        if well_entity:
            # Use self.response_dto_type from base class (which has from_entity)
            return self.response_dto_type.from_entity(well_entity)
        return None

# Note: get_all_wells functionality is handled by ListWellUseCase.

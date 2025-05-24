from src.application.dtos.request.well_request import WellRequest
from src.application.dtos.response.well_response import WellResponse
from src.domain.interfaces.repository import IWellRepository
from src.domain.entities.well import Well 
from typing import Optional
from .base import UpdateUseCase # Import the base class

class UpdateWellUseCase(UpdateUseCase[Well, WellRequest, WellResponse, IWellRepository, str]):
    def __init__(self, well_repository: IWellRepository):
        super().__init__(well_repository, Well, WellResponse)

    def execute(self, well_code: str, well_request_dto: WellRequest) -> Optional[WellResponse]:
        """
        Updates an existing well. Overrides base to use get_by_well_code.
        """
        existing_well_entity = self.repository.get_by_well_code(well_code)
        
        if not existing_well_entity:
            return None # Well not found

        update_data = well_request_dto.model_dump(exclude_unset=True)
        
        updated_well_instance = existing_well_entity.model_copy(update=update_data)
        
        persisted_well_entity = self.repository.update(updated_well_instance)
        
        return self.response_dto_type.from_entity(persisted_well_entity)

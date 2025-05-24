from src.application.dtos.request.well_request import WellRequest
from src.application.dtos.response.well_response import WellResponse
from src.domain.interfaces.repository import IWellRepository
from src.domain.entities.well import Well # Ensure Well entity is imported for type hints if needed
from typing import Optional

class UpdateWellUseCase:
    def __init__(self, well_repository: IWellRepository):
        self.well_repository = well_repository

    def execute(self, well_code: str, well_request_dto: WellRequest) -> Optional[WellResponse]:
        """
        Updates an existing well.
        """
        existing_well_entity = self.well_repository.get_by_well_code(well_code)
        
        if not existing_well_entity:
            return None # Well not found

        # Create a dictionary of fields to update from the request DTO
        # exclude_unset=True ensures only provided fields are used for update
        update_data = well_request_dto.model_dump(exclude_unset=True)

        # Ensure the well_code from the path is authoritative, even if present in DTO.
        # (Pydantic's model_copy(update=...) will use keys from `update_data` dict,
        # so if well_code is in `update_data`, it could override the existing one if not handled)
        # However, the primary key (well_code) should not be changed via this method.
        # If well_code is part of WellRequest and can differ, it might indicate an attempt to change the PK.
        # For this implementation, we assume well_code in WellRequest DTO is for data, not for changing the PK.
        # The existing_well_entity.well_code is the true identifier.
        
        # Create the updated entity instance.
        # existing_well_entity.model_copy(update=update_data) creates a new instance
        # with fields from existing_well_entity overwritten by fields in update_data.
        updated_well_entity = existing_well_entity.model_copy(update=update_data)

        # Persist the updated entity using the repository
        # The repository's update method should handle the actual database update.
        # It's assumed to return the final state of the entity (e.g., after DB triggers or versioning).
        persisted_well_entity = self.well_repository.update(updated_well_entity)
        
        # Convert the persisted domain entity to a response DTO
        return WellResponse(**persisted_well_entity.model_dump())

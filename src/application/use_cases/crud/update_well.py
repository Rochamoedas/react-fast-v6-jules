from src.domain.entities.well import Well
from src.application.dtos.request.well_request import WellRequest # Or a specific UpdateWellRequest
from src.application.dtos.response.well_response import WellResponse
from src.domain.interfaces.repository import IWellRepository
from typing import Optional

class UpdateWellUseCase:
    def __init__(self, well_repository: IWellRepository):
        self.well_repository = well_repository

    def execute(self, well_code: str, well_request: WellRequest) -> Optional[WellResponse]:
        # Check if well exists
        existing_well = self.well_repository.get_by_well_code(well_code)
        if not existing_well:
            return None # Or raise an exception

        # Update fields - simple full update for now
        # Pydantic models can be updated like this:
        updated_well_data = existing_well.model_copy(update=well_request.model_dump(exclude_unset=True))
        
        # The repository's update method should handle persisting this
        # For now, we assume it takes the updated entity.
        # Some repository patterns might take ID and a dict of changes.
        # We'll assume the IWellRepository's update method expects the full entity.
        
        # The well_code in the path should match the well_code in the body,
        # or the one in the body should be ignored / validated.
        # For simplicity, we ensure the well_code from the path is used for the entity.
        if well_request.well_code != well_code:
            # Or handle as an error, depending on API design
            pass # For now, we assume well_request.well_code is the authoritative one if different,
                 # but typically they should match or path parameter is the key.
                 # Let's ensure the well_code from the path is the primary key.
            updated_well_data.well_code = well_code


        # This part is tricky: IWellRepository.update expects a Well entity.
        # We have existing_well (a Well entity) and well_request (a WellRequest DTO).
        # We need to merge them.
        
        # Create a new Well instance with updated fields
        # We are updating 'existing_well' based on 'well_request'
        # The 'well_code' is the key and should not change or be part of the request payload to change the key.
        
        # update_payload = well_request.model_dump()
        # Ensure well_code from path is used, not from payload if they differ for keying
        # update_payload['well_code'] = well_code 
        
        # well_to_update = Well(**update_payload) # Create a Well entity from the request data
        
        # The updated_well_data is already a Well instance because model_copy returns an instance of the model
        updated_entity = self.well_repository.update(updated_well_data)
        
        return WellResponse(**updated_entity.model_dump())

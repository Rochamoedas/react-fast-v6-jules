from src.domain.entities.well import Well
from src.application.dtos.request.well_request import WellRequest
from src.application.dtos.response.well_response import WellResponse
from src.domain.interfaces.repository import IWellRepository
from src.core.exceptions import AppException # Import AppException

class CreateWellUseCase:
    def __init__(self, well_repository: IWellRepository):
        self.well_repository = well_repository

    def execute(self, well_request_dto: WellRequest) -> WellResponse:
        well_to_create = Well(**well_request_dto.model_dump())

        # Check if a well with the same well_code already exists
        # Assuming IWellRepository has a method like get_by_well_code
        # If the primary key method is just get(), and it takes well_code, adjust accordingly.
        # For this example, let's assume get_by_well_code is appropriate.
        existing_well = self.well_repository.get_by_well_code(well_to_create.well_code)
        
        if existing_well:
            raise AppException(
                message=f"Well with code '{well_to_create.well_code}' already exists.",
                status_code=409  # HTTP 409 Conflict
            )
        
        # If no existing well is found, proceed with adding the new well
        created_well = self.well_repository.add(well_to_create)
        
        return WellResponse(**created_well.model_dump())

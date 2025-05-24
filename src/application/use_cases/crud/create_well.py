from src.domain.entities.well import Well
from src.application.dtos.request.well_request import WellRequest
from src.application.dtos.response.well_response import WellResponse
from src.domain.interfaces.repository import IWellRepository # Using specific interface

class CreateWellUseCase:
    def __init__(self, well_repository: IWellRepository):
        self.well_repository = well_repository

    def execute(self, well_request: WellRequest) -> WellResponse:
        # TODO: Add logic for checking if well_code already exists, if necessary
        
        well = Well(**well_request.model_dump())
        created_well = self.well_repository.add(well)
        
        # Assuming the repository returns the entity with any db-generated fields (like ID)
        # For now, WellResponse mirrors Well entity structure
        return WellResponse(**created_well.model_dump())

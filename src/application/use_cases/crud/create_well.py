from src.domain.entities.well import Well
from src.application.dtos.request.well_request import WellRequest
from src.application.dtos.response.well_response import WellResponse
from src.domain.interfaces.repository import IWellRepository
from src.core.exceptions import AppException # Import AppException
from .base import CreateUseCase # Import the base class

class CreateWellUseCase(CreateUseCase[Well, WellRequest, WellResponse, IWellRepository]):
    def __init__(self, well_repository: IWellRepository):
        super().__init__(well_repository, Well, WellResponse)

    def execute(self, well_request_dto: WellRequest) -> WellResponse:
        # Specific pre-existence check for Well
        existing_well = self.repository.get_by_well_code(well_request_dto.well_code)
        if existing_well:
            raise AppException(
                message=f"Well with code '{well_request_dto.well_code}' already exists.",
                status_code=409  # HTTP 409 Conflict
            )
        
        # Create entity instance using self.entity_type from base class
        well_to_create = self.entity_type(**well_request_dto.model_dump())
        
        created_well_entity = self.repository.add(well_to_create)
        
        # Convert to ResponseDTO using self.response_dto_type from base class
        # (which should have from_entity)
        return self.response_dto_type.from_entity(created_well_entity)

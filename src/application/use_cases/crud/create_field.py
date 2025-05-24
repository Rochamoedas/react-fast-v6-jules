# src/application/use_cases/crud/create_field.py
from src.domain.entities.field import Field
from src.application.dtos.request.field_request import FieldRequest
from src.application.dtos.response.field_response import FieldResponse
from src.domain.interfaces.repository import IFieldRepository

class CreateFieldUseCase:
    def __init__(self, field_repository: IFieldRepository):
        self.field_repository = field_repository

    def execute(self, field_request_dto: FieldRequest) -> FieldResponse:
        """
        Creates a new field.
        """
        field_entity = Field(**field_request_dto.model_dump())
        
        # Add the new field entity to the repository
        created_field_entity = self.field_repository.add(field_entity)
        
        # Convert the created domain entity to a response DTO
        return FieldResponse(**created_field_entity.model_dump())

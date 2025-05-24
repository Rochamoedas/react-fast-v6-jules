# src/application/use_cases/crud/update_field.py
from typing import Optional
from src.application.dtos.request.field_request import FieldRequest
from src.application.dtos.response.field_response import FieldResponse
from src.domain.interfaces.repository import IFieldRepository
# from src.domain.entities.field import Field # Not strictly needed unless for type hinting 'existing_field_entity'

class UpdateFieldUseCase:
    def __init__(self, field_repository: IFieldRepository):
        self.field_repository = field_repository

    def execute(self, field_code: str, field_request_dto: FieldRequest) -> Optional[FieldResponse]:
        """
        Updates an existing field.
        """
        existing_field_entity = self.field_repository.get_by_field_code(field_code)
        
        if not existing_field_entity:
            return None # Field not found

        # Create a dictionary of fields to update from the request DTO
        update_data = field_request_dto.model_dump(exclude_unset=True)
        
        # Create the updated entity instance
        updated_field_entity = existing_field_entity.model_copy(update=update_data)
        
        # Persist the updated entity using the repository
        persisted_field_entity = self.field_repository.update(updated_field_entity)
        
        # Convert the persisted domain entity to a response DTO
        return FieldResponse(**persisted_field_entity.model_dump())

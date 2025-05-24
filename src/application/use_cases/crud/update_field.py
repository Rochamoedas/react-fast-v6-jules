# src/application/use_cases/crud/update_field.py
from typing import Optional
from src.application.dtos.request.field_request import FieldRequest
from src.application.dtos.response.field_response import FieldResponse
from src.domain.interfaces.repository import IFieldRepository
from src.domain.entities.field import Field # Ensure Field is imported
from .base import UpdateUseCase # Import the base class

class UpdateFieldUseCase(UpdateUseCase[Field, FieldRequest, FieldResponse, IFieldRepository, str]):
    def __init__(self, field_repository: IFieldRepository):
        super().__init__(field_repository, Field, FieldResponse)

    def execute(self, field_code: str, field_request_dto: FieldRequest) -> Optional[FieldResponse]:
        """
        Updates an existing field. Overrides base to use get_by_field_code.
        """
        existing_field_entity = self.repository.get_by_field_code(field_code)
        
        if not existing_field_entity:
            return None # Field not found

        update_data = field_request_dto.model_dump(exclude_unset=True)
        
        updated_field_instance = existing_field_entity.model_copy(update=update_data)
        
        persisted_field_entity = self.repository.update(updated_field_instance)
        
        return self.response_dto_type.from_entity(persisted_field_entity)

# src/application/use_cases/crud/read_field.py
from typing import Optional
from src.application.dtos.response.field_response import FieldResponse
from src.domain.interfaces.repository import IFieldRepository
from src.domain.entities.field import Field # Ensure Field is imported
from .base import ReadUseCase # Import the base class

class ReadFieldUseCase(ReadUseCase[Field, FieldResponse, IFieldRepository, str]):
    def __init__(self, field_repository: IFieldRepository):
        super().__init__(field_repository, FieldResponse)

    def execute(self, field_code: str) -> Optional[FieldResponse]:
        """
        Retrieves a field by its code. Overrides base to use get_by_field_code.
        """
        field_entity = self.repository.get_by_field_code(field_code)
        
        if field_entity:
            return self.response_dto_type.from_entity(field_entity)
        return None

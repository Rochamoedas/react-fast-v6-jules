# src/application/use_cases/crud/read_field.py
from typing import Optional
from src.application.dtos.response.field_response import FieldResponse
from src.domain.interfaces.repository import IFieldRepository

class ReadFieldUseCase:
    def __init__(self, field_repository: IFieldRepository):
        self.field_repository = field_repository

    def execute(self, field_code: str) -> Optional[FieldResponse]:
        """
        Retrieves a field by its code.
        """
        # Assumes IFieldRepository has a method get_by_field_code,
        # or the concrete FieldDuckDBRepository implements it.
        # FieldDuckDBRepository has get_by_field_code(self, field_code: str) -> Optional[Field]:
        field_entity = self.field_repository.get_by_field_code(field_code)
        
        if field_entity:
            return FieldResponse(**field_entity.model_dump())
        return None

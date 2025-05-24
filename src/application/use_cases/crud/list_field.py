# src/application/use_cases/crud/list_field.py
from typing import List, Optional, Dict, Any
from src.domain.interfaces.repository import IFieldRepository
from src.application.dtos.response.field_response import FieldResponse
from src.domain.entities.field import Field
from .base import ListUseCase # Import the base class

class ListFieldUseCase(ListUseCase[Field, FieldResponse, IFieldRepository]):
    def __init__(self, field_repository: IFieldRepository):
        super().__init__(field_repository, FieldResponse)

    # The execute method can be inherited directly from ListUseCase
    # as FieldResponse has from_entity.

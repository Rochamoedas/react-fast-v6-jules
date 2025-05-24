# src/application/use_cases/crud/create_field.py
from src.domain.entities.field import Field
from src.application.dtos.request.field_request import FieldRequest
from src.application.dtos.response.field_response import FieldResponse
from src.domain.interfaces.repository import IFieldRepository
from .base import CreateUseCase # Import the base class

class CreateFieldUseCase(CreateUseCase[Field, FieldRequest, FieldResponse, IFieldRepository]):
    def __init__(self, field_repository: IFieldRepository):
        super().__init__(field_repository, Field, FieldResponse)

    def execute(self, field_request_dto: FieldRequest) -> FieldResponse:
        """
        Creates a new field. Leverages the base class execute method.
        Assumes no pre-existence check is needed here based on current file content.
        If a pre-existence check (e.g., by field_code) was required, 
        this method would need to implement it before calling super().execute() or 
        replicating the creation logic.
        """
        # The base class execute handles DTO -> Entity -> add -> DTO conversion.
        return super().execute(field_request_dto)

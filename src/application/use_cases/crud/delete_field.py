# src/application/use_cases/crud/delete_field.py
from src.domain.interfaces.repository import IFieldRepository
from .base import DeleteUseCase # Import the base class

class DeleteFieldUseCase(DeleteUseCase[IFieldRepository, str]):
    def __init__(self, field_repository: IFieldRepository):
        super().__init__(field_repository)
        # The IdentifierType is str (for field_code)

    def execute(self, field_code: str) -> None:
        """
        Deletes a field by its code.
        This now calls the base class execute method.
        The IFieldRepository.delete method is expected to accept field_code as entity_id.
        """
        super().execute(field_code)

# src/application/use_cases/crud/delete_field.py
from src.domain.interfaces.repository import IFieldRepository

class DeleteFieldUseCase:
    def __init__(self, field_repository: IFieldRepository):
        self.field_repository = field_repository

    def execute(self, field_code: str) -> None:
        """
        Deletes a field by its code.
        The repository's delete method is expected to handle cases
        where the field_code does not exist.
        """
        # Assumes IFieldRepository has a delete method that accepts field_code.
        # If FieldDuckDBRepository.delete is inherited from DuckDBGenericRepository,
        # it needs to be implemented to call super().delete(field_code, self.pk_name).
        self.field_repository.delete(field_code)

from src.domain.interfaces.repository import IWellRepository
from .base import DeleteUseCase # Import the base class

class DeleteWellUseCase(DeleteUseCase[IWellRepository, str]):
    def __init__(self, well_repository: IWellRepository):
        super().__init__(well_repository)
        # The IdentifierType is str (for well_code)

    def execute(self, well_code: str) -> None:
        """
        Deletes a well by its code.
        This now calls the base class execute method.
        The IWellRepository.delete method is expected to accept well_code as entity_id.
        The concrete WellDuckDBRepository must implement delete(self, entity_id: Any) 
        from IRepository and call super().delete(entity_id, self.pk_name) correctly.
        """
        super().execute(well_code)

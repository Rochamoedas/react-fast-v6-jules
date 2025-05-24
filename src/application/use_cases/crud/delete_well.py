from src.domain.interfaces.repository import IWellRepository
from typing import Optional

class DeleteWellUseCase:
    def __init__(self, well_repository: IWellRepository):
        self.well_repository = well_repository

    def execute(self, well_code: str) -> bool:
        # Check if well exists before attempting delete for a clearer true/false
        # or rely on repository to handle non-existent deletes gracefully (e.g., return None or raise)
        existing_well = self.well_repository.get_by_well_code(well_code)
        if not existing_well:
            return False # Well not found, so not deleted

        self.well_repository.delete(well_code) # Assuming delete takes the ID
        return True # Successfully deleted (or request to delete was made)

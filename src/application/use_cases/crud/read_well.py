from typing import Optional
from src.application.dtos.response.well_response import WellResponse
from src.domain.interfaces.repository import IWellRepository

class ReadWellUseCase:
    def __init__(self, well_repository: IWellRepository):
        self.well_repository = well_repository

    def execute(self, well_code: str) -> Optional[WellResponse]:
        """
        Retrieves a well by its code.
        """
        well = self.well_repository.get_by_well_code(well_code)
        if well:
            return WellResponse(**well.model_dump())
        return None

# Note: get_all_wells functionality might be part of a different use case
# (e.g., ListWellsUseCase) or added here later if requirements expand.
# For now, adhering to the single entity read pattern for ReadWellUseCase.
#
#    def get_all_wells(self) -> List[WellResponse]:
#        wells = self.well_repository.list()
#        return [WellResponse(**well.model_dump()) for well in wells]

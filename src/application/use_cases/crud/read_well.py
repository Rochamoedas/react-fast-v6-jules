from typing import Optional, List
from src.application.dtos.response.well_response import WellResponse
from src.domain.interfaces.repository import IWellRepository

class ReadWellUseCase:
    def __init__(self, well_repository: IWellRepository):
        self.well_repository = well_repository

    def get_by_well_code(self, well_code: str) -> Optional[WellResponse]:
        well = self.well_repository.get_by_well_code(well_code)
        if well:
            # Assuming 'well' is an instance of the domain entity Well
            # and WellResponse can be created from its dict representation
            return WellResponse(**well.model_dump())
        return None

    def get_all_wells(self) -> List[WellResponse]:
        wells = self.well_repository.list()
        # Assuming 'wells' is a list of domain entity Well instances
        return [WellResponse(**well.model_dump()) for well in wells]

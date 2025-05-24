# src/application/use_cases/crud/list_well.py
from typing import List, Optional, Dict, Any
from src.domain.interfaces.repository import IWellRepository
from src.application.dtos.response.well_response import WellResponse
from src.domain.entities.well import Well
from .base import ListUseCase # Import the base class

class ListWellUseCase(ListUseCase[Well, WellResponse, IWellRepository]):
    def __init__(self, well_repository: IWellRepository):
        # Pass response_dto_type to the base class constructor
        super().__init__(well_repository, WellResponse)

    # The execute method can be inherited directly from ListUseCase
    # if WellResponse.from_entity works as expected and the repository's list method
    # signature matches.
    #
    # def execute(self, filters: Optional[Dict[str, Any]] = None) -> List[WellResponse]:
    #     return super().execute(filters=filters)
    #
    # For clarity, or if any slight modification were needed, it could be written out:
    # def execute(self, filters: Optional[Dict[str, Any]] = None) -> List[WellResponse]:
    #     wells_entities: List[Well] = self.repository.list(filters=filters)
    #     return [self.response_dto_type.from_entity(well) for well in wells_entities]
    #
    # Since the base class execute is already:
    # def execute(self, filters: Optional[Dict[str, Any]] = None) -> List[ResponseDTO]:
    #     entities: List[Entity] = self.repository.list(filters=filters) # type: ignore
    #     response_list = []
    #     for entity in entities:
    #         if hasattr(self.response_dto_type, 'from_entity'):
    #             response_list.append(self.response_dto_type.from_entity(entity)) # type: ignore
    #         else:
    #             response_list.append(self.response_dto_type(**entity.model_dump())) # type: ignore
    #     return response_list
    # ... and WellResponse has from_entity, we can remove the explicit execute here.
    # If the base class implementation is sufficient, no need to override execute.

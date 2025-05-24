# src/routers/well_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any

from src.infrastructure.adapters.duckdb_adapter import DuckDBAdapter # For get_well_repository
from src.domain.interfaces.repository import IWellRepository
from src.application.dtos.request.well_request import WellRequest
from src.application.dtos.response.well_response import WellResponse
from src.application.use_cases.crud.create_well import CreateWellUseCase
from src.application.use_cases.crud.read_well import ReadWellUseCase
from src.application.use_cases.crud.update_well import UpdateWellUseCase
from src.application.use_cases.crud.delete_well import DeleteWellUseCase
from src.application.use_cases.crud.list_well import ListWellUseCase
from src.routers.dependencies import get_db_adapter # For DI of DuckDBAdapter
# from src.core.exceptions import NotFoundError # Not directly used here, but use cases might

# Router instance
well_router = APIRouter(prefix="/wells", tags=["Wells"])

# DI Providers for Well entity
def get_well_repository(adapter: DuckDBAdapter = Depends(get_db_adapter)) -> IWellRepository:
    # Ensure adapter provides get_well_repository method
    if not hasattr(adapter, 'get_well_repository'):
        raise AttributeError("DuckDBAdapter does not have get_well_repository method")
    return adapter.get_well_repository()

def get_create_well_use_case(repo: IWellRepository = Depends(get_well_repository)) -> CreateWellUseCase:
    return CreateWellUseCase(repo)

def get_read_well_use_case(repo: IWellRepository = Depends(get_well_repository)) -> ReadWellUseCase:
    return ReadWellUseCase(repo)

def get_update_well_use_case(repo: IWellRepository = Depends(get_well_repository)) -> UpdateWellUseCase:
    return UpdateWellUseCase(repo)

def get_delete_well_use_case(repo: IWellRepository = Depends(get_well_repository)) -> DeleteWellUseCase:
    return DeleteWellUseCase(repo)

def get_list_well_use_case(repo: IWellRepository = Depends(get_well_repository)) -> ListWellUseCase:
    return ListWellUseCase(repo)

# Well Endpoints
@well_router.post("/", response_model=WellResponse, status_code=status.HTTP_201_CREATED)
def create_well(well_request: WellRequest, use_case: CreateWellUseCase = Depends(get_create_well_use_case)):
    try:
        return use_case.execute(well_request)
    except Exception as e: # More specific exception handling can be added if needed
        # Consider if AppException from src.core.exceptions should be caught here or if global handler is enough
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@well_router.get("/{well_code}", response_model=WellResponse)
def read_well(well_code: str, use_case: ReadWellUseCase = Depends(get_read_well_use_case)):
    result = use_case.execute(well_code)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Well not found")
    return result

@well_router.get("/", response_model=List[WellResponse])
def list_wells(
    field_code: Optional[str] = Query(None), 
    well_name: Optional[str] = Query(None), 
    use_case: ListWellUseCase = Depends(get_list_well_use_case)
):
    filters: Dict[str, Any] = {}
    if field_code:
        filters["field_code"] = field_code
    if well_name:
        filters["well_name"] = well_name
    return use_case.execute(filters=filters if filters else None)

@well_router.put("/{well_code}", response_model=WellResponse)
def update_well(
    well_code: str, 
    well_request: WellRequest, 
    use_case: UpdateWellUseCase = Depends(get_update_well_use_case)
):
    if hasattr(well_request, 'well_code') and well_request.well_code != well_code:
         # This logic might be better placed within the use case or handled via validation
         well_request.well_code = well_code 

    updated_well = use_case.execute(well_code=well_code, well_request_dto=well_request)
    if not updated_well:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Well not found")
    return updated_well

@well_router.delete("/{well_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_well(
    well_code: str, 
    use_case: DeleteWellUseCase = Depends(get_delete_well_use_case),
    read_use_case: ReadWellUseCase = Depends(get_read_well_use_case) 
):
    # The check for existence before delete is a common pattern.
    # DeleteUseCase itself might also raise NotFoundError if it checks.
    if not read_use_case.execute(well_code): 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Well not found")
    try:
        use_case.execute(well_code)
    except Exception as e: 
        # Log error: import logging; logger = logging.getLogger(__name__); logger.error(...)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting well: {e}")

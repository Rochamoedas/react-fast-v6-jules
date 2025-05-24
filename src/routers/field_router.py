# src/routers/field_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any

from src.infrastructure.adapters.duckdb_adapter import DuckDBAdapter # For get_field_repository
from src.domain.interfaces.repository import IFieldRepository
from src.application.dtos.request.field_request import FieldRequest
from src.application.dtos.response.field_response import FieldResponse
from src.application.use_cases.crud.create_field import CreateFieldUseCase
from src.application.use_cases.crud.read_field import ReadFieldUseCase
from src.application.use_cases.crud.update_field import UpdateFieldUseCase
from src.application.use_cases.crud.delete_field import DeleteFieldUseCase
from src.application.use_cases.crud.list_field import ListFieldUseCase
from src.routers.dependencies import get_db_adapter # For DI of DuckDBAdapter
from src.core.exceptions import NotFoundError # For error handling

# Router instance
field_router = APIRouter(prefix="/fields", tags=["Fields"])

# DI Providers for Field entity
def get_field_repository(adapter: DuckDBAdapter = Depends(get_db_adapter)) -> IFieldRepository:
    if not hasattr(adapter, 'get_field_repository'):
        raise AttributeError("DuckDBAdapter does not have get_field_repository method")
    return adapter.get_field_repository()

def get_create_field_use_case(repo: IFieldRepository = Depends(get_field_repository)) -> CreateFieldUseCase:
    return CreateFieldUseCase(repo)

def get_read_field_use_case(repo: IFieldRepository = Depends(get_field_repository)) -> ReadFieldUseCase:
    return ReadFieldUseCase(repo)

def get_update_field_use_case(repo: IFieldRepository = Depends(get_field_repository)) -> UpdateFieldUseCase:
    return UpdateFieldUseCase(repo)

def get_delete_field_use_case(repo: IFieldRepository = Depends(get_field_repository)) -> DeleteFieldUseCase:
    return DeleteFieldUseCase(repo)

def get_list_field_use_case(repo: IFieldRepository = Depends(get_field_repository)) -> ListFieldUseCase:
    return ListFieldUseCase(repo)

# Field Endpoints
@field_router.post("/", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
def create_field(field_request: FieldRequest, use_case: CreateFieldUseCase = Depends(get_create_field_use_case)):
    try:
        return use_case.execute(field_request)
    except Exception as e: # Consider more specific exceptions if use case raises them
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@field_router.get("/{field_code}", response_model=FieldResponse)
def read_field(field_code: str, use_case: ReadFieldUseCase = Depends(get_read_field_use_case)):
    result = use_case.execute(field_code)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
    return result

@field_router.get("/", response_model=List[FieldResponse])
def list_fields(
    field_name: Optional[str] = Query(None), 
    use_case: ListFieldUseCase = Depends(get_list_field_use_case)
):
    filters: Dict[str, Any] = {}
    if field_name:
        filters["field_name"] = field_name
    return use_case.execute(filters=filters if filters else None)

@field_router.put("/{field_code}", response_model=FieldResponse)
def update_field(
    field_code: str, 
    field_request: FieldRequest, 
    use_case: UpdateFieldUseCase = Depends(get_update_field_use_case)
):
    if hasattr(field_request, 'field_code') and field_request.field_code != field_code:
        field_request.field_code = field_code

    updated_field = use_case.execute(field_code=field_code, field_request_dto=field_request)
    if not updated_field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
    return updated_field

@field_router.delete("/{field_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_field(
    field_code: str, 
    use_case: DeleteFieldUseCase = Depends(get_delete_field_use_case),
    read_use_case: ReadFieldUseCase = Depends(get_read_field_use_case) 
):
    if not read_use_case.execute(field_code):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
    try:
        use_case.execute(field_code)
    # Assuming DeleteFieldUseCase might raise specific errors, or catch generic ones
    except NotFoundError as e: # If DeleteUseCase is modified to raise NotFoundError
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e: 
        # logger.error(f"Error deleting field: {e}", exc_info=True) # Consider logging
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting field: {e}")

# src/routers/production_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import date

from src.infrastructure.adapters.duckdb_adapter import DuckDBAdapter
from src.domain.interfaces.repository import IProductionRepository
from src.application.dtos.request.production_request import ProductionRequest
from src.application.dtos.response.production_response import ProductionResponse
from src.application.use_cases.crud.create_production import CreateProductionUseCase
from src.application.use_cases.crud.read_production import ReadProductionUseCase
from src.application.use_cases.crud.update_production import UpdateProductionUseCase
from src.application.use_cases.crud.delete_production import DeleteProductionUseCase
from src.application.use_cases.crud.list_production import ListProductionUseCase
from src.routers.dependencies import get_db_adapter
from src.core.exceptions import NotFoundError
import logging # For potential logging within router endpoints

logger = logging.getLogger(__name__)

# Router instance
production_router = APIRouter(prefix="/production", tags=["Production Data"])

# DI Providers for Production entity
def get_production_repository(adapter: DuckDBAdapter = Depends(get_db_adapter)) -> IProductionRepository:
    if not hasattr(adapter, 'get_production_repository'):
        raise AttributeError("DuckDBAdapter does not have get_production_repository method")
    return adapter.get_production_repository()

def get_create_production_use_case(repo: IProductionRepository = Depends(get_production_repository)) -> CreateProductionUseCase:
    return CreateProductionUseCase(repo)

def get_read_production_use_case(repo: IProductionRepository = Depends(get_production_repository)) -> ReadProductionUseCase:
    return ReadProductionUseCase(repo)

def get_update_production_use_case(repo: IProductionRepository = Depends(get_production_repository)) -> UpdateProductionUseCase:
    return UpdateProductionUseCase(repo)

def get_delete_production_use_case(repo: IProductionRepository = Depends(get_production_repository)) -> DeleteProductionUseCase:
    return DeleteProductionUseCase(repo)

def get_list_production_use_case(repo: IProductionRepository = Depends(get_production_repository)) -> ListProductionUseCase:
    return ListProductionUseCase(repo)

# Production Endpoints
@production_router.post("/", response_model=ProductionResponse, status_code=status.HTTP_201_CREATED)
def create_production_entry(production_request: ProductionRequest, use_case: CreateProductionUseCase = Depends(get_create_production_use_case)):
    try:
        return use_case.execute(production_request)
    except Exception as e:
        logger.error(f"Error creating production entry: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@production_router.get("/{well_code}/{reference_date}", response_model=ProductionResponse)
def read_production_entry(well_code: str, reference_date: date, use_case: ReadProductionUseCase = Depends(get_read_production_use_case)):
    result = use_case.execute(well_code=well_code, reference_date=reference_date)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Production entry not found")
    return result

@production_router.get("/", response_model=List[ProductionResponse])
def list_production_entries(
    well_code: Optional[str] = Query(None), 
    start_date: Optional[date] = Query(None), 
    end_date: Optional[date] = Query(None), 
    use_case: ListProductionUseCase = Depends(get_list_production_use_case)
):
    return use_case.execute(well_code=well_code, start_date=start_date, end_date=end_date)

@production_router.put("/{well_code}/{reference_date}", response_model=ProductionResponse)
def update_production_entry(
    well_code: str, 
    reference_date: date, 
    production_request: ProductionRequest, 
    use_case: UpdateProductionUseCase = Depends(get_update_production_use_case)
):
    updated_production = use_case.execute(well_code=well_code, reference_date=reference_date, production_request_dto=production_request)
    if not updated_production:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Production entry not found for update")
    return updated_production

@production_router.delete("/{well_code}/{reference_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_production_entry(
    well_code: str, 
    reference_date: date, 
    use_case: DeleteProductionUseCase = Depends(get_delete_production_use_case)
):
    try:
        use_case.execute(well_code=well_code, reference_date=reference_date)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting production entry: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting production entry: {e}")

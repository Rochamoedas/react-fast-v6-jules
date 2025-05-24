# src/routers/oil_price_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import date

from src.infrastructure.adapters.duckdb_adapter import DuckDBAdapter
from src.domain.interfaces.repository import IOilPriceRepository
from src.application.dtos.request.oil_price_request import OilPriceRequest
from src.application.dtos.response.oil_price_response import OilPriceResponse
from src.application.use_cases.crud.create_oil_price import CreateOilPriceUseCase
from src.application.use_cases.crud.read_oil_price import ReadOilPriceUseCase
from src.application.use_cases.crud.update_oil_price import UpdateOilPriceUseCase
from src.application.use_cases.crud.delete_oil_price import DeleteOilPriceUseCase
from src.application.use_cases.crud.list_oil_price import ListOilPriceUseCase
from src.routers.dependencies import get_db_adapter
from src.core.exceptions import NotFoundError
import logging

logger = logging.getLogger(__name__)

# Router instance
oil_price_router = APIRouter(prefix="/oil-prices", tags=["Oil Prices"])

# DI Providers for Oil Price entity
def get_oil_price_repository(adapter: DuckDBAdapter = Depends(get_db_adapter)) -> IOilPriceRepository:
    if not hasattr(adapter, 'get_oil_price_repository'):
        raise AttributeError("DuckDBAdapter does not have get_oil_price_repository method")
    return adapter.get_oil_price_repository()

def get_create_oil_price_use_case(repo: IOilPriceRepository = Depends(get_oil_price_repository)) -> CreateOilPriceUseCase:
    return CreateOilPriceUseCase(repo)

def get_read_oil_price_use_case(repo: IOilPriceRepository = Depends(get_oil_price_repository)) -> ReadOilPriceUseCase:
    return ReadOilPriceUseCase(repo)

def get_update_oil_price_use_case(repo: IOilPriceRepository = Depends(get_oil_price_repository)) -> UpdateOilPriceUseCase:
    return UpdateOilPriceUseCase(repo)

def get_delete_oil_price_use_case(repo: IOilPriceRepository = Depends(get_oil_price_repository)) -> DeleteOilPriceUseCase:
    return DeleteOilPriceUseCase(repo)

def get_list_oil_price_use_case(repo: IOilPriceRepository = Depends(get_oil_price_repository)) -> ListOilPriceUseCase:
    return ListOilPriceUseCase(repo)

# Oil Price Endpoints
@oil_price_router.post("/", response_model=OilPriceResponse, status_code=status.HTTP_201_CREATED)
def create_oil_price_entry(oil_price_request: OilPriceRequest, use_case: CreateOilPriceUseCase = Depends(get_create_oil_price_use_case)):
    try:
        return use_case.execute(oil_price_request)
    except Exception as e:
        logger.error(f"Error creating oil price entry: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@oil_price_router.get("/{field_code}/{reference_date}", response_model=OilPriceResponse)
def read_oil_price_entry(field_code: str, reference_date: date, use_case: ReadOilPriceUseCase = Depends(get_read_oil_price_use_case)):
    result = use_case.execute(field_code=field_code, reference_date=reference_date)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oil price entry not found")
    return result

@oil_price_router.get("/", response_model=List[OilPriceResponse])
def list_oil_price_entries(
    field_code: Optional[str] = Query(None), 
    start_date: Optional[date] = Query(None), 
    end_date: Optional[date] = Query(None), 
    use_case: ListOilPriceUseCase = Depends(get_list_oil_price_use_case)
):
    return use_case.execute(field_code=field_code, start_date=start_date, end_date=end_date)

@oil_price_router.put("/{field_code}/{reference_date}", response_model=OilPriceResponse)
def update_oil_price_entry(
    field_code: str, 
    reference_date: date, 
    oil_price_request: OilPriceRequest, 
    use_case: UpdateOilPriceUseCase = Depends(get_update_oil_price_use_case)
):
    updated_oil_price = use_case.execute(field_code=field_code, reference_date=reference_date, oil_price_request_dto=oil_price_request)
    if not updated_oil_price:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oil price entry not found for update")
    return updated_oil_price

@oil_price_router.delete("/{field_code}/{reference_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_oil_price_entry(
    field_code: str, 
    reference_date: date, 
    use_case: DeleteOilPriceUseCase = Depends(get_delete_oil_price_use_case)
):
    try:
        use_case.execute(field_code=field_code, reference_date=reference_date)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting oil price entry: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting oil price entry: {e}")

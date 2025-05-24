# src/routers/exchange_rate_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import date

from src.infrastructure.adapters.duckdb_adapter import DuckDBAdapter
from src.domain.interfaces.repository import IExchangeRateRepository
from src.application.dtos.request.exchange_rate_request import ExchangeRateRequest
from src.application.dtos.response.exchange_rate_response import ExchangeRateResponse
from src.application.use_cases.crud.create_exchange_rate import CreateExchangeRateUseCase
from src.application.use_cases.crud.read_exchange_rate import ReadExchangeRateUseCase
from src.application.use_cases.crud.update_exchange_rate import UpdateExchangeRateUseCase
from src.application.use_cases.crud.delete_exchange_rate import DeleteExchangeRateUseCase
from src.application.use_cases.crud.list_exchange_rate import ListExchangeRateUseCase
from src.routers.dependencies import get_db_adapter
from src.core.exceptions import NotFoundError # Though not directly used in current endpoints, good for consistency
import logging

logger = logging.getLogger(__name__)

# Router instance
exchange_rate_router = APIRouter(prefix="/exchange-rates", tags=["Exchange Rates"])

# DI Providers for Exchange Rate entity
def get_exchange_rate_repository(adapter: DuckDBAdapter = Depends(get_db_adapter)) -> IExchangeRateRepository:
    if not hasattr(adapter, 'get_exchange_rate_repository'):
        raise AttributeError("DuckDBAdapter does not have get_exchange_rate_repository method")
    return adapter.get_exchange_rate_repository()

def get_create_exchange_rate_use_case(repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)) -> CreateExchangeRateUseCase:
    return CreateExchangeRateUseCase(repo)

def get_read_exchange_rate_use_case(repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)) -> ReadExchangeRateUseCase:
    return ReadExchangeRateUseCase(repo)

def get_update_exchange_rate_use_case(repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)) -> UpdateExchangeRateUseCase:
    return UpdateExchangeRateUseCase(repo)

def get_delete_exchange_rate_use_case(repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)) -> DeleteExchangeRateUseCase:
    return DeleteExchangeRateUseCase(repo)

def get_list_exchange_rate_use_case(repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)) -> ListExchangeRateUseCase:
    return ListExchangeRateUseCase(repo)

# Exchange Rate Endpoints
@exchange_rate_router.post("/", response_model=ExchangeRateResponse, status_code=status.HTTP_201_CREATED)
def create_exchange_rate_entry(exchange_rate_request: ExchangeRateRequest, use_case: CreateExchangeRateUseCase = Depends(get_create_exchange_rate_use_case)):
    try:
        return use_case.execute(exchange_rate_request)
    except Exception as e:
        logger.error(f"Error creating exchange rate entry: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@exchange_rate_router.get("/{reference_date}", response_model=ExchangeRateResponse)
def read_exchange_rate_entry(reference_date: date, use_case: ReadExchangeRateUseCase = Depends(get_read_exchange_rate_use_case)):
    result = use_case.execute(rate_id=reference_date) # Use case expects 'rate_id'
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange rate entry not found")
    return result

@exchange_rate_router.get("/", response_model=List[ExchangeRateResponse])
def list_exchange_rate_entries(
    start_date: Optional[date] = Query(None), 
    end_date: Optional[date] = Query(None), 
    use_case: ListExchangeRateUseCase = Depends(get_list_exchange_rate_use_case)
):
    return use_case.execute(start_date=start_date, end_date=end_date)

@exchange_rate_router.put("/{reference_date}", response_model=ExchangeRateResponse)
def update_exchange_rate_entry(
    reference_date: date, 
    exchange_rate_request: ExchangeRateRequest, 
    use_case: UpdateExchangeRateUseCase = Depends(get_update_exchange_rate_use_case)
):
    updated_entry = use_case.execute(rate_id=reference_date, exchange_rate_request_dto=exchange_rate_request)
    if not updated_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange rate entry not found")
    return updated_entry

@exchange_rate_router.delete("/{reference_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exchange_rate_entry(
    reference_date: date, 
    use_case: DeleteExchangeRateUseCase = Depends(get_delete_exchange_rate_use_case),
    read_use_case: ReadExchangeRateUseCase = Depends(get_read_exchange_rate_use_case) # For pre-check
):
    if not read_use_case.execute(rate_id=reference_date): # Check if entry exists
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange rate not found")
    try:
        use_case.execute(rate_id=reference_date)
    except NotFoundError as e: # If DeleteUseCase raises NotFoundError
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting exchange rate entry: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting exchange rate: {e}")

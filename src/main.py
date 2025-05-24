# src/main.py
import asyncio 
import logging 
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, Query, Request
from fastapi.responses import JSONResponse 
from typing import List, Optional, Dict, Any, cast

from datetime import date
from pydantic import BaseModel, Field # Added for AggregationRequest

# Logging configuration
from src.logging_config import setup_logging 

# Core exceptions
from src.core.exceptions import AppException 

# Infrastructure
from src.infrastructure.adapters.duckdb_adapter import DuckDBAdapter
from src.infrastructure.adapters.external_api_adapter import ExternalApiAdapter
from src.infrastructure.adapters.apscheduler_adapter import APSchedulerAdapter

# Domain Interfaces (Repositories & External API)
from src.domain.interfaces.repository import (
    IWellRepository, IFieldRepository, IProductionRepository,
    IOilPriceRepository, IExchangeRateRepository
)
from src.domain.interfaces.external_api import IExternalAPI
from src.domain.aggregates.financials import Financials
from src.domain.services.data_service import DataService # Added DataService

# Application DTOs
from src.application.dtos.request.well_request import WellRequest
from src.application.dtos.response.well_response import WellResponse
from src.application.dtos.request.field_request import FieldRequest
from src.application.dtos.response.field_response import FieldResponse
from src.application.dtos.request.production_request import ProductionRequest
from src.application.dtos.response.production_response import ProductionResponse # Ensure this covers analytical needs
from src.application.dtos.request.oil_price_request import OilPriceRequest
from src.application.dtos.response.oil_price_response import OilPriceResponse
from src.application.dtos.request.exchange_rate_request import ExchangeRateRequest
from src.application.dtos.response.exchange_rate_response import ExchangeRateResponse

# Application Use Cases - CRUD
from src.application.use_cases.crud.create_well import CreateWellUseCase
from src.application.use_cases.crud.read_well import ReadWellUseCase
from src.application.use_cases.crud.update_well import UpdateWellUseCase
from src.application.use_cases.crud.delete_well import DeleteWellUseCase
from src.application.use_cases.crud.create_field import CreateFieldUseCase
from src.application.use_cases.crud.read_field import ReadFieldUseCase
from src.application.use_cases.crud.update_field import UpdateFieldUseCase
from src.application.use_cases.crud.delete_field import DeleteFieldUseCase
from src.application.use_cases.crud.create_production import CreateProductionUseCase
from src.application.use_cases.crud.read_production import ReadProductionUseCase
from src.application.use_cases.crud.update_production import UpdateProductionUseCase
from src.application.use_cases.crud.delete_production import DeleteProductionUseCase
from src.application.use_cases.crud.create_oil_price import CreateOilPriceUseCase
from src.application.use_cases.crud.read_oil_price import ReadOilPriceUseCase
from src.application.use_cases.crud.update_oil_price import UpdateOilPriceUseCase
from src.application.use_cases.crud.delete_oil_price import DeleteOilPriceUseCase
from src.application.use_cases.crud.create_exchange_rate import CreateExchangeRateUseCase
from src.application.use_cases.crud.read_exchange_rate import ReadExchangeRateUseCase
from src.application.use_cases.crud.update_exchange_rate import UpdateExchangeRateUseCase
from src.application.use_cases.crud.delete_exchange_rate import DeleteExchangeRateUseCase

# Application Use Cases - Analytical
from src.application.use_cases.analytical.filter_production_use_case import FilterProductionUseCase
from src.application.use_cases.analytical.aggregate_production_use_case import AggregateProductionUseCase
from src.application.use_cases.analytical.join_tables_use_case import JoinTablesUseCase

# Get a logger for this module
logger = logging.getLogger(__name__)

# --- Pydantic Request Models for Analytical Use Cases ---
class AggregationRequest(BaseModel):
    group_by_fields: List[str] = Field(..., example=["well_code"])
    aggregation_functions: Dict[str, str] = Field(..., example={"oil_prod": "sum", "gas_prod": "mean"})


# --- FastAPI Application Setup ---
app = FastAPI(
    title="Oil & Gas Data API",
    description="API for managing and accessing oil and gas exploration and production data.",
    version="0.1.0"
)

# Instantiate Adapters
db_adapter = DuckDBAdapter() 
api_adapter = ExternalApiAdapter() 
scheduler_adapter: Optional[APSchedulerAdapter] = None


# --- Global Exception Handler ---
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.error(f"AppException caught: {exc}", exc_info=exc) 
    return JSONResponse(
        status_code=getattr(exc, "status_code", 500), 
        content={"message": f"An application error occurred: {str(exc)}",
                 "detail": getattr(exc, "detail", None)},
    )

@app.exception_handler(Exception) 
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected internal server error occurred."},
    )

# --- Lifespan Events for Database Connection & Scheduler ---
@app.on_event("startup")
async def startup_event():
    global scheduler_adapter 
    
    setup_logging() 
    logger.info("FastAPI application startup: Initializing database and scheduler...")
    
    db_adapter._get_connection() 
    db_adapter.initialize_database() 
    logger.info("Database initialized.")

    # Initialize and start APScheduler
    scheduler_adapter = APSchedulerAdapter(
        duckdb_adapter=db_adapter,
        external_api_adapter=api_adapter,
        data_service=DataService(), # Pass DataService instance
        financials_aggregate_type=Financials
    )
    
    # Example scheduling calls (adjust as needed)
    await scheduler_adapter.schedule_daily_data_fetch(source_name="production_data", hour=1, minute=0)
    await scheduler_adapter.schedule_daily_data_fetch(source_name="oil_price", hour=2, minute=0)
    await scheduler_adapter.schedule_daily_data_fetch(source_name="exchange_rate", hour=2, minute=15)
    await scheduler_adapter.schedule_daily_financial_computation(hour=3, minute=0)
    
    await scheduler_adapter.start()
    logger.info("APScheduler started and jobs scheduled.")


@app.on_event("shutdown")
async def shutdown_event():
    global scheduler_adapter
    logger.info("FastAPI application shutdown: Closing database connection and shutting down scheduler...")
    
    if scheduler_adapter:
        await scheduler_adapter.shutdown()
        logger.info("APScheduler shut down.")
    
    db_adapter._close_connection()
    logger.info("Database connection closed.")

# --- Dependency Injection Providers --- 
def get_db_adapter() -> DuckDBAdapter:
    return db_adapter

def get_api_adapter() -> IExternalAPI: 
    return api_adapter

# Repositories
def get_well_repository(adapter: DuckDBAdapter = Depends(get_db_adapter)) -> IWellRepository:
    return adapter.get_well_repository()

def get_field_repository(adapter: DuckDBAdapter = Depends(get_db_adapter)) -> IFieldRepository:
    return adapter.get_field_repository()

def get_production_repository(adapter: DuckDBAdapter = Depends(get_db_adapter)) -> IProductionRepository:
    return adapter.get_production_repository()

def get_oil_price_repository(adapter: DuckDBAdapter = Depends(get_db_adapter)) -> IOilPriceRepository:
    return adapter.get_oil_price_repository()

def get_exchange_rate_repository(adapter: DuckDBAdapter = Depends(get_db_adapter)) -> IExchangeRateRepository:
    return adapter.get_exchange_rate_repository()

# Use Cases - CRUD (abbreviated for focus)
def get_create_well_use_case(repo: IWellRepository = Depends(get_well_repository)) -> CreateWellUseCase:
    return CreateWellUseCase(repo)
# ... other CRUD use case providers ...
def get_read_well_use_case(repo: IWellRepository = Depends(get_well_repository)) -> ReadWellUseCase:
    return ReadWellUseCase(repo)
def get_update_well_use_case(repo: IWellRepository = Depends(get_well_repository)) -> UpdateWellUseCase:
    return UpdateWellUseCase(repo)
def get_delete_well_use_case(repo: IWellRepository = Depends(get_well_repository)) -> DeleteWellUseCase:
    return DeleteWellUseCase(repo)
def get_create_field_use_case(repo: IFieldRepository = Depends(get_field_repository)) -> CreateFieldUseCase:
    return CreateFieldUseCase(repo)
def get_read_field_use_case(repo: IFieldRepository = Depends(get_field_repository)) -> ReadFieldUseCase:
    return ReadFieldUseCase(repo)
def get_update_field_use_case(repo: IFieldRepository = Depends(get_field_repository)) -> UpdateFieldUseCase:
    return UpdateFieldUseCase(repo)
def get_delete_field_use_case(repo: IFieldRepository = Depends(get_field_repository)) -> DeleteFieldUseCase:
    return DeleteFieldUseCase(repo)
def get_create_production_use_case(repo: IProductionRepository = Depends(get_production_repository)) -> CreateProductionUseCase:
    return CreateProductionUseCase(repo)
def get_read_production_use_case(repo: IProductionRepository = Depends(get_production_repository)) -> ReadProductionUseCase:
    return ReadProductionUseCase(repo)
def get_update_production_use_case(repo: IProductionRepository = Depends(get_production_repository)) -> UpdateProductionUseCase:
    return UpdateProductionUseCase(repo)
def get_delete_production_use_case(repo: IProductionRepository = Depends(get_production_repository)) -> DeleteProductionUseCase:
    return DeleteProductionUseCase(repo)
def get_create_oil_price_use_case(repo: IOilPriceRepository = Depends(get_oil_price_repository)) -> CreateOilPriceUseCase:
    return CreateOilPriceUseCase(repo)
def get_read_oil_price_use_case(repo: IOilPriceRepository = Depends(get_oil_price_repository)) -> ReadOilPriceUseCase:
    return ReadOilPriceUseCase(repo)
def get_update_oil_price_use_case(repo: IOilPriceRepository = Depends(get_oil_price_repository)) -> UpdateOilPriceUseCase:
    return UpdateOilPriceUseCase(repo)
def get_delete_oil_price_use_case(repo: IOilPriceRepository = Depends(get_oil_price_repository)) -> DeleteOilPriceUseCase:
    return DeleteOilPriceUseCase(repo)
def get_create_exchange_rate_use_case(repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)) -> CreateExchangeRateUseCase:
    return CreateExchangeRateUseCase(repo)
def get_read_exchange_rate_use_case(repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)) -> ReadExchangeRateUseCase:
    return ReadExchangeRateUseCase(repo)
def get_update_exchange_rate_use_case(repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)) -> UpdateExchangeRateUseCase:
    return UpdateExchangeRateUseCase(repo)
def get_delete_exchange_rate_use_case(repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)) -> DeleteExchangeRateUseCase:
    return DeleteExchangeRateUseCase(repo)

# Use Cases - Analytical
def get_filter_production_use_case(production_repo: IProductionRepository = Depends(get_production_repository)) -> FilterProductionUseCase:
    return FilterProductionUseCase(data_service=DataService(), production_repo=production_repo)

def get_aggregate_production_use_case(production_repo: IProductionRepository = Depends(get_production_repository)) -> AggregateProductionUseCase:
    # Note: AggregateProductionUseCase expects (production_repo, data_service) in its constructor
    return AggregateProductionUseCase(production_repo=production_repo, data_service=DataService())


def get_join_tables_use_case(
    production_repo: IProductionRepository = Depends(get_production_repository),
    oil_price_repo: IOilPriceRepository = Depends(get_oil_price_repository),
    exchange_rate_repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)
) -> JoinTablesUseCase:
    # Constructor order: production_repo, oil_price_repo, exchange_rate_repo, data_service
    return JoinTablesUseCase(
        production_repo=production_repo,
        oil_price_repo=oil_price_repo,
        exchange_rate_repo=exchange_rate_repo,
        data_service=DataService()
    )

# --- API Routers ---
# CRUD Routers (existing)
well_router = APIRouter(prefix="/wells", tags=["Wells"])
@well_router.post("/", response_model=WellResponse, status_code=status.HTTP_201_CREATED)
def create_well(well_request: WellRequest, use_case: CreateWellUseCase = Depends(get_create_well_use_case)):
    try: return use_case.execute(well_request)
    except Exception as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
@well_router.get("/{well_code}", response_model=WellResponse)
def read_well(well_code: str, use_case: ReadWellUseCase = Depends(get_read_well_use_case)):
    result = use_case.execute(well_code)
    if not result: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Well not found")
    return result
@well_router.get("/", response_model=List[WellResponse])
def list_wells(field_code: Optional[str] = Query(None), well_name: Optional[str] = Query(None), repo: IWellRepository = Depends(get_well_repository)):
    filters: Dict[str, Any] = {}
    if field_code: filters["field_code"] = field_code
    if well_name: filters["well_name"] = well_name
    wells = repo.list(filters=filters if filters else None)
    return [WellResponse(**well.model_dump()) for well in wells]
@well_router.put("/{well_code}", response_model=WellResponse)
def update_well(well_code: str, well_request: WellRequest, use_case: UpdateWellUseCase = Depends(get_update_well_use_case)):
    if hasattr(well_request, 'well_code') and well_request.well_code != well_code: well_request.well_code = well_code 
    updated_well = use_case.execute(well_code=well_code, well_request_dto=well_request)
    if not updated_well: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Well not found")
    return updated_well
@well_router.delete("/{well_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_well(well_code: str, use_case: DeleteWellUseCase = Depends(get_delete_well_use_case), read_use_case: ReadWellUseCase = Depends(get_read_well_use_case)):
    if not read_use_case.execute(well_code): raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Well not found")
    try: use_case.execute(well_code)
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting well: {e}")

field_router = APIRouter(prefix="/fields", tags=["Fields"])
# ... (Field CRUD endpoints remain unchanged, abbreviated for focus) ...
@field_router.post("/", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
def create_field(field_request: FieldRequest, use_case: CreateFieldUseCase = Depends(get_create_field_use_case)):
    try: return use_case.execute(field_request)
    except Exception as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
@field_router.get("/{field_code}", response_model=FieldResponse)
def read_field(field_code: str, use_case: ReadFieldUseCase = Depends(get_read_field_use_case)):
    result = use_case.execute(field_code)
    if not result: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
    return result
@field_router.get("/", response_model=List[FieldResponse])
def list_fields(field_name: Optional[str] = Query(None), repo: IFieldRepository = Depends(get_field_repository)):
    filters: Dict[str, Any] = {}
    if field_name: filters["field_name"] = field_name
    fields = repo.list(filters=filters if filters else None)
    return [FieldResponse(**field.model_dump()) for field in fields]
@field_router.put("/{field_code}", response_model=FieldResponse)
def update_field(field_code: str, field_request: FieldRequest, use_case: UpdateFieldUseCase = Depends(get_update_field_use_case)):
    if hasattr(field_request, 'field_code') and field_request.field_code != field_code: field_request.field_code = field_code
    updated_field = use_case.execute(field_code=field_code, field_request_dto=field_request)
    if not updated_field: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
    return updated_field
@field_router.delete("/{field_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_field(field_code: str, use_case: DeleteFieldUseCase = Depends(get_delete_field_use_case), read_use_case: ReadFieldUseCase = Depends(get_read_field_use_case)):
    if not read_use_case.execute(field_code): raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
    try: use_case.execute(field_code)
    except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting field: {e}")

production_router = APIRouter(prefix="/production", tags=["Production Data"])
# ... (Production CRUD endpoints remain unchanged, abbreviated for focus) ...
@production_router.post("/", response_model=ProductionResponse, status_code=status.HTTP_201_CREATED)
def create_production_entry(production_request: ProductionRequest, use_case: CreateProductionUseCase = Depends(get_create_production_use_case)):
    try: return use_case.execute(production_request)
    except Exception as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
@production_router.get("/{well_code}/{reference_date}", response_model=ProductionResponse)
def read_production_entry(well_code: str, reference_date: date, repo: IProductionRepository = Depends(get_production_repository)):
    result = repo.get_by_well_code_and_date(well_code, reference_date)
    if not result: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Production entry not found")
    return ProductionResponse(**result.model_dump())
@production_router.get("/", response_model=List[ProductionResponse])
def list_production_entries(well_code: Optional[str] = Query(None), start_date: Optional[date] = Query(None), end_date: Optional[date] = Query(None), repo: IProductionRepository = Depends(get_production_repository)):
    if start_date and end_date:
        if well_code:
             filters = {"well_code": well_code, "start_date": start_date, "end_date": end_date} 
             entries = repo.list(filters=filters) 
        else: entries = repo.find_by_date_range(start_date, end_date)
    elif well_code: entries = repo.find_by_well_code(well_code)
    else: entries = repo.list() 
    return [ProductionResponse(**entry.model_dump()) for entry in entries]
@production_router.put("/{well_code}/{reference_date}", response_model=ProductionResponse)
def update_production_entry(well_code: str, reference_date: date, production_request: ProductionRequest, repo: IProductionRepository = Depends(get_production_repository)):
    key_values = {"well_code": well_code, "reference_date": reference_date}
    existing = repo.get_by_composite_key(key_values)
    if not existing: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Production entry not found")
    from src.domain.entities.production import Production 
    entity_to_update = Production(**production_request.model_dump())
    updated_entity = repo.update_by_composite_key(entity_to_update, key_values)
    return ProductionResponse(**updated_entity.model_dump())
@production_router.delete("/{well_code}/{reference_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_production_entry(well_code: str, reference_date: date, repo: IProductionRepository = Depends(get_production_repository)):
    key_values = {"well_code": well_code, "reference_date": reference_date}
    existing = repo.get_by_composite_key(key_values)
    if not existing: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Production entry not found")
    repo.delete_by_composite_key(key_values)

oil_price_router = APIRouter(prefix="/oil-prices", tags=["Oil Prices"])
# ... (Oil Price CRUD endpoints remain unchanged, abbreviated for focus) ...
@oil_price_router.post("/", response_model=OilPriceResponse, status_code=status.HTTP_201_CREATED)
def create_oil_price_entry(oil_price_request: OilPriceRequest, use_case: CreateOilPriceUseCase = Depends(get_create_oil_price_use_case)):
    try: return use_case.execute(oil_price_request)
    except Exception as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
@oil_price_router.get("/{field_code}/{reference_date}", response_model=OilPriceResponse)
def read_oil_price_entry(field_code: str, reference_date: date, repo: IOilPriceRepository = Depends(get_oil_price_repository)):
    result = repo.get_by_field_code_and_date(field_code, reference_date)
    if not result: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oil price entry not found")
    return OilPriceResponse(**result.model_dump())
@oil_price_router.get("/", response_model=List[OilPriceResponse])
def list_oil_price_entries(field_code: Optional[str] = Query(None), start_date: Optional[date] = Query(None), end_date: Optional[date] = Query(None), repo: IOilPriceRepository = Depends(get_oil_price_repository)):
    if start_date and end_date:
        if field_code:
             filters = {"field_code": field_code, "start_date": start_date, "end_date": end_date}
             entries = repo.list(filters=filters) 
        else: entries = repo.find_by_date_range(start_date, end_date)
    elif field_code: entries = repo.find_by_field_code(field_code)
    else: entries = repo.list()
    return [OilPriceResponse(**entry.model_dump()) for entry in entries]
@oil_price_router.put("/{field_code}/{reference_date}", response_model=OilPriceResponse)
def update_oil_price_entry(field_code: str, reference_date: date, oil_price_request: OilPriceRequest, repo: IOilPriceRepository = Depends(get_oil_price_repository)):
    key_values = {"field_code": field_code, "reference_date": reference_date}
    existing = repo.get_by_composite_key(key_values)
    if not existing: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oil price entry not found")
    from src.domain.entities.oil_price import OilPrice
    entity_to_update = OilPrice(**oil_price_request.model_dump())
    updated_entity = repo.update_by_composite_key(entity_to_update, key_values)
    return OilPriceResponse(**updated_entity.model_dump())
@oil_price_router.delete("/{field_code}/{reference_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_oil_price_entry(field_code: str, reference_date: date, repo: IOilPriceRepository = Depends(get_oil_price_repository)):
    key_values = {"field_code": field_code, "reference_date": reference_date}
    if not repo.get_by_composite_key(key_values): raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oil price entry not found")
    repo.delete_by_composite_key(key_values)

exchange_rate_router = APIRouter(prefix="/exchange-rates", tags=["Exchange Rates"])
# ... (Exchange Rate CRUD endpoints remain unchanged, abbreviated for focus) ...
@exchange_rate_router.post("/", response_model=ExchangeRateResponse, status_code=status.HTTP_201_CREATED)
def create_exchange_rate_entry(exchange_rate_request: ExchangeRateRequest, use_case: CreateExchangeRateUseCase = Depends(get_create_exchange_rate_use_case)):
    try: return use_case.execute(exchange_rate_request)
    except Exception as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
@exchange_rate_router.get("/{reference_date}", response_model=ExchangeRateResponse)
def read_exchange_rate_entry(reference_date: date, repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)):
    result = repo.get_by_date(reference_date)
    if not result: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange rate entry not found")
    return ExchangeRateResponse(**result.model_dump())
@exchange_rate_router.get("/", response_model=List[ExchangeRateResponse])
def list_exchange_rate_entries(start_date: Optional[date] = Query(None), end_date: Optional[date] = Query(None), repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)):
    if start_date and end_date: entries = repo.find_by_date_range(start_date, end_date)
    else: entries = repo.list()
    return [ExchangeRateResponse(**entry.model_dump()) for entry in entries]
@exchange_rate_router.put("/{reference_date}", response_model=ExchangeRateResponse)
def update_exchange_rate_entry(reference_date: date, exchange_rate_request: ExchangeRateRequest, use_case: UpdateExchangeRateUseCase = Depends(get_update_exchange_rate_use_case)):
    updated_entry = use_case.execute(rate_id=reference_date, exchange_rate_request_dto=exchange_rate_request)
    if not updated_entry: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange rate entry not found")
    return updated_entry
@exchange_rate_router.delete("/{reference_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exchange_rate_entry(reference_date: date, use_case: DeleteExchangeRateUseCase = Depends(get_delete_exchange_rate_use_case), read_use_case: ReadExchangeRateUseCase = Depends(get_read_exchange_rate_use_case)):
    if not read_use_case.execute(rate_id=reference_date): raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange rate not found")
    use_case.execute(rate_id=reference_date)

# Analytical Router
analysis_router = APIRouter(prefix="/analysis", tags=["Analysis"])

@analysis_router.post("/production/filter", response_model=List[ProductionResponse])
def filter_production_data(
    criteria: Dict[str, Any], 
    use_case: FilterProductionUseCase = Depends(get_filter_production_use_case)
):
    try:
        return use_case.execute(criteria=criteria)
    except Exception as e:
        logger.error(f"Error in filter_production_data endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@analysis_router.post("/production/aggregate", response_model=List[Dict[str, Any]])
def aggregate_production_data(
    request: AggregationRequest, 
    use_case: AggregateProductionUseCase = Depends(get_aggregate_production_use_case)
):
    try:
        return use_case.execute(
            group_by_fields=request.group_by_fields, 
            aggregation_functions=request.aggregation_functions
        )
    except Exception as e:
        logger.error(f"Error in aggregate_production_data endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@analysis_router.get("/data/joined", response_model=List[Dict[str, Any]])
def get_joined_data(
    use_case: JoinTablesUseCase = Depends(get_join_tables_use_case)
):
    try:
        return use_case.execute()
    except Exception as e:
        logger.error(f"Error in get_joined_data endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Include Routers in the main application
app.include_router(well_router)
app.include_router(field_router)
app.include_router(production_router)
app.include_router(oil_price_router)
app.include_router(exchange_rate_router)
app.include_router(analysis_router) # Added analytical router

# For debugging: A root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Oil & Gas Data API. See /docs for API documentation."}

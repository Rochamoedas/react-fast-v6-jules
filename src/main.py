# src/main.py
import asyncio # For APScheduler example jobs
import logging # Added for logging
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, Query, Request
from fastapi.responses import JSONResponse # Added for custom exception handler
from typing import List, Optional, Dict, Any, cast

from datetime import date

# Logging configuration
from src.logging_config import setup_logging # Added

# Core exceptions
from src.core.exceptions import AppException # Added

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

# Application DTOs (omitted for brevity in diff, assume they are correctly imported)
from src.application.dtos.request.well_request import WellRequest
from src.application.dtos.response.well_response import WellResponse
from src.application.dtos.request.field_request import FieldRequest
from src.application.dtos.response.field_response import FieldResponse
from src.application.dtos.request.production_request import ProductionRequest
from src.application.dtos.response.production_response import ProductionResponse
from src.application.dtos.request.oil_price_request import OilPriceRequest
from src.application.dtos.response.oil_price_response import OilPriceResponse
from src.application.dtos.request.exchange_rate_request import ExchangeRateRequest
from src.application.dtos.response.exchange_rate_response import ExchangeRateResponse

# Application Use Cases - CRUD (omitted for brevity in diff)
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

# Get a logger for this module
logger = logging.getLogger(__name__)

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
    logger.error(f"AppException caught: {exc}", exc_info=exc) # Log the exception
    return JSONResponse(
        status_code=getattr(exc, "status_code", 500), # Use status_code from exc if available
        content={"message": f"An application error occurred: {str(exc)}",
                 "detail": getattr(exc, "detail", None)},
    )

@app.exception_handler(Exception) # Catch-all for other unexpected errors
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
    
    # Setup logging
    setup_logging() # Call the logging setup function
    logger.info("FastAPI application startup: Initializing database and scheduler...")
    
    # Initialize Database
    db_adapter._get_connection() 
    db_adapter.initialize_database() 
    logger.info("Database initialized.")

    # Initialize and start APScheduler
    scheduler_adapter = APSchedulerAdapter(
        duckdb_adapter=db_adapter,
        external_api_adapter=api_adapter,
        financials_aggregate_type=Financials
    )
    
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

# --- Dependency Injection Providers --- (Omitted for brevity in diff, assume unchanged)
def get_db_adapter() -> DuckDBAdapter:
    return db_adapter

def get_api_adapter() -> IExternalAPI: # Use interface type
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

# Use Cases - Well
def get_create_well_use_case(repo: IWellRepository = Depends(get_well_repository)) -> CreateWellUseCase:
    return CreateWellUseCase(repo)

def get_read_well_use_case(repo: IWellRepository = Depends(get_well_repository)) -> ReadWellUseCase:
    return ReadWellUseCase(repo)

def get_update_well_use_case(repo: IWellRepository = Depends(get_well_repository)) -> UpdateWellUseCase:
    return UpdateWellUseCase(repo)

def get_delete_well_use_case(repo: IWellRepository = Depends(get_well_repository)) -> DeleteWellUseCase:
    return DeleteWellUseCase(repo)

# Use Cases - Field (similar setup for other entities)
def get_create_field_use_case(repo: IFieldRepository = Depends(get_field_repository)) -> CreateFieldUseCase:
    return CreateFieldUseCase(repo)

def get_read_field_use_case(repo: IFieldRepository = Depends(get_field_repository)) -> ReadFieldUseCase:
    return ReadFieldUseCase(repo)

def get_update_field_use_case(repo: IFieldRepository = Depends(get_field_repository)) -> UpdateFieldUseCase:
    return UpdateFieldUseCase(repo)

def get_delete_field_use_case(repo: IFieldRepository = Depends(get_field_repository)) -> DeleteFieldUseCase:
    return DeleteFieldUseCase(repo)

# Production
def get_create_production_use_case(repo: IProductionRepository = Depends(get_production_repository)) -> CreateProductionUseCase:
    return CreateProductionUseCase(repo)

def get_read_production_use_case(repo: IProductionRepository = Depends(get_production_repository)) -> ReadProductionUseCase:
    return ReadProductionUseCase(repo)

def get_update_production_use_case(repo: IProductionRepository = Depends(get_production_repository)) -> UpdateProductionUseCase:
    return UpdateProductionUseCase(repo)

def get_delete_production_use_case(repo: IProductionRepository = Depends(get_production_repository)) -> DeleteProductionUseCase:
    return DeleteProductionUseCase(repo)

# Oil Price
def get_create_oil_price_use_case(repo: IOilPriceRepository = Depends(get_oil_price_repository)) -> CreateOilPriceUseCase:
    return CreateOilPriceUseCase(repo)

def get_read_oil_price_use_case(repo: IOilPriceRepository = Depends(get_oil_price_repository)) -> ReadOilPriceUseCase:
    return ReadOilPriceUseCase(repo)

def get_update_oil_price_use_case(repo: IOilPriceRepository = Depends(get_oil_price_repository)) -> UpdateOilPriceUseCase:
    return UpdateOilPriceUseCase(repo)

def get_delete_oil_price_use_case(repo: IOilPriceRepository = Depends(get_oil_price_repository)) -> DeleteOilPriceUseCase:
    return DeleteOilPriceUseCase(repo)

# Exchange Rate
def get_create_exchange_rate_use_case(repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)) -> CreateExchangeRateUseCase:
    return CreateExchangeRateUseCase(repo)

def get_read_exchange_rate_use_case(repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)) -> ReadExchangeRateUseCase:
    return ReadExchangeRateUseCase(repo)

def get_update_exchange_rate_use_case(repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)) -> UpdateExchangeRateUseCase:
    return UpdateExchangeRateUseCase(repo)

def get_delete_exchange_rate_use_case(repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)) -> DeleteExchangeRateUseCase:
    return DeleteExchangeRateUseCase(repo)


# --- API Routers --- (Omitted for brevity in diff, assume unchanged from previous state)
# Well Router
well_router = APIRouter(prefix="/wells", tags=["Wells"])

@well_router.post("/", response_model=WellResponse, status_code=status.HTTP_201_CREATED)
def create_well(
    well_request: WellRequest,
    use_case: CreateWellUseCase = Depends(get_create_well_use_case)
):
    try:
        return use_case.execute(well_request)
    except Exception as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@well_router.get("/{well_code}", response_model=WellResponse)
def read_well(
    well_code: str,
    use_case: ReadWellUseCase = Depends(get_read_well_use_case)
):
    result = use_case.execute(well_code)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Well not found")
    return result

@well_router.get("/", response_model=List[WellResponse])
def list_wells(
    field_code: Optional[str] = Query(None, description="Filter by field code"),
    well_name: Optional[str] = Query(None, description="Filter by well name (exact match)"),
    repo: IWellRepository = Depends(get_well_repository) 
):
    filters: Dict[str, Any] = {}
    if field_code:
        filters["field_code"] = field_code
    if well_name:
        filters["well_name"] = well_name
    
    wells = repo.list(filters=filters if filters else None)
    return [WellResponse(**well.model_dump()) for well in wells]


@well_router.put("/{well_code}", response_model=WellResponse)
def update_well(
    well_code: str,
    well_request: WellRequest,
    use_case: UpdateWellUseCase = Depends(get_update_well_use_case)
):
    if hasattr(well_request, 'well_code') and well_request.well_code != well_code:
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
    if not read_use_case.execute(well_code): 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Well not found")
    try:
        use_case.execute(well_code)
    except Exception as e: 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting well: {e}")


# Field Router
field_router = APIRouter(prefix="/fields", tags=["Fields"])

@field_router.post("/", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
def create_field(
    field_request: FieldRequest,
    use_case: CreateFieldUseCase = Depends(get_create_field_use_case)
):
    try:
        return use_case.execute(field_request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@field_router.get("/{field_code}", response_model=FieldResponse)
def read_field(
    field_code: str,
    use_case: ReadFieldUseCase = Depends(get_read_field_use_case)
):
    result = use_case.execute(field_code)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
    return result

@field_router.get("/", response_model=List[FieldResponse])
def list_fields(
    field_name: Optional[str] = Query(None, description="Filter by field name (exact match)"),
    repo: IFieldRepository = Depends(get_field_repository)
):
    filters: Dict[str, Any] = {}
    if field_name:
        filters["field_name"] = field_name
    
    fields = repo.list(filters=filters if filters else None)
    return [FieldResponse(**field.model_dump()) for field in fields]

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
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting field: {e}")


# Production Router
production_router = APIRouter(prefix="/production", tags=["Production Data"])

@production_router.post("/", response_model=ProductionResponse, status_code=status.HTTP_201_CREATED)
def create_production_entry(
    production_request: ProductionRequest,
    use_case: CreateProductionUseCase = Depends(get_create_production_use_case)
):
    try:
        return use_case.execute(production_request)
    except Exception as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@production_router.get("/{well_code}/{reference_date}", response_model=ProductionResponse)
def read_production_entry(
    well_code: str,
    reference_date: date, 
    repo: IProductionRepository = Depends(get_production_repository)
):
    result = repo.get_by_well_code_and_date(well_code, reference_date)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Production entry not found")
    return ProductionResponse(**result.model_dump())


@production_router.get("/", response_model=List[ProductionResponse])
def list_production_entries(
    well_code: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    repo: IProductionRepository = Depends(get_production_repository)
):
    if start_date and end_date:
        if well_code:
             filters = {"well_code": well_code, "start_date": start_date, "end_date": end_date} # Custom filter
             entries = repo.list(filters=filters) 
        else:
            entries = repo.find_by_date_range(start_date, end_date)
    elif well_code:
        entries = repo.find_by_well_code(well_code)
    else:
        entries = repo.list() 
    
    return [ProductionResponse(**entry.model_dump()) for entry in entries]

@production_router.put("/{well_code}/{reference_date}", response_model=ProductionResponse)
def update_production_entry(
    well_code: str,
    reference_date: date,
    production_request: ProductionRequest,
    repo: IProductionRepository = Depends(get_production_repository) 
):
    key_values = {"well_code": well_code, "reference_date": reference_date}
    existing = repo.get_by_composite_key(key_values)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Production entry not found")

    from src.domain.entities.production import Production 
    entity_to_update = Production(**production_request.model_dump())
    updated_entity = repo.update_by_composite_key(entity_to_update, key_values)
    return ProductionResponse(**updated_entity.model_dump())


@production_router.delete("/{well_code}/{reference_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_production_entry(
    well_code: str,
    reference_date: date,
    repo: IProductionRepository = Depends(get_production_repository) 
):
    key_values = {"well_code": well_code, "reference_date": reference_date}
    existing = repo.get_by_composite_key(key_values)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Production entry not found")
    repo.delete_by_composite_key(key_values)


# OilPrice Router
oil_price_router = APIRouter(prefix="/oil-prices", tags=["Oil Prices"])

@oil_price_router.post("/", response_model=OilPriceResponse, status_code=status.HTTP_201_CREATED)
def create_oil_price_entry(
    oil_price_request: OilPriceRequest,
    use_case: CreateOilPriceUseCase = Depends(get_create_oil_price_use_case)
):
    try:
        return use_case.execute(oil_price_request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@oil_price_router.get("/{field_code}/{reference_date}", response_model=OilPriceResponse)
def read_oil_price_entry(
    field_code: str,
    reference_date: date,
    repo: IOilPriceRepository = Depends(get_oil_price_repository) 
):
    result = repo.get_by_field_code_and_date(field_code, reference_date)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oil price entry not found")
    return OilPriceResponse(**result.model_dump())

@oil_price_router.get("/", response_model=List[OilPriceResponse])
def list_oil_price_entries(
    field_code: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    repo: IOilPriceRepository = Depends(get_oil_price_repository)
):
    if start_date and end_date:
        if field_code:
             filters = {"field_code": field_code, "start_date": start_date, "end_date": end_date}
             entries = repo.list(filters=filters) 
        else:
            entries = repo.find_by_date_range(start_date, end_date)
    elif field_code:
        entries = repo.find_by_field_code(field_code)
    else:
        entries = repo.list()
    return [OilPriceResponse(**entry.model_dump()) for entry in entries]

@oil_price_router.put("/{field_code}/{reference_date}", response_model=OilPriceResponse)
def update_oil_price_entry(
    field_code: str,
    reference_date: date,
    oil_price_request: OilPriceRequest,
    repo: IOilPriceRepository = Depends(get_oil_price_repository)
):
    key_values = {"field_code": field_code, "reference_date": reference_date}
    existing = repo.get_by_composite_key(key_values)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oil price entry not found")
    
    from src.domain.entities.oil_price import OilPrice
    entity_to_update = OilPrice(**oil_price_request.model_dump())
    updated_entity = repo.update_by_composite_key(entity_to_update, key_values)
    return OilPriceResponse(**updated_entity.model_dump())

@oil_price_router.delete("/{field_code}/{reference_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_oil_price_entry(
    field_code: str,
    reference_date: date,
    repo: IOilPriceRepository = Depends(get_oil_price_repository)
):
    key_values = {"field_code": field_code, "reference_date": reference_date}
    if not repo.get_by_composite_key(key_values):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oil price entry not found")
    repo.delete_by_composite_key(key_values)


# ExchangeRate Router
exchange_rate_router = APIRouter(prefix="/exchange-rates", tags=["Exchange Rates"])

@exchange_rate_router.post("/", response_model=ExchangeRateResponse, status_code=status.HTTP_201_CREATED)
def create_exchange_rate_entry(
    exchange_rate_request: ExchangeRateRequest,
    use_case: CreateExchangeRateUseCase = Depends(get_create_exchange_rate_use_case)
):
    try:
        return use_case.execute(exchange_rate_request)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@exchange_rate_router.get("/{reference_date}", response_model=ExchangeRateResponse)
def read_exchange_rate_entry(
    reference_date: date,
    repo: IExchangeRateRepository = Depends(get_exchange_rate_repository) 
):
    result = repo.get_by_date(reference_date)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange rate entry not found")
    return ExchangeRateResponse(**result.model_dump())

@exchange_rate_router.get("/", response_model=List[ExchangeRateResponse])
def list_exchange_rate_entries(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    repo: IExchangeRateRepository = Depends(get_exchange_rate_repository)
):
    if start_date and end_date:
        entries = repo.find_by_date_range(start_date, end_date)
    else:
        entries = repo.list()
    return [ExchangeRateResponse(**entry.model_dump()) for entry in entries]

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
    read_use_case: ReadExchangeRateUseCase = Depends(get_read_exchange_rate_use_case)
):
    if not read_use_case.execute(rate_id=reference_date): 
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange rate not found")
    use_case.execute(rate_id=reference_date)


# Include Routers in the main application
app.include_router(well_router)
app.include_router(field_router)
app.include_router(production_router)
app.include_router(oil_price_router)
app.include_router(exchange_rate_router)

# For debugging: A root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Oil & Gas Data API. See /docs for API documentation."}

**Key Implementations:**

1.  **FastAPI App Instance:**
    *   `app = FastAPI(...)` created with title, description, and version.

2.  **Imports:**
    *   All necessary modules imported, including `FastAPI`, `Depends`, `HTTPException`, DTOs, use cases, repository interfaces, and the `DuckDBAdapter`.

3.  **DuckDBAdapter Instantiation:**
    *   `db_adapter = DuckDBAdapter()` instantiated globally.

4.  **Lifespan Events (Startup/Shutdown):**
    *   `@app.on_event("startup")`: Calls `db_adapter._get_connection()` and `db_adapter.initialize_database()` to ensure the database is connected and tables are created.
    *   `@app.on_event("shutdown")`: Calls `db_adapter._close_connection()` to close the database connection.

5.  **Dependency Injection:**
    *   Provider function `get_db_adapter()` returns the global `db_adapter` instance.
    *   Provider functions created for each repository (e.g., `get_well_repository`), depending on `get_db_adapter()`.
    *   Provider functions created for all CRUD use cases (e.g., `get_create_well_use_case`), injecting their respective repositories.

6.  **API Routers:**
    *   `APIRouter` created for each entity: `well_router`, `field_router`, `production_router`, `oil_price_router`, `exchange_rate_router`, with appropriate prefixes and tags.

7.  **CRUD Endpoints:**
    *   **Create (POST `/`)**: Implemented for all entities, taking a request DTO, using the corresponding `CreateEntityUseCase`, and returning a response DTO with status 201. Basic error handling for bad requests included.
    *   **Read One (GET `/{entity_id}` or composite key path):**
        *   Implemented for single PK entities (`Well`, `Field`, `ExchangeRate`) using their `ReadEntityUseCase`.
        *   For composite PK entities (`Production`, `OilPrice`), endpoints use specific repository methods (`get_by_well_code_and_date`, `get_by_field_code_and_date`) for direct lookup, as generic use cases assume a single ID.
        *   Returns 404 if not found.
    *   **Read List/Query (GET `/`)**:
        *   Implemented for all entities, using the repository's `list()` or specific query methods (e.g., `find_by_date_range`).
        *   Supports query parameters for filtering as specified:
            *   `Well`: `field_code`, `well_name`.
            *   `Field`: `field_name`.
            *   `Production`: `well_code`, `start_date`, `end_date`.
            *   `OilPrice`: `field_code`, `start_date`, `end_date`.
            *   `ExchangeRate`: `start_date`, `end_date`.
        *   Constructs a filter dictionary for exact matches passed to `repo.list()`. For date ranges or more specific queries, dedicated repository methods are used.
    *   **Update (PUT `/{entity_id}` or composite key path):**
        *   Implemented for single PK entities using their `UpdateEntityUseCase`.
        *   For composite PK entities, endpoints use specific repository methods (`update_by_composite_key`) directly.
        *   Returns updated response DTO or 404.
    *   **Delete (DELETE `/{entity_id}` or composite key path):**
        *   Implemented for single PK entities using their `DeleteEntityUseCase`, with an existence check using the `ReadEntityUseCase`.
        *   For composite PK entities, endpoints use specific repository methods (`delete_by_composite_key`) directly, including an existence check.
        *   Returns 204 No Content or 404.

8.  **Router Inclusion:**
    *   All routers are included in the main `app` using `app.include_router()`.
    *   A root `/` endpoint is added for basic API welcome.

**Notes on Implementation Choices:**
*   For entities with composite primary keys (`Production`, `OilPrice`), the Read One, Update, and Delete endpoints bypass the generic single-ID use cases and interact directly with repository methods designed for composite keys. This is a pragmatic approach given the current use case design.
*   The `list` endpoints use a combination of the generic `repo.list(filters=...)` for exact matches and specific repository methods (e.g., `find_by_date_range`) for range queries. More complex combined filtering (e.g., field_code AND date_range) would require enhancements to the generic `list` method or more specific repository methods.
*   Error handling is basic (`HTTPException` for 400, 404, 500). More specific error handling can be added.
*   The `cast` import was correctly placed at the top of the file.

The `src/main.py` file now provides a functional set of CRUD API endpoints for all defined entities.

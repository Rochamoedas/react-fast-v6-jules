# src/routers/analysis_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query # Query is not used here but kept for consistency
from typing import List, Optional, Dict, Any # Optional not used here but kept
from datetime import date # Though not directly used in endpoints, DI providers might need it via other modules

# Logging
import logging
logger = logging.getLogger(__name__)

# Core exceptions
from src.core.exceptions import NotFoundError

# Infrastructure & Adapters (for repository getters if defined locally, though preferred from their own router files)
# from src.infrastructure.adapters.duckdb_adapter import DuckDBAdapter # Not directly needed if using repo providers

# Domain Interfaces & Services
from src.domain.interfaces.repository import (
    IProductionRepository, IOilPriceRepository, IExchangeRateRepository, IWellRepository
)
from src.domain.services.data_service import DataService
from src.domain.services.dca_service import DCAService

# Application DTOs
from src.application.dtos.request.analytical_requests import AggregationRequest # Moved
from src.application.dtos.request.dca_request import DCARequest
from src.application.dtos.response.production_response import ProductionResponse
from src.application.dtos.response.dca_response import DCAResponse

# Application Use Cases - Analytical
from src.application.use_cases.analytical.filter_production_use_case import FilterProductionUseCase
from src.application.use_cases.analytical.aggregate_production_use_case import AggregateProductionUseCase
from src.application.use_cases.analytical.join_tables_use_case import JoinTablesUseCase
from src.application.use_cases.analytical.decline_curve_analysis_use_case import DeclineCurveAnalysisUseCase

# Global/Shared Dependency Providers
# from src.routers.dependencies import get_db_adapter # Not directly used by providers here, but by repo providers

# Repository DI Providers from other router modules
# These show inter-router dependencies for providers
from src.routers.production_router import get_production_repository
from src.routers.oil_price_router import get_oil_price_repository
from src.routers.exchange_rate_router import get_exchange_rate_repository
from src.routers.well_router import get_well_repository


# Router instance
analysis_router = APIRouter(prefix="/analysis", tags=["Analysis"])

# --- Dependency Injection Providers for Analytical Services and Use Cases ---

def get_data_service() -> DataService: 
    return DataService()

def get_dca_service() -> DCAService:
    return DCAService()

def get_filter_production_use_case(
    production_repo: IProductionRepository = Depends(get_production_repository),
    data_service: DataService = Depends(get_data_service) 
) -> FilterProductionUseCase:
    return FilterProductionUseCase(data_service=data_service, production_repo=production_repo)

def get_aggregate_production_use_case(
    production_repo: IProductionRepository = Depends(get_production_repository),
    data_service: DataService = Depends(get_data_service) 
) -> AggregateProductionUseCase:
    return AggregateProductionUseCase(production_repo=production_repo, data_service=data_service)

def get_join_tables_use_case(
    production_repo: IProductionRepository = Depends(get_production_repository),
    oil_price_repo: IOilPriceRepository = Depends(get_oil_price_repository),
    exchange_rate_repo: IExchangeRateRepository = Depends(get_exchange_rate_repository),
    data_service: DataService = Depends(get_data_service) 
) -> JoinTablesUseCase:
    return JoinTablesUseCase(
        production_repo=production_repo,
        oil_price_repo=oil_price_repo,
        exchange_rate_repo=exchange_rate_repo,
        data_service=data_service
    )

def get_decline_curve_analysis_use_case(
    production_repo: IProductionRepository = Depends(get_production_repository),
    dca_service: DCAService = Depends(get_dca_service),
    well_repo: IWellRepository = Depends(get_well_repository)
) -> DeclineCurveAnalysisUseCase:
    return DeclineCurveAnalysisUseCase(
        production_repo=production_repo,
        dca_service=dca_service,
        well_repo=well_repo
    )

# --- Analysis Endpoints ---

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
    request_body: AggregationRequest, 
    use_case: AggregateProductionUseCase = Depends(get_aggregate_production_use_case)
):
    try:
        return use_case.execute(
            group_by_fields=request_body.group_by_fields, 
            aggregation_functions=request_body.aggregation_functions
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

@analysis_router.post("/decline-curve", response_model=DCAResponse)
def perform_decline_curve_analysis(
    request_body: DCARequest, 
    use_case: DeclineCurveAnalysisUseCase = Depends(get_decline_curve_analysis_use_case)
):
    try:
        return use_case.execute(request_body)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error in perform_decline_curve_analysis endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during DCA.")

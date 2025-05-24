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
from src.domain.services.data_service import DataService 
from src.domain.services.dca_service import DCAService # Added DCAService

# Application DTOs
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
from src.application.dtos.request.dca_request import DCARequest # Added DCARequest
from src.application.dtos.response.dca_response import DCAResponse # Added DCAResponse


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
from src.application.use_cases.crud.list_well import ListWellUseCase
from src.application.use_cases.crud.list_field import ListFieldUseCase
from src.application.use_cases.crud.list_production import ListProductionUseCase
from src.application.use_cases.crud.list_oil_price import ListOilPriceUseCase
from src.application.use_cases.crud.list_exchange_rate import ListExchangeRateUseCase

# Application Use Cases - Analytical
from src.application.use_cases.analytical.filter_production_use_case import FilterProductionUseCase
from src.application.use_cases.analytical.aggregate_production_use_case import AggregateProductionUseCase
from src.application.use_cases.analytical.join_tables_use_case import JoinTablesUseCase
from src.application.use_cases.analytical.decline_curve_analysis_use_case import DeclineCurveAnalysisUseCase # Added DCA Use Case
from src.routers.dependencies import get_db_adapter, get_api_adapter # Moved global providers
from src.routers.well_router import well_router # Import the new well_router
from src.routers.field_router import field_router # Import the new field_router
from src.routers.production_router import production_router # Import the new production_router
from src.routers.oil_price_router import oil_price_router # Import the new oil_price_router
from src.routers.exchange_rate_router import exchange_rate_router # Import the new exchange_rate_router
from src.routers.analysis_router import analysis_router # Import the new analysis_router

# Get a logger for this module
logger = logging.getLogger(__name__)

# --- Pydantic Request Models for Analytical Use Cases ---
# AggregationRequest moved to src.application.dtos.request.analytical_requests

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
# get_db_adapter and get_api_adapter are now in src.routers.dependencies

# Repositories
# get_well_repository moved to src.routers.well_router
# get_field_repository moved to src.routers.field_router
# get_production_repository moved to src.routers.production_router
# get_oil_price_repository moved to src.routers.oil_price_router
# get_exchange_rate_repository moved to src.routers.exchange_rate_router

# Use Cases - CRUD (abbreviated for focus)
# Well use case providers moved to src.routers.well_router
# Field use case providers moved to src.routers.field_router
# Production use case providers moved to src.routers.production_router
# Oil Price use case providers moved to src.routers.oil_price_router
# Exchange Rate use case providers moved to src.routers.exchange_rate_router

# List Use Cases
# get_list_well_use_case moved to src.routers.well_router
# get_list_field_use_case moved to src.routers.field_router
# get_list_production_use_case moved to src.routers.production_router
# get_list_oil_price_use_case moved to src.routers.oil_price_router
# get_list_exchange_rate_use_case moved to src.routers.exchange_rate_router

# Use Cases - Analytical
# All analytical use case providers and get_dca_service moved to src.routers.analysis_router

# --- API Routers ---
# CRUD Routers (existing)
# well_router and its endpoints moved to src.routers.well_router
# field_router and its endpoints moved to src.routers.field_router
# production_router and its endpoints moved to src.routers.production_router
# oil_price_router and its endpoints moved to src.routers.oil_price_router
# exchange_rate_router and its endpoints moved to src.routers.exchange_rate_router
# analysis_router and its endpoints moved to src.routers.analysis_router

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

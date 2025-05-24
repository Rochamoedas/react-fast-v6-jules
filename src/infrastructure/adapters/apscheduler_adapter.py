# src/infrastructure/adapters/apscheduler_adapter.py
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_ERROR, JobExecutionEvent
from typing import Type 

# Domain & Application Layer components
from src.application.use_cases.scheduling.schedule_fetch_data_use_case import ScheduleFetchDataUseCase
from src.application.use_cases.scheduling.schedule_compute_financials_use_case import ScheduleComputeFinancialsUseCase
from src.domain.interfaces.external_api import IExternalAPI
from src.domain.interfaces.repository import (
    IProductionRepository, IOilPriceRepository, IExchangeRateRepository
)
from src.domain.aggregates.financials import Financials
from src.domain.services.data_service import DataService # Added DataService import

# Infrastructure Layer components
from src.infrastructure.adapters.duckdb_adapter import DuckDBAdapter 

# Initialize logger at module level
logger = logging.getLogger(__name__)

class APSchedulerAdapter:
    def __init__(self,
                 duckdb_adapter: DuckDBAdapter,
                 external_api_adapter: IExternalAPI,
                 data_service: DataService, # Added data_service parameter
                 financials_aggregate_type: Type[Financials]):
        """
        Initializes the APSchedulerAdapter.

        Args:
            duckdb_adapter: Instance of DuckDBAdapter to access repositories.
            external_api_adapter: Instance of an IExternalAPI implementation.
            data_service: Instance of DataService.
            financials_aggregate_type: The class type of the Financials aggregate.
        """
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_listener(self.job_listener, EVENT_JOB_ERROR)
        
        self.duckdb_adapter = duckdb_adapter
        self.external_api_adapter = external_api_adapter
        self.data_service = data_service # Store data_service
        self.financials_aggregate_type = financials_aggregate_type
        
        logger.info("APSchedulerAdapter initialized.")

    def job_listener(self, event: JobExecutionEvent):
        """Listens for job execution errors and logs them."""
        if event.exception:
            logger.error(f"Job {event.job_id} failed with exception: {event.exception}", exc_info=event.exception)
        else:
            # This part might be too verbose for regular successful jobs.
            # Consider logging only if a specific flag is set or for specific job types.
            logger.debug(f"Job {event.job_id} event: {event.__class__.__name__} (no exception).")


    async def schedule_daily_data_fetch(self, source_name: str, hour: int = 0, minute: int = 0):
        """
        Schedules a daily job to fetch data from a given source.
        """
        prod_repo: Optional[IProductionRepository] = None
        oil_repo: Optional[IOilPriceRepository] = None
        ex_repo: Optional[IExchangeRateRepository] = None

        # Dynamically get repositories based on source_name
        # This assumes that not all repositories are needed for every source.
        # ScheduleFetchDataUseCase is designed to accept None for unneeded repos.
        if source_name == "production_data":
            prod_repo = self.duckdb_adapter.get_production_repository()
        elif source_name == "oil_price":
            oil_repo = self.duckdb_adapter.get_oil_price_repository()
        elif source_name == "exchange_rate":
            ex_repo = self.duckdb_adapter.get_exchange_rate_repository()
        
        use_case = ScheduleFetchDataUseCase(
            api_adapter=self.external_api_adapter,
            production_repo=prod_repo,
            oil_price_repo=oil_repo,
            exchange_rate_repo=ex_repo
        )
        
        job_id = f"fetch_{source_name}_daily"
        try:
            self.scheduler.add_job(
                use_case.execute, 
                'cron', 
                args=[source_name], # params for execute method of use_case; params defaults to None
                hour=hour, 
                minute=minute, 
                id=job_id,
                replace_existing=True
            )
            logger.info(f"Job '{job_id}' scheduled daily at {hour:02d}:{minute:02d} for source '{source_name}'.")
        except Exception as e:
            logger.error(f"Error scheduling job '{job_id}': {e}", exc_info=True)


    async def schedule_daily_financial_computation(self, hour: int = 1, minute: int = 0):
        """
        Schedules a daily job to compute financial metrics.
        """
        production_repo = self.duckdb_adapter.get_production_repository()
        oil_price_repo = self.duckdb_adapter.get_oil_price_repository()
        exchange_rate_repo = self.duckdb_adapter.get_exchange_rate_repository()
        
        use_case = ScheduleComputeFinancialsUseCase(
            production_repo=production_repo,
            oil_price_repo=oil_price_repo,
            exchange_rate_repo=exchange_rate_repo,
            data_service=self.data_service, # Pass the data_service instance
            financials_aggregate_type=self.financials_aggregate_type
        )
        
        job_id = "compute_financials_daily"
        try:
            self.scheduler.add_job(
                use_case.execute,
                'cron',
                args=[None], # Corresponds to 'params: Optional[Dict[str, Any]] = None' in execute
                hour=hour,
                minute=minute,
                id=job_id,
                replace_existing=True
            )
            logger.info(f"Job '{job_id}' scheduled daily at {hour:02d}:{minute:02d}.")
        except Exception as e:
            logger.error(f"Error scheduling job '{job_id}': {e}", exc_info=True)

    async def start(self):
        """Starts the scheduler."""
        if not self.scheduler.running:
            try:
                self.scheduler.start()
                logger.info("APScheduler started.")
            except Exception as e: 
                logger.error(f"Error starting APScheduler: {e}", exc_info=True)
        else:
            logger.info("APScheduler already running.")

    async def shutdown(self):
        """Shuts down the scheduler."""
        if self.scheduler.running:
            try:
                self.scheduler.shutdown()
                logger.info("APScheduler shut down.")
            except Exception as e:
                logger.error(f"Error shutting down APScheduler: {e}", exc_info=True)
        else:
            logger.info("APScheduler not running, no shutdown needed.")

# Example usage remains commented out as it's for illustration
# async def main():
# ...
# if __name__ == "__main__":
# ...
#     pass

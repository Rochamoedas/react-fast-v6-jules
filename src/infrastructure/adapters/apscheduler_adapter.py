# src/infrastructure/adapters/apscheduler_adapter.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_ERROR, JobExecutionEvent
from typing import Type # For Financials aggregate type

# Domain & Application Layer components
from src.application.use_cases.scheduling.schedule_fetch_data_use_case import ScheduleFetchDataUseCase
from src.application.use_cases.scheduling.schedule_compute_financials_use_case import ScheduleComputeFinancialsUseCase
from src.domain.interfaces.external_api import IExternalAPI
from src.domain.interfaces.repository import (
    IProductionRepository, IOilPriceRepository, IExchangeRateRepository
)
from src.domain.aggregates.financials import Financials

# Infrastructure Layer components
from src.infrastructure.adapters.duckdb_adapter import DuckDBAdapter # To get concrete repos

class APSchedulerAdapter:
    def __init__(self,
                 duckdb_adapter: DuckDBAdapter,
                 external_api_adapter: IExternalAPI,
                 financials_aggregate_type: Type[Financials]):
        """
        Initializes the APSchedulerAdapter.

        Args:
            duckdb_adapter: Instance of DuckDBAdapter to access repositories.
            external_api_adapter: Instance of an IExternalAPI implementation.
            financials_aggregate_type: The class type of the Financials aggregate.
        """
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_listener(self.job_listener, EVENT_JOB_ERROR)
        
        self.duckdb_adapter = duckdb_adapter
        self.external_api_adapter = external_api_adapter
        self.financials_aggregate_type = financials_aggregate_type
        
        print("APSchedulerAdapter initialized.")

    def job_listener(self, event: JobExecutionEvent):
        """Listens for job execution errors and logs them."""
        if event.exception:
            print(f"Job {event.job_id} failed with exception: {event.exception}")
        else:
            print(f"Job {event.job_id} executed successfully (or event without exception).")


    async def schedule_daily_data_fetch(self, source_name: str, hour: int = 0, minute: int = 0):
        """
        Schedules a daily job to fetch data from a given source.
        """
        # Obtain necessary repositories from DuckDBAdapter
        # This logic might need to be more dynamic based on source_name
        prod_repo = None
        oil_repo = None
        ex_repo = None

        if source_name == "production_data":
            prod_repo = self.duckdb_adapter.get_production_repository()
        elif source_name == "oil_price":
            oil_repo = self.duckdb_adapter.get_oil_price_repository()
        elif source_name == "exchange_rate": # Assuming a source name for exchange rates
            ex_repo = self.duckdb_adapter.get_exchange_rate_repository()
        
        # Instantiate the use case with its dependencies
        # The ScheduleFetchDataUseCase expects specific repos or None
        use_case = ScheduleFetchDataUseCase(
            api_adapter=self.external_api_adapter,
            production_repo=prod_repo,
            oil_price_repo=oil_repo,
            exchange_rate_repo=ex_repo
        )
        
        job_id = f"fetch_{source_name}_daily"
        try:
            # APScheduler's add_job with async functions needs to be handled carefully.
            # If use_case.execute is an async def, it's fine.
            # If it's a synchronous def, APScheduler will run it in a thread pool.
            # Our current use cases are synchronous placeholders.
            self.scheduler.add_job(
                use_case.execute, 
                'cron', 
                args=[source_name], 
                hour=hour, 
                minute=minute, 
                id=job_id,
                replace_existing=True # Avoids error if job already exists (e.g. on app restart)
            )
            print(f"Job '{job_id}' scheduled daily at {hour:02d}:{minute:02d} for source '{source_name}'.")
        except Exception as e:
            print(f"Error scheduling job '{job_id}': {e}")


    async def schedule_daily_financial_computation(self, hour: int = 1, minute: int = 0):
        """
        Schedules a daily job to compute financial metrics.
        """
        # Obtain necessary repositories
        production_repo = self.duckdb_adapter.get_production_repository()
        oil_price_repo = self.duckdb_adapter.get_oil_price_repository()
        exchange_rate_repo = self.duckdb_adapter.get_exchange_rate_repository()
        
        # Instantiate the use case
        use_case = ScheduleComputeFinancialsUseCase(
            production_repo=production_repo,
            oil_price_repo=oil_price_repo,
            exchange_rate_repo=exchange_rate_repo,
            financials_aggregate_type=self.financials_aggregate_type
        )
        
        job_id = "compute_financials_daily"
        try:
            # Assuming use_case.execute is synchronous for now.
            # params for execute would be passed in args, e.g., args=[{"some_param": "value"}]
            self.scheduler.add_job(
                use_case.execute,
                'cron',
                args=[None], # Placeholder params for the use case's execute method
                hour=hour,
                minute=minute,
                id=job_id,
                replace_existing=True
            )
            print(f"Job '{job_id}' scheduled daily at {hour:02d}:{minute:02d}.")
        except Exception as e:
            print(f"Error scheduling job '{job_id}': {e}")

    async def start(self):
        """Starts the scheduler."""
        if not self.scheduler.running:
            try:
                self.scheduler.start()
                print("APScheduler started.")
            except Exception as e: # Catch potential issues like running in a non-async context if not careful
                print(f"Error starting APScheduler: {e}")
        else:
            print("APScheduler already running.")

    async def shutdown(self):
        """Shuts down the scheduler."""
        if self.scheduler.running:
            try:
                self.scheduler.shutdown()
                print("APScheduler shut down.")
            except Exception as e:
                print(f"Error shutting down APScheduler: {e}")

# Example of how to use (typically not here, but in main.py or similar)
# async def main():
#     # This is a conceptual example. Dependencies would be properly initialized.
#     # Mock or real adapters would be needed.
#     class MockDuckDBAdapter:
#         def get_production_repository(self): return None
#         def get_oil_price_repository(self): return None
#         def get_exchange_rate_repository(self): return None
#     class MockExternalApiAdapter: pass
# 
#     scheduler_adapter = APSchedulerAdapter(
#         duckdb_adapter=MockDuckDBAdapter(), # type: ignore
#         external_api_adapter=MockExternalApiAdapter(), # type: ignore
#         financials_aggregate_type=Financials 
#     )
#     await scheduler_adapter.schedule_daily_data_fetch(source_name="oil_price", hour=10, minute=30)
#     await scheduler_adapter.schedule_daily_financial_computation(hour=11, minute=0)
#     await scheduler_adapter.start()
#     try:
#         while True: # Keep alive for scheduler to run
#             await asyncio.sleep(10) # Use asyncio.sleep
#     except KeyboardInterrupt:
#         await scheduler_adapter.shutdown()
#
# if __name__ == "__main__":
#     import asyncio
#     # To run the example:
#     # asyncio.run(main()) # Python 3.7+
#     pass

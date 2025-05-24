import logging
from typing import Dict, Any, Type, Optional, List

from pydantic import ValidationError

from src.domain.interfaces.repository import (
    IProductionRepository, IOilPriceRepository, IExchangeRateRepository
)
from src.domain.services.data_service import DataService
from src.domain.aggregates.financials import Financials
from src.domain.entities.production import Production
from src.domain.entities.oil_price import OilPrice
from src.domain.entities.exchange_rate import ExchangeRate

class ScheduleComputeFinancialsUseCase:
    def __init__(self, 
                 production_repo: IProductionRepository, 
                 oil_price_repo: IOilPriceRepository,
                 exchange_rate_repo: IExchangeRateRepository,
                 data_service: DataService, # Added DataService
                 financials_aggregate_type: Type[Financials]
                 ):
        self.production_repo = production_repo
        self.oil_price_repo = oil_price_repo
        self.exchange_rate_repo = exchange_rate_repo
        self.data_service = data_service # Store DataService
        self.financials_aggregate_type = financials_aggregate_type
        self.logger = logging.getLogger(__name__)

    def execute(self, params: Optional[Dict[str, Any]] = None) -> None:
        """
        Computes financial metrics based on production, oil price, and exchange rates.
        
        Args:
            params: Optional dictionary for filtering data (not used in this iteration).
        """
        self.logger.info(f"Executing ScheduleComputeFinancialsUseCase with params: {params}")

        # Fetch all data
        production_data: List[Production] = []
        oil_price_data: List[OilPrice] = []
        exchange_rate_data: List[ExchangeRate] = []

        try:
            production_data = self.production_repo.list()
            if production_data is None: production_data = []
            self.logger.info(f"Fetched {len(production_data)} production records.")
        except Exception as e:
            self.logger.error(f"Error fetching production data: {e}", exc_info=True)
            return # Cannot proceed without production data

        if not production_data:
            self.logger.info("No production data available. Aborting financial computation.")
            return

        try:
            oil_price_data = self.oil_price_repo.list()
            if oil_price_data is None: oil_price_data = []
            self.logger.info(f"Fetched {len(oil_price_data)} oil price records.")
        except Exception as e:
            self.logger.error(f"Error fetching oil price data: {e}", exc_info=True)
            self.logger.warning("Proceeding without oil price data; some financial calculations may be skipped.")
            oil_price_data = []

        try:
            exchange_rate_data = self.exchange_rate_repo.list()
            if exchange_rate_data is None: exchange_rate_data = []
            self.logger.info(f"Fetched {len(exchange_rate_data)} exchange rate records.")
        except Exception as e:
            self.logger.error(f"Error fetching exchange rate data: {e}", exc_info=True)
            self.logger.warning("Proceeding without exchange rate data; some financial calculations may be skipped.")
            exchange_rate_data = []

        # Join data using DataService
        joined_data_list: List[Dict[str, Any]] = []
        try:
            joined_data_list = self.data_service.join_data(
                production_data, oil_price_data, exchange_rate_data
            )
            self.logger.info(f"DataService returned {len(joined_data_list)} joined records.")
        except Exception as e:
            self.logger.error(f"Error joining data using DataService: {e}", exc_info=True)
            return

        if not joined_data_list:
            self.logger.info("No data after joining. Aborting financial computation.")
            return

        # Process joined records
        successful_calculations = 0
        failed_entity_creations = 0
        failed_financial_calculations = 0

        for i, joined_record in enumerate(joined_data_list):
            prod_entity: Optional[Production] = None
            price_entity: Optional[OilPrice] = None
            exchange_entity: Optional[ExchangeRate] = None
            
            try:
                # Create Production entity (essential)
                # Pydantic models only take fields they know, so joined_record can be broad
                prod_entity = Production(**joined_record)
                
                # Create OilPrice entity (essential for Financials)
                # Check for presence of 'price' as it's key for OilPrice and might be missing after left join
                if 'price' not in joined_record or joined_record['price'] is None:
                    self.logger.debug(
                        f"Record {i+1} (Well: {prod_entity.well_code}, Date: {prod_entity.reference_date}): "
                        f"Missing 'price' data. Skipping financial calculation."
                    )
                    failed_entity_creations +=1
                    continue 
                price_entity = OilPrice(**joined_record)

                # Create ExchangeRate entity (essential for Financials)
                # Check for 'rate'
                if 'rate' not in joined_record or joined_record['rate'] is None:
                    self.logger.debug(
                        f"Record {i+1} (Well: {prod_entity.well_code}, Date: {prod_entity.reference_date}): "
                        f"Missing 'rate' data. Skipping financial calculation."
                    )
                    failed_entity_creations += 1
                    continue
                exchange_entity = ExchangeRate(**joined_record)

            except ValidationError as ve:
                self.logger.warning(
                    f"Record {i+1}: Validation error creating entities from joined record: {ve.errors()}. "
                    f"Record data: { {k:v for k,v in joined_record.items() if k in ['reference_date', 'well_code', 'price', 'rate']} }", # Log specific important fields
                    exc_info=False
                )
                failed_entity_creations += 1
                continue
            
            # All entities must be valid to proceed to Financials aggregate
            if not (prod_entity and price_entity and exchange_entity):
                 # This case should be caught by earlier checks if joined_record lacks price/rate
                 self.logger.warning(f"Record {i+1}: One or more essential entities could not be created. Skipping financial calculation.")
                 failed_entity_creations +=1 # Count it here if somehow not caught by specific checks
                 continue

            try:
                financial_calc = self.financials_aggregate_type(
                    production=prod_entity, 
                    oil_price=price_entity, 
                    exchange_rate=exchange_entity
                )
                revenue_usd = financial_calc.calculate_oil_revenue_usd()
                revenue_brl = financial_calc.calculate_oil_revenue_brl()
                
                self.logger.info(
                    f"Financials for Well: {prod_entity.well_code}, Date: {prod_entity.reference_date} - "
                    f"Oil Prod: {prod_entity.oil_prod}, Price USD: {price_entity.price}, Ex.Rate: {exchange_entity.rate} - "
                    f"Revenue USD: {revenue_usd:.2f}, Revenue BRL: {revenue_brl:.2f}"
                )
                successful_calculations += 1
            except Exception as e_calc:
                self.logger.error(
                    f"Error calculating financials for Well: {prod_entity.well_code}, Date: {prod_entity.reference_date}: {e_calc}", 
                    exc_info=True
                )
                failed_financial_calculations += 1
        
        total_processed_from_join = len(joined_data_list)
        self.logger.info(
            f"ScheduleComputeFinancialsUseCase finished. "
            f"Total joined records processed: {total_processed_from_join}. "
            f"Successfully calculated financials for: {successful_calculations} records. "
            f"Failed entity creations (missing price/rate or validation): {failed_entity_creations}. "
            f"Failed financial calculations (other errors): {failed_financial_calculations}."
        )

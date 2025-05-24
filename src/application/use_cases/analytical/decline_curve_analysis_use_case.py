# src/application/use_cases/analytical/decline_curve_analysis_use_case.py
from typing import List
import numpy as np
from datetime import date, timedelta

from src.domain.interfaces.repository import IProductionRepository, IWellRepository
from src.domain.services.dca_service import DCAService
from src.application.dtos.request.dca_request import DCARequest
from src.application.dtos.response.dca_response import DCAResponse
from src.core.exceptions import NotFoundError, ValueError # Assuming ValueError is a custom or core exception

class DeclineCurveAnalysisUseCase:
    def __init__(
        self, 
        production_repository: IProductionRepository, 
        dca_service: DCAService,
        well_repository: IWellRepository 
    ):
        self.production_repository = production_repository
        self.dca_service = dca_service
        self.well_repository = well_repository

    def execute(self, request: DCARequest) -> DCAResponse:
        # 1. Validate well existence
        well = self.well_repository.get_by_well_code(request.well_code)
        if not well:
            raise NotFoundError(f"Well with code {request.well_code} not found.")

        # 2. Fetch production data
        production_data = self.production_repository.find_by_well_code_and_date_range(
            well_code=request.well_code,
            start_date=request.start_date,
            end_date=request.end_date
        )

        if not production_data:
            raise ValueError("No production data available for the specified well and date range.")

        # Ensure data is sorted by date (repository should handle this, but double check)
        # Production data is already sorted by reference_date ASC by the repository method.

        # 3. Prepare data for DCA service
        if not production_data: # Should be caught by previous check, but as a safeguard
            raise ValueError("Production data list is empty after fetching.")

        first_prod_date: date = production_data[0].reference_date
        
        time_actual_days: List[float] = []
        rate_actual: List[float] = []

        for prod_entry in production_data:
            # Calculate days from the first production date
            time_delta_days = (prod_entry.reference_date - first_prod_date).days
            time_actual_days.append(float(time_delta_days))
            rate_actual.append(prod_entry.oil_prod)
            
        time_actual_np = np.array(time_actual_days)
        rate_actual_np = np.array(rate_actual)

        if len(time_actual_np) < 2: # Minimum points for any fit
             raise ValueError("Insufficient production data points for decline curve analysis (minimum 2 required).")
        if request.model_type.lower() == "hyperbolic" and len(time_actual_np) < 3:
             raise ValueError("At least three data points are recommended for hyperbolic fitting.")


        # 4. Call DCA service
        try:
            rate_fitted_np, time_forecast_np, rate_forecast_np, fitted_params_dict, rmse = \
                self.dca_service.fit_model_and_generate_forecast(
                    time_actual_np,
                    rate_actual_np,
                    request.model_type,
                    request.forecast_duration
                )
        except RuntimeError as e: # Catch fitting errors from DCAService
            raise ValueError(f"Error during decline curve fitting: {str(e)}")
        except ValueError as e: # Catch other value errors from DCAService (e.g. insufficient data)
            raise ValueError(str(e))


        # 5. Populate and return DCAResponse
        return DCAResponse(
            well_code=request.well_code,
            model_type=request.model_type,
            time_actual=time_actual_np.tolist(),
            rate_actual=rate_actual_np.tolist(),
            time_fitted=time_actual_np.tolist(), # Fitted time is same as actual time
            rate_fitted=rate_fitted_np.tolist(),
            time_forecast=time_forecast_np.tolist(),
            rate_forecast=rate_forecast_np.tolist(),
            parameters=fitted_params_dict,
            rmse=rmse
        )

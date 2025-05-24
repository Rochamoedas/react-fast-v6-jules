# src/domain/services/dca_service.py
import numpy as np
from scipy.optimize import curve_fit
from typing import Tuple, Callable, Dict, List
import math

class DCAService:
    """
    Provides services for Decline Curve Analysis (DCA).
    """

    @staticmethod
    def _exponential_decline(t: np.ndarray, qi: float, Di: float) -> np.ndarray:
        """
        Exponential decline curve equation.
        q(t) = qi * exp(-Di * t)
        Di should be in per-day units if t is in days.
        """
        return qi * np.exp(-Di * t)

    @staticmethod
    def _hyperbolic_decline(t: np.ndarray, qi: float, Di: float, b: float) -> np.ndarray:
        """
        Hyperbolic decline curve equation.
        q(t) = qi / (1 + b * Di * t)^(1/b)
        Di should be in per-day units if t is in days.
        b must be > 0. For b=0, it's exponential. For b=1, it's harmonic.
        """
        # Ensure b is not exactly zero to avoid division by zero in the exponent.
        # Small positive b values can be handled.
        # If b is very close to 0, hyperbolic approaches exponential.
        # scipy.optimize.curve_fit might struggle if b is too small or bounds are not set.
        if b == 0: # Theoretical limit to exponential
            return DCAService._exponential_decline(t, qi, Di)
        return qi / np.power((1 + b * Di * t), (1 / b))

    def fit_exponential(self, time_data: np.ndarray, rate_data: np.ndarray) -> Tuple[float, float]:
        """
        Fits an exponential decline model to the provided time and rate data.
        Returns:
            Tuple[float, float]: (qi, Di) - initial rate, initial decline rate (per unit of time_data).
        Raises:
            RuntimeError: If optimal parameters not found.
        """
        if len(time_data) < 2 or len(rate_data) < 2:
            raise ValueError("At least two data points are required for fitting.")
        
        # Initial guesses: qi from the first data point, Di can be a small positive value.
        # Bounds can help guide the optimizer.
        initial_qi = rate_data[0] if rate_data[0] > 0 else np.mean(rate_data)
        if initial_qi <=0: initial_qi = 1.0 # Ensure positive initial guess

        p0 = [initial_qi, 0.001] # Initial guess for [qi, Di]
        bounds = ([0, 0], [np.inf, np.inf]) # qi > 0, Di > 0

        try:
            params, _ = curve_fit(self._exponential_decline, time_data, rate_data, p0=p0, bounds=bounds)
            return params[0], params[1]
        except RuntimeError as e:
            raise RuntimeError(f"Exponential curve_fit failed to find optimal parameters: {e}")

    def fit_hyperbolic(self, time_data: np.ndarray, rate_data: np.ndarray) -> Tuple[float, float, float]:
        """
        Fits a hyperbolic decline model to the provided time and rate data.
        Returns:
            Tuple[float, float, float]: (qi, Di, b) - initial rate, initial decline rate, b-exponent.
        Raises:
            RuntimeError: If optimal parameters not found.
        """
        if len(time_data) < 3: # Hyperbolic typically needs more points than exponential
            raise ValueError("At least three data points are recommended for hyperbolic fitting.")

        initial_qi = rate_data[0] if rate_data[0] > 0 else np.mean(rate_data)
        if initial_qi <=0: initial_qi = 1.0

        # Initial guesses and bounds
        # b typically between 0 and 2. Di > 0.
        p0 = [initial_qi, 0.001, 0.5]  # Initial guess for [qi, Di, b]
        # Bounds: qi > 0, Di > 0, 0 < b <= 2 (common practical range for b)
        bounds = ([0, 0, 1e-6], [np.inf, np.inf, 2.0]) 

        try:
            params, _ = curve_fit(self._hyperbolic_decline, time_data, rate_data, p0=p0, bounds=bounds, maxfev=5000)
            return params[0], params[1], params[2]
        except RuntimeError as e:
            raise RuntimeError(f"Hyperbolic curve_fit failed to find optimal parameters: {e}")

    def generate_rates(self, decline_func: Callable, time_points: np.ndarray, params: Dict[str, float]) -> np.ndarray:
        """
        Generates rates using the provided decline function, time points, and parameters.
        """
        if decline_func == self._exponential_decline:
            return self._exponential_decline(time_points, params['qi'], params['Di'])
        elif decline_func == self._hyperbolic_decline:
            return self._hyperbolic_decline(time_points, params['qi'], params['Di'], params['b'])
        else:
            raise ValueError("Unsupported decline function provided.")

    @staticmethod
    def calculate_rmse(actual_rates: np.ndarray, fitted_rates: np.ndarray) -> float:
        """
        Calculates the Root Mean Squared Error (RMSE) between actual and fitted rates.
        """
        if len(actual_rates) != len(fitted_rates):
            raise ValueError("Actual and fitted rates arrays must have the same length.")
        if len(actual_rates) == 0:
            return 0.0
        return np.sqrt(np.mean((actual_rates - fitted_rates)**2))

    def get_decline_function_and_param_names(self, model_type: str) -> Tuple[Callable, List[str]]:
        """
        Returns the decline function and its parameter names based on model_type.
        """
        if model_type.lower() == "exponential":
            return self._exponential_decline, ['qi', 'Di']
        elif model_type.lower() == "hyperbolic":
            return self._hyperbolic_decline, ['qi', 'Di', 'b']
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

    def fit_model_and_generate_forecast(
        self, 
        time_actual_np: np.ndarray, 
        rate_actual_np: np.ndarray, 
        model_type: str, 
        forecast_duration: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, float], float]:
        """
        Fits the specified model, generates fitted rates for actual period, 
        and forecasts rates for the future.
        
        Returns:
            Tuple containing:
            - rate_fitted_np: np.ndarray
            - time_forecast_np: np.ndarray
            - rate_forecast_np: np.ndarray
            - fitted_params_dict: Dict[str, float]
            - rmse: float
        """
        parameters: Tuple
        decline_func: Callable
        param_names: List[str]

        if model_type.lower() == "exponential":
            decline_func, param_names = self._exponential_decline, ['qi', 'Di']
            qi, Di = self.fit_exponential(time_actual_np, rate_actual_np)
            parameters = (qi, Di)
        elif model_type.lower() == "hyperbolic":
            decline_func, param_names = self._hyperbolic_decline, ['qi', 'Di', 'b']
            qi, Di, b = self.fit_hyperbolic(time_actual_np, rate_actual_np)
            parameters = (qi, Di, b)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        fitted_params_dict = dict(zip(param_names, parameters))

        # Generate fitted rates for the actual period
        rate_fitted_np = self.generate_rates(decline_func, time_actual_np, fitted_params_dict)

        # Calculate RMSE
        rmse = self.calculate_rmse(rate_actual_np, rate_fitted_np)

        # Generate forecast
        # Forecast time starts from the end of actual time for forecast_duration days
        last_actual_time = time_actual_np[-1] if len(time_actual_np) > 0 else 0
        # Create forecast time points (e.g., daily for forecast_duration)
        # If time_actual_np represents days, then forecast_time_points also in days
        forecast_time_points = np.arange(last_actual_time + 1, last_actual_time + 1 + forecast_duration) 
        
        # The decline functions expect time relative to the start of the decline (t=0 for qi).
        # So, for forecasting, we pass these absolute time values directly.
        rate_forecast_np = self.generate_rates(decline_func, forecast_time_points, fitted_params_dict)
        
        return rate_fitted_np, forecast_time_points, rate_forecast_np, fitted_params_dict, rmse

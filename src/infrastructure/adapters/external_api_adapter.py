# src/infrastructure/adapters/external_api_adapter.py
import requests
import logging # Added
from typing import Dict, Any, Optional, List

from src.domain.interfaces.external_api import IExternalAPI
from src.config import (
    OIL_PRICE_API_URL, OIL_PRICE_API_KEY,
    EXCHANGE_RATE_API_URL,
    PRODUCTION_DATA_API_URL, PRODUCTION_API_KEY,
    ODATA_PRODUCTION_DATA_API_URL, ODATA_API_USERNAME, ODATA_API_PASSWORD # Added for OData
)
from src.core.exceptions import AppException # Added

logger = logging.getLogger(__name__) # Added

# Updated Custom Exception
class ExternalApiError(AppException): # Inherits from AppException
    """Custom exception for external API related errors."""
    def __init__(self, message: str, status_code: int = 503, detail: str = None): # type: ignore
        super().__init__(message, status_code, detail)


class ExternalApiAdapter(IExternalAPI):
    """
    Adapter for fetching data from external APIs.
    """
    _api_configs: Dict[str, Dict[str, Optional[str]]]

    def __init__(self):
        """
        Initializes the adapter by loading API configurations.
        """
        self._api_configs = {
            "oil_price": {
                "url": OIL_PRICE_API_URL,
                "key": OIL_PRICE_API_KEY,
                "key_header_template": "Bearer {}" 
            },
            "exchange_rate": {
                "url": EXCHANGE_RATE_API_URL,
                "key": None, 
                "key_header_template": None
            },
            "production_data": {
                "url": PRODUCTION_DATA_API_URL,
                "key": PRODUCTION_API_KEY,
                "key_header_template": "X-API-Key {}"
            },
            "odata_production_data": { # Added OData config
                "url": ODATA_PRODUCTION_DATA_API_URL,
                "username": ODATA_API_USERNAME,
                "password": ODATA_API_PASSWORD,
                "auth_type": "basic",
                "key": None, # Ensure key-based auth is not attempted
                "key_header_template": None
            }
        }
        logger.info("ExternalApiAdapter initialized.")


    def fetch_data(self, source_name: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if source_name not in self._api_configs:
            logger.error(f"Unknown data source requested: {source_name}")
            raise ValueError(f"Unknown data source: {source_name}") # Or an AppException

        config = self._api_configs[source_name]
        url = config.get("url")
        api_key = config.get("key")
        key_header_template = config.get("key_header_template")
        auth_type = config.get("auth_type")
        username = config.get("username")
        password = config.get("password")

        if not url or ("YOUR_" in url.upper() and source_name != "odata_production_data") : # Simplified placeholder check, adjusted for OData
            logger.error(f"API URL for '{source_name}' is not configured or is a placeholder: {url}")
            raise ExternalApiError(
                message=f"API URL for '{source_name}' is not configured correctly.",
                detail="The URL is either missing or still contains placeholder values."
            )

        headers = {"Accept": "application/json"}
        auth_args = None

        if auth_type == "basic":
            if not username or not password or "YOUR_" in username.upper() or "YOUR_" in password.upper():
                error_msg = f"Username or password for Basic Auth in '{source_name}' is missing or is a placeholder."
                logger.error(error_msg)
                raise ExternalApiError(message=error_msg, detail="Ensure username and password are configured correctly.")
            auth_args = requests.auth.HTTPBasicAuth(username, password)
            logger.debug(f"Using HTTP Basic Authentication for '{source_name}'.")
        elif api_key and "YOUR_" not in api_key.upper(): # Process API key if not basic auth and key exists
            if key_header_template:
                if "{}" in key_header_template:
                    auth_value = key_header_template.format(api_key)
                    auth_header_name = "Authorization" if "Bearer" in key_header_template else key_header_template.split(" ")[0]
                    headers[auth_header_name] = auth_value
                else: # Template is the header name, value is the key
                    headers[key_header_template] = api_key
            else: # Default to Bearer token if no template
                headers["Authorization"] = f"Bearer {api_key}"
        
        logger.debug(f"Fetching data from {url} for source '{source_name}' with params {params}")
        try:
            response = requests.get(url, params=params, headers=headers, auth=auth_args, timeout=10)
            response.raise_for_status()
            json_response = response.json()

            if isinstance(json_response, list):
                return json_response
            elif isinstance(json_response, dict):
                for key in ["data", "results", "items", "records"]:
                    if key in json_response and isinstance(json_response[key], list):
                        return json_response[key]
                logger.warning(f"API response for '{source_name}' was a dict but not in expected list format. Keys: {list(json_response.keys())}")
                raise ExternalApiError(f"API response for '{source_name}' was a dictionary but not in expected list format.")
            else:
                logger.warning(f"API response for '{source_name}' is not a list or recognizable dict structure. Type: {type(json_response)}")
                raise ExternalApiError(f"API response for '{source_name}' is not a list or recognizable dictionary structure.")

        except requests.exceptions.HTTPError as http_err:
            error_message = f"API request to '{source_name}' failed with status {http_err.response.status_code}: {http_err.response.text[:200]}"
            logger.error(error_message, exc_info=True)
            raise ExternalApiError(message=error_message, status_code=http_err.response.status_code) from http_err
        except requests.exceptions.Timeout as timeout_err:
            error_message = f"API request to '{source_name}' timed out: {timeout_err}"
            logger.error(error_message, exc_info=True)
            raise ExternalApiError(message=error_message, status_code=504) from timeout_err
        except requests.exceptions.ConnectionError as conn_err:
            error_message = f"API request to '{source_name}' failed due to connection error: {conn_err}"
            logger.error(error_message, exc_info=True)
            raise ExternalApiError(message=error_message, status_code=503) from conn_err
        except requests.exceptions.JSONDecodeError as json_err:
            error_message = f"Failed to decode JSON response from '{source_name}': {json_err}. Response text: {response.text[:200]}..."
            logger.error(error_message, exc_info=True)
            raise ExternalApiError(message=error_message, status_code=502) from json_err
        except requests.exceptions.RequestException as req_err:
            error_message = f"An unexpected error occurred with API request to '{source_name}': {req_err}"
            logger.error(error_message, exc_info=True)
            raise ExternalApiError(message=error_message) from req_err

    def fetch_production_data_monthly(self, year: int, month: int, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetches monthly production data from the OData source for a specific year and month.

        Args:
            year: The year for which to fetch data.
            month: The month (1-12) for which to fetch data.
            params: Optional dictionary of additional parameters to pass to the API.

        Returns:
            A list of dictionaries, where each dictionary represents a data record.
        """
        logger.info(f"Fetching monthly production data for {year:04d}-{month:02d} from OData source.")

        request_params: Dict[str, Any] = {"year": year, "month": month}
        
        # OData specific filtering might look like:
        # request_params["$filter"] = f"year eq {year} and month eq {month}"
        # For now, we'll assume the API can take year/month directly or they are handled by generic 'params'

        if params:
            request_params.update(params)

        try:
            data = self.fetch_data("odata_production_data", params=request_params)
            logger.info(f"Successfully fetched {len(data)} records for {year:04d}-{month:02d}.")
            return data
        except ExternalApiError as e:
            logger.error(f"Failed to fetch monthly production data for {year:04d}-{month:02d}: {e.detail or e.message}", exc_info=True)
            # Re-raise the exception to be handled by the caller
            raise
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"An unexpected error occurred while fetching monthly production data for {year:04d}-{month:02d}: {e}", exc_info=True)
            raise ExternalApiError(
                message=f"An unexpected error occurred while fetching data for {year:04d}-{month:02d}.",
                detail=str(e)
            )


if __name__ == "__main__":
    # Basic logging setup for standalone testing of this module
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("ExternalApiAdapter Demo")
    adapter = ExternalApiAdapter()

    logger.info("\n--- Test Case 1: Unknown Source ---")
    try:
        adapter.fetch_data("non_existent_source")
    except ValueError as e:
        logger.info(f"Caught expected error: {e}")
    except ExternalApiError as e: 
        logger.info(f"Caught expected error due to placeholder URL: {e}")


    logger.info("\n--- Test Case 2: Known Source (expecting ExternalApiError due to placeholder URL) ---")
    try:
        data = adapter.fetch_data("exchange_rate", params={"base": "USD", "symbols": "BRL"})
        logger.info(f"Fetched data for exchange_rate: {data}")
    except ExternalApiError as e:
        logger.info(f"Caught expected error: {e}")
    except ValueError as e: 
        logger.info(f"Caught unexpected ValueError: {e}")

    logger.info("\nDemo finished. Note: Most tests will raise errors due to placeholder API configurations.")

from app.adapters.http_adapters.http_client import HttpClient
from dotenv import load_dotenv
import os
from app.application.use_cases.fetch_external_data import FetchExternalDataUseCase
from app.application.use_cases.get_greeting import GetGreetingUseCase
from app.application.use_cases.fetch_odata_data import FetchODataDataUseCase
from app.adapters.api_clients.odata_api_client import ODataAPIClient
from app.adapters.api_clients.new_odata_api_client import NewODataAPIClient
from app.domain.interfaces.http_interfaces.external_service import ExternalServiceInterface
from app.infrastructure.database.o_data_repository import DuckDBODataRepository

class DIContainer:
    """Simple dependency injection container."""
    
    def __init__(self):
        load_dotenv()  # Load environment variables from .env file
        self._services = {}
        self._register_services()

    def _register_services(self):
        # Register adapters
        # Register the interface implementation
        odata_url = os.getenv("ODATA_WM_LDI_URL")
        username = os.getenv("CREDENTIALS_USERNAME")
        password = os.getenv("CREDENTIALS_PASSWORD")

        if not all([odata_url, username, password]):
            raise ValueError("ODATA_WM_LDI_URL, CREDENTIALS_USERNAME, and CREDENTIALS_PASSWORD must be set as environment variables.")

        self._services[ExternalServiceInterface] = ODataAPIClient(  # Use the concrete client that implements the interface
            base_url=odata_url,
            username=username,
            password=password
        )
        
        # Register concrete clients if needed separately
        self._services[ODataAPIClient] = ODataAPIClient(
            base_url=odata_url,
            username=username,
            password=password
        )
        
        self._services[NewODataAPIClient] = NewODataAPIClient(
            url=odata_url,
            username=username,
            password=password
        )
        
        # Register the DuckDBODataRepository
        self._services[DuckDBODataRepository] = DuckDBODataRepository()
        
        # Register use cases
        self._services[GetGreetingUseCase] = GetGreetingUseCase()
        self._services[FetchExternalDataUseCase] = FetchExternalDataUseCase(
            external_service=self.get(ExternalServiceInterface)
        )
        self._services[FetchODataDataUseCase] = FetchODataDataUseCase(
            api_client=self.get(ExternalServiceInterface),
            odata_repository=self.get(DuckDBODataRepository)  # Inject the DuckDBODataRepository
        )
    
    def get(self, service_type):
        """Get a service from the container."""
        return self._services.get(service_type)

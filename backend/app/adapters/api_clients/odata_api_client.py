from typing import Any, Dict
import requests
from app.adapters.api_clients.base_odata_api_client import BaseODataAPIClient

class ODataAPIClient(BaseODataAPIClient):
    """OData API client that implements the ExternalServiceInterface via BaseODataAPIClient."""
    
    def __init__(self, base_url: str, username: str, password: str):
        """Initialize the OData API client.
        
        Args:
            base_url: The base URL for the OData API.
            username: The username for authentication.
            password: The password for authentication.
        """
        super().__init__(url=base_url, username=username, password=password)
        self.base_url = base_url
    
    async def fetch_data(self, endpoint: str = None) -> Dict[str, Any]:
        """Fetch data from the OData API.
        
        Args:
            endpoint: The full URL to fetch data from.
            
        Returns:
            The JSON response from the API.
        """
        try:
            # Use the endpoint as the full URL directly, or fall back to base_url if None
            url = endpoint if endpoint else self.base_url
                
            # Use the base class implementation to make the request
            response = await super().fetch_data(url)
            
            # Check if response content is empty before returning JSON
            if response is None or response == '':
                raise ValueError("Empty response content")
            
            return response
        except Exception as e:
            import traceback
            print(f"Error in fetch_data: {e}")
            traceback.print_exc()
            raise

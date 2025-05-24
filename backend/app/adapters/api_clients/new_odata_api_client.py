import requests
from typing import Any, Dict
import asyncio
from app.adapters.api_clients.base_odata_api_client import BaseODataAPIClient

class NewODataAPIClient(BaseODataAPIClient):
    """New OData API client that implements the ExternalServiceInterface via BaseODataAPIClient."""
    
    def __init__(self, url: str, username: str, password: str):
        """Initialize the OData API client.
        
        Args:
            url: The URL for the OData API.
            username: The username for authentication.
            password: The password for authentication.
        """
        print(f"[NewODataAPIClient.__init__] Initializing with url={url}, username={username}, password={password}")
        super().__init__(url=url, username=username, password=password)
    
    async def fetch_data(self, endpoint: str = None) -> Dict[str, Any]:
        """Fetch data from the OData API asynchronously.
        
        Args:
            endpoint: The endpoint to fetch data from. Currently not used.
            
        Returns:
            The JSON response from the API.
        """
        try:
            url = self.url
            print(f"[NewODataAPIClient.fetch_data] Called with url={url}, endpoint={endpoint}")
            print(f"[NewODataAPIClient.fetch_data] Fetching data from url={url} with username={self.username} and password={self.password}")
            
            # Use the base class implementation to make the request
            response = await super()._make_request(url)
            
            print(f"[NewODataAPIClient.fetch_data] Response status_code={response.status_code}")
            json_data = response.json()
            print(f"[NewODataAPIClient.fetch_data] Response JSON: {str(json_data)[:500]}")
            return json_data
        except Exception as e:
            print(f"[NewODataAPIClient.fetch_data] Could not decode JSON: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    # For backward compatibility with synchronous code
    def fetch_data_sync(self, endpoint: str = None):
        """Fetch data from the OData API synchronously.
        
        This method is provided for backward compatibility with code that expects
        a synchronous fetch_data method. It wraps the asynchronous fetch_data method.
        
        Args:
            endpoint: The endpoint to fetch data from. Currently not used.
            
        Returns:
            The response object from the API.
        """
        try:
            url = self.url
            print(f"[NewODataAPIClient.fetch_data_sync] Called with url={url}, endpoint={endpoint}")
            print(f"[NewODataAPIClient.fetch_data_sync] Fetching data from url={url} with username={self.username} and password={self.password}")
            
            # Make the request synchronously
            response = requests.get(url, auth=requests.auth.HTTPBasicAuth(self.username, self.password))
            print(f"[NewODataAPIClient.fetch_data_sync] Response status_code={response.status_code}")
            print(f"[NewODataAPIClient.fetch_data_sync] Response JSON: {response.json()}")
            response.raise_for_status()
            return response
        except Exception as e:
            import traceback
            print(f"[NewODataAPIClient.fetch_data_sync] Error: {e}")
            traceback.print_exc()
            raise

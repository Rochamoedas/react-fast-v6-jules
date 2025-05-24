from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import requests
from requests.auth import HTTPBasicAuth
import os
import asyncio
from app.domain.interfaces.http_interfaces.external_service import ExternalServiceInterface


class BaseODataAPIClient(ExternalServiceInterface, ABC):
    """Base class for OData API clients that implements common functionality."""
    
    def __init__(self, url: str, username: str, password: str):
        """Initialize the OData API client.
        
        Args:
            url: The base URL for the OData API.
            username: The username for authentication.
            password: The password for authentication.
        """
        self.url = url
        self.username = username
        self.password = password
    
    async def fetch_data(self, url: str = None) -> Dict[str, Any]:
        """Fetch data from the OData API.
        
        Args:
            url: The URL to fetch data from. If None, will use the base URL.
            
        Returns:
            The JSON response from the API.
        """
        # Use the provided URL or fall back to the base URL
        request_url = url if url else self.url
        
        # Make the request
        response = await self._make_request(request_url)
        
        # Return the JSON response
        return response.json()
    
    async def _make_request(self, url: str):
        """Make a request to the OData API asynchronously.
        
        This method uses a thread pool to run the synchronous requests.get
        in a separate thread to avoid blocking the event loop.
        
        Args:
            url: The URL to make the request to.
            
        Returns:
            The response from the API.
        """
        # Create the auth object
        auth = HTTPBasicAuth(self.username, self.password)
        
        # Run the synchronous request in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.get(url, auth=auth)
        )
        
        response.raise_for_status()  # Raise an error for bad responses
        
        return response

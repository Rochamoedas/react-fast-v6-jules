import logging
import requests
from requests.exceptions import RequestException
from .base_fetch_data import BaseFetchDataUseCase
from app.domain.interfaces.http_interfaces.external_service import ExternalServiceInterface
from app.infrastructure.database.o_data_repository import DuckDBODataRepository
import asyncio


class FetchODataDataUseCase(BaseFetchDataUseCase):
    def __init__(self, api_client: ExternalServiceInterface, odata_repository: DuckDBODataRepository, *args, **kwargs):
        super().__init__(api_client, *args, **kwargs)
        self.odata_repository = odata_repository
        print("[FetchODataDataUseCase.__init__] Initializing FetchODataDataUseCase")

    async def execute(self, endpoint: str = None):  # Default endpoint removed to avoid duplication
        print(f"[FetchODataDataUseCase.execute] Called with endpoint={endpoint}")
        all_data = []
        iteration = 0
        max_iterations = 2

        while iteration < max_iterations:
            # Check if the api_client has a fetch_data_sync method (for backward compatibility)
            if hasattr(self.api_client, 'fetch_data_sync'):
                response = self.api_client.fetch_data_sync(endpoint) if endpoint else self.api_client.fetch_data_sync()
            else:
                # If the api_client doesn't have a fetch_data_sync method, use the async fetch_data method
                response = await self.api_client.fetch_data(endpoint) if endpoint else await self.api_client.fetch_data()
            print(f"[FetchODataDataUseCase.execute] Response object: {response}")
            try:
                data = response
                print(f"[FetchODataDataUseCase.execute] Response data: {data}")
                all_data.extend(data.get('value', []))
                endpoint = data.get('@odata.nextLink')
            except Exception as e:
                print(f"[FetchODataDataUseCase.execute] Could not process response: {e}")
                break
            iteration += 1

        processed_data = self.process_data(all_data)
        print(f"[FetchODataDataUseCase.execute] Processed data: {processed_data}")
        # Save only the 'value' part of the response data to avoid encoding issues
        self.odata_repository.save(processed_data)
        return processed_data

    def process_data(self, data):
        print(f"[FetchODataDataUseCase.process_data] Called with data: {data}")
        import polars as pl
        # Convert the data to a Polars DataFrame
        df = pl.DataFrame(data, strict=False)
        print(f"[FetchODataDataUseCase.process_data] Polars DataFrame: {df}")
        # Convert the DataFrame to a list of dictionaries
        processed_data = df.to_dicts()
        print(f"[FetchODataDataUseCase.process_data] Processed data: {processed_data}")
        return processed_data

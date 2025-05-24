import os
from fastapi import APIRouter, Depends, HTTPException
from app.application.use_cases.fetch_odata_data import FetchODataDataUseCase
from app.adapters.api_clients.new_odata_api_client import NewODataAPIClient

from app.application.dtos.external_data_dto import ExternalDataError, ExternalDataResponse
from app.application.use_cases.fetch_external_data import FetchExternalDataUseCase
from app.infrastructure.di.container import DIContainer


class ExternalDataController:
    """Controller for external data-related endpoints."""
    
    def __init__(self, container: DIContainer):
        self.router = APIRouter()
        self.container = container
        self._configure_routes()
    
    def _configure_routes(self):
        # Only keep the /external/cats route as requested
        self.router.add_api_route("/external/cats", self.get_external_cats_data, methods=["GET"])
    
    async def get_external_cats_data(self):
        url = os.getenv("EXTERNAL_TEST_API_URL")
        if url is None:
            raise HTTPException(status_code=400, detail="EXTERNAL_TEST_API_URL environment variable is not set")
        use_case = self.container.get(FetchExternalDataUseCase)
        result = await use_case.execute(url)
        if isinstance(result, ExternalDataError):
            return {"error": result.error, "content": result.content if hasattr(result, 'content') else None}
        return result.data

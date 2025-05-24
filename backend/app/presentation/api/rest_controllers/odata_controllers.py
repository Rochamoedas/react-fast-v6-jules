from fastapi import APIRouter, Depends, HTTPException
from app.application.use_cases.fetch_odata_data import FetchODataDataUseCase
from app.infrastructure.di.container import DIContainer
import logging

class ODataController:
    """Controller for odata-related endpoints."""

    def __init__(self, container: DIContainer):
        self.router = APIRouter()
        self.container = container
        self._configure_routes()

    def _configure_routes(self):
        self.router.add_api_route("/odata_query", self.odata_test, methods=["GET"])

    async def odata_test(self):
        print("[odata_test] /odata_test endpoint called")
        try:
            fetch_data_use_case = self.container.get(FetchODataDataUseCase)
            processed_data = await fetch_data_use_case.execute()
            print(f"[odata_test] Data processed and saved successfully: {processed_data}")
            return {"message": "Data processed and saved successfully", "data": processed_data}
        except Exception as e:
            print(f"[odata_test] Error processing OData: {e}")
            logging.error(f"Error processing OData: {e}")
            raise HTTPException(status_code=500, detail="Failed to process OData")

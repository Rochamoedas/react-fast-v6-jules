from fastapi import FastAPI

from app.infrastructure.di.container import DIContainer
from app.presentation.api.rest_controllers.external_data_controller import ExternalDataController
from app.presentation.api.rest_controllers.odata_controllers import ODataController
from app.presentation.api.rest_controllers.greeting_controller import GreetingController


def setup_api(app: FastAPI, container: DIContainer):
    """Configure the FastAPI application with all controllers."""
    # Initialize controllers
    greeting_controller = GreetingController(container)
    external_data_controller = ExternalDataController(container)
    odata_controller = ODataController(container)

    # Include routers
    app.include_router(greeting_controller.router, tags=["greetings"])
    app.include_router(external_data_controller.router, tags=["testing_endpoints"])
    app.include_router(odata_controller.router, tags=["odata_ldi_query"])

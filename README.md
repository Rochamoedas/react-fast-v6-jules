# Oil & Gas Data API

## Project Overview

This project provides a FastAPI-based backend API designed for managing and analyzing oil and gas exploration and production (E&P) data. It allows users to perform CRUD (Create, Read, Update, Delete) operations on key E&P entities and offers analytical capabilities to process and gain insights from this data.

The system is structured with a layered architecture, separating concerns into domain logic, application services, and infrastructure components. It uses DuckDB for local data storage and is designed to potentially integrate with external APIs for fetching data like oil prices and exchange rates. Scheduled tasks via APScheduler are also incorporated for regular data updates and computations.

## Purpose

The primary purposes of this API are:

*   **Data Management:** To serve as a centralized repository for various E&P data points, including:
    *   Well information (metadata, status, location)
    *   Field details
    *   Daily/periodic production volumes (oil, gas, water)
    *   Oil price information
    *   Currency exchange rates
*   **Data Access:** To provide a standardized interface for clients to retrieve and modify this data through a RESTful API.
*   **Data Analysis:** To offer analytical endpoints that allow for:
    *   Filtering production data based on various criteria.
    *   Aggregating production data (e.g., sums, averages by well or field).
    *   Joining different datasets (e.g., combining production data with financial information like prices and exchange rates) to derive valuable insights.
*   **Automation:** To automate routine tasks such as fetching updated data from external sources and performing periodic calculations (e.g., financial summaries).

This API is intended for developers building applications for the oil and gas industry, data analysts requiring programmatic access to E&P data, or any system needing to integrate with such datasets.

## Project Structure

The project is organized into the following main directories and files:

```
├── data/                     # (Intended for) Local data storage, e.g., DuckDB file (not in repo by default)
├── requirements.txt          # Python package dependencies
├── src/                      # Main source code directory
│   ├── __init__.py
│   ├── application/          # Application layer: use cases and DTOs
│   │   ├── __init__.py
│   │   ├── dtos/             # Data Transfer Objects (request/response models)
│   │   │   ├── __init__.py
│   │   │   ├── request/
│   │   │   └── response/
│   │   └── use_cases/        # Application logic and orchestration
│   │       ├── __init__.py
│   │       ├── analytical/   # Use cases for data analysis
│   │       ├── crud/         # Use cases for CRUD operations
│   │       └── scheduling/   # Use cases for scheduled tasks
│   ├── core/                 # Core components like custom exceptions
│   │   ├── __init__.py
│   │   └── exceptions.py
│   ├── domain/               # Domain layer: entities, value objects, repository interfaces, domain services
│   │   ├── __init__.py
│   │   ├── aggregates/       # Domain aggregates (e.g., Financials)
│   │   ├── entities/         # Domain entities (e.g., Well, Production)
│   │   ├── interfaces/       # Abstract interfaces (e.g., IWellRepository, IExternalAPI)
│   │   ├── services/         # Domain services (e.g., DataService)
│   │   └── value_objects/    # Domain value objects
│   ├── infrastructure/       # Infrastructure layer: adapters for external concerns
│   │   ├── __init__.py
│   │   └── adapters/         # Concrete implementations for DB, external APIs, scheduler
│   │       ├── __init__.py
│   │       ├── apscheduler_adapter.py
│   │       ├── duckdb_adapter.py
│   │       └── external_api_adapter.py
│   ├── logging_config.py     # Logging setup
│   └── main.py               # FastAPI application entry point, API routers, dependency injection
└── ... (other project files like .gitignore, etc.)
```

### Key File Descriptions:

*   **`src/main.py`**:
    *   Initializes the FastAPI application.
    *   Defines API routers and endpoints.
    *   Manages dependency injection for use cases and repositories.
    *   Handles application startup and shutdown events (e.g., initializing database, scheduler).
*   **`src/config.py`**:
    *   Contains application settings, including placeholders for API URLs, keys, database paths, and data schemas.
*   **`src/logging_config.py`**:
    *   Configures application-wide logging.
*   **`src/core/exceptions.py`**:
    *   Defines custom application-specific exceptions.
*   **`src/domain/entities/`**:
    *   Contains Pydantic models representing the core business objects (e.g., `Well`, `Field`, `Production`).
*   **`src/domain/interfaces/`**:
    *   Defines abstract interfaces for repositories and external services, promoting loose coupling.
*   **`src/domain/services/data_service.py`**:
    *   Provides domain-specific logic for data manipulation like filtering, aggregation, and joining, currently utilizing Polars for performance.
*   **`src/application/dtos/`**:
    *   Holds Pydantic models used for API request and response validation and serialization.
*   **`src/application/use_cases/`**:
    *   Contains classes that orchestrate actions and business logic for specific operations (e.g., creating a well, filtering production data).
*   **`src/infrastructure/adapters/`**:
    *   Provides concrete implementations for interacting with external systems:
        *   `duckdb_adapter.py`: Manages database connections, schema initialization, and provides repository implementations for DuckDB.
        *   `external_api_adapter.py`: (Intended to) handle communication with third-party APIs for data fetching.
        *   `apscheduler_adapter.py`: Manages scheduled tasks within the application.
*   **`requirements.txt`**:
    *   Lists all Python dependencies required to run the project.

## Setup and Running the Application

Follow these steps to set up and run the Oil & Gas Data API locally:

### 1. Prerequisites

*   Python 3.8 or higher
*   Pip (Python package installer)
*   (Optional) Git for cloning the repository

### 2. Clone the Repository (Optional)

If you have Git, clone the repository:
```bash
git clone <repository_url> # Replace <repository_url> with the actual URL
cd <repository_directory>
```
Alternatively, download and extract the source code.

### 3. Create a Virtual Environment (Recommended)

It's highly recommended to use a virtual environment to manage project dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scriptsctivate
```

### 4. Install Dependencies

Install the required Python packages using `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 5. Configure the Application

The main configuration file is `src/config.py`. You **must** update placeholder values for the application to function correctly, especially for external API integration.

*   **API URLs and Keys:**
    *   Open `src/config.py`.
    *   Replace placeholder values like `"YOUR_OIL_PRICE_API_URL_HERE"` and `"YOUR_OIL_PRICE_API_KEY_HERE"` with actual URLs and valid API keys for:
        *   `OIL_PRICE_API_URL`, `OIL_PRICE_API_KEY`
        *   `EXCHANGE_RATE_API_URL` (and `EXCHANGE_RATE_API_KEY` if needed by the provider)
        *   `PRODUCTION_DATA_API_URL`, `PRODUCTION_API_KEY`
    *   **Note:** Without these, functionalities relying on external data fetching (including scheduled tasks) will fail.

*   **Database Path (Optional):**
    *   The default database path is `data/local_database.duckdb`. DuckDB will attempt to create this file.
    *   Ensure the `data/` directory exists at the root of the project, or create it if necessary:
        ```bash
        mkdir data
        ```
    *   You can change `DATABASE_PATH` in `src/config.py` if needed.

*   **Environment Variables (Recommended for Production):**
    *   For production or sensitive environments, it's strongly recommended to load sensitive configurations (like API keys and database URLs) from environment variables instead of hardcoding them in `src/config.py`.
    *   The `config.py` file contains commented-out examples using `os.getenv()`. You would typically create a `.env` file (and add it to `.gitignore`) like so:
        ```env
        # .env file example
        OIL_PRICE_API_KEY="your_actual_api_key"
        DATABASE_PATH="data/my_production_db.duckdb"
        # etc.
        ```
    *   And then modify `src/config.py` to load these (ensure `python-dotenv` is in `requirements.txt`):
        ```python
        import os
        # from dotenv import load_dotenv # Uncomment if you add python-dotenv

        # load_dotenv() # Load variables from .env file if using python-dotenv

        OIL_PRICE_API_KEY = os.getenv("OIL_PRICE_API_KEY", "YOUR_DEFAULT_KEY_IF_ANY")
        DATABASE_PATH = os.getenv("DATABASE_PATH", "data/local_database.duckdb")
        # ... and so on for other sensitive configurations
        ```

### 6. Run the Application

Once dependencies are installed and configurations are set, you can run the FastAPI application using Uvicorn (which is included in the dependencies):

```bash
uvicorn src.main:app --reload
```

*   `src.main:app`: Points to the FastAPI application instance (`app`) in the `src/main.py` file.
*   `--reload`: Enables auto-reloading the server when code changes are detected (useful for development).

The API should now be running locally. By default, you can access it at:

*   **API URL:** `http://127.0.0.1:8000`
*   **Interactive API Documentation (Swagger UI):** `http://127.0.0.1:8000/docs`
*   **Alternative API Documentation (ReDoc):** `http://127.0.0.1:8000/redoc`

## Key Modules and Components

This section describes the roles of the major modules and architectural components within the `src` directory.

### `main.py` - FastAPI Application Core

*   **API Definition:** Initializes the `FastAPI` application, serving as the central point for the API.
*   **Routing:** Includes and configures `APIRouter` instances for different resource types (e.g., Wells, Fields, Production Data). Each router defines specific endpoints (paths, HTTP methods).
*   **Dependency Injection (DI):** Manages the provision of dependencies to endpoint handlers. This includes:
    *   Repositories (e.g., `IWellRepository`) for data access.
    *   Use Cases (e.g., `CreateWellUseCase`) for encapsulating application logic.
    *   Adapters (e.g., `DuckDBAdapter`, `ExternalApiAdapter`).
*   **Lifecycle Events:** Handles application startup (`@app.on_event("startup")`) and shutdown (`@app.on_event("shutdown")`) events, used for tasks like initializing database connections, starting the scheduler, and cleaning up resources.
*   **Global Exception Handling:** Defines handlers for custom `AppException` and generic `Exception` types to ensure consistent error responses.

### `config.py` - Application Configuration

*   Stores static configuration settings for the application.
*   Includes placeholders for sensitive information (API URLs, keys) that **must be configured** by the user.
*   Defines schemas for database tables (e.g., `WELL_SCHEMA`, `PRODUCTION_SCHEMA`) used during database initialization.
*   Suggests the use of environment variables for managing sensitive data in production environments.

### `logging_config.py` - Logging

*   Sets up centralized logging for the application, allowing for consistent log formatting and output.

### Domain Layer (`src/domain/`)

*   **`entities/`**: Contains Pydantic models representing the core business objects of the application (e.g., `Well`, `Field`, `Production`, `OilPrice`, `ExchangeRate`). These define the structure and types of data.
*   **`value_objects/`**: (If used extensively) Would contain immutable objects representing descriptive aspects of the domain that don't have a conceptual identity (e.g., `PriceVO`, `DateVO`).
*   **`interfaces/`**: Defines abstract Python interfaces (contracts) for repositories (e.g., `IWellRepository`, `IProductionRepository`) and external services (`IExternalAPI`). This promotes loose coupling and allows for different implementations.
*   **`services/data_service.py` (`DataService` class)**: Implements domain-specific operations that don't naturally fit within a single entity. Currently, it handles complex data operations like:
    *   Filtering lists of entities based on dynamic criteria.
    *   Aggregating data (e.g., sum, mean) using specified grouping fields.
    *   Joining different datasets (e.g., production with price and exchange rates).
    It leverages the Polars library for efficient data manipulation.
*   **`aggregates/`**: (If used extensively) Would define complex domain objects that group entities and value objects into a consistency boundary (e.g., `Financials`).

### Application Layer (`src/application/`)

*   **`dtos/` (Data Transfer Objects)**: Pydantic models specifically designed for API request (`request/`) and response (`response/`) bodies. They define the external contract of the API and help with validation and serialization.
*   **`use_cases/`**: Classes that encapsulate specific application functionalities or user stories. They orchestrate interactions between the domain layer (entities, services, repositories) and the infrastructure layer.
    *   **`crud/`**: Contains use cases for Create, Read, Update, and Delete operations for each manageable entity (e.g., `CreateWellUseCase`, `ReadFieldUseCase`).
    *   **`analytical/`**: Houses use cases for performing data analysis, such as `FilterProductionUseCase`, `AggregateProductionUseCase`, and `JoinTablesUseCase`. These typically use `DataService` and repositories.
    *   **`scheduling/`**: Contains use cases related to scheduled tasks, like fetching data or performing computations periodically.

### Infrastructure Layer (`src/infrastructure/adapters/`)

This layer contains concrete implementations for interacting with external systems and concerns, adapting them to the interfaces defined in the domain or application layers.

*   **`duckdb_adapter.py` (`DuckDBAdapter` and repository implementations)**:
    *   Manages the connection to the DuckDB database.
    *   Initializes the database schema based on definitions in `config.py`.
    *   Provides concrete repository implementations (e.g., `WellDuckDBRepository`) that fulfill the domain repository interfaces (e.g., `IWellRepository`), handling data persistence and retrieval using DuckDB. It often uses a `DuckDBGenericRepository` base class for common CRUD operations.
*   **`external_api_adapter.py` (`ExternalApiAdapter` class)**:
    *   Implements the `IExternalAPI` interface.
    *   (Intended to) encapsulate the logic for making HTTP requests to third-party APIs to fetch data (e.g., oil prices, exchange rates).
    *   Uses API URLs and keys from `config.py`.
*   **`apscheduler_adapter.py` (`APSchedulerAdapter` class)**:
    *   Manages background scheduling of tasks using the APScheduler library.
    *   Used to automate regular jobs like fetching data from external APIs or performing calculations.
    *   Configured with other adapters (e.g., `DuckDBAdapter`, `ExternalApiAdapter`) and services (`DataService`) to execute these tasks.

## API Endpoints

The API provides RESTful endpoints for interacting with various oil and gas data entities.
The base URL is `http://127.0.0.1:8000`.
Full interactive documentation is available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

### Wells

*   **Prefix:** `/wells`
*   **`POST /`**: Create a new well.
*   **`GET /{well_code}`**: Retrieve a specific well.
*   **`GET /`**: List all wells.
*   **`PUT /{well_code}`**: Update an existing well.
*   **`DELETE /{well_code}`**: Delete a well.

### Fields

*   **Prefix:** `/fields`
*   (Similar CRUD endpoints as Wells: POST, GET one, GET all, PUT, DELETE)

### Production Data

*   **Prefix:** `/production`
*   **`POST /`**: Create a new production data entry.
*   **`GET /{well_code}/{reference_date}`**: Retrieve a production entry.
*   **`GET /`**: List production entries.
*   **`PUT /{well_code}/{reference_date}`**: Update an existing production entry.
*   **`DELETE /{well_code}/{reference_date}`**: Delete a production entry.

### Oil Prices

*   **Prefix:** `/oil-prices`
*   (Similar CRUD endpoints, typically identified by field_code and reference_date)

### Exchange Rates

*   **Prefix:** `/exchange-rates`
*   (Similar CRUD endpoints, typically identified by reference_date)

### Analysis Endpoints

*   **Prefix:** `/analysis`
*   **`POST /production/filter`**: Filter production data.
*   **`POST /production/aggregate`**: Aggregate production data.
*   **`GET /data/joined`**: Get joined production, oil price, and exchange rate data.

---
**Note:** For detailed request/response schemas, parameters, and to try out the API, please refer to the interactive documentation at `/docs` when the application is running.

## Potential Improvements and Future Features

This API provides a solid foundation for managing and analyzing oil and gas data. Here are some potential areas for improvement and ideas for future features:

### Code Refinements & Architectural Enhancements

*   **Refactor CRUD Use Cases:** Introduce a generic base class for CRUD use cases to reduce boilerplate.
*   **Consistent Use Case Layer Application:** Ensure all endpoints (especially Production/OilPrice read/delete) use the application layer consistently.
*   **Refactor `main.py` DI Providers:** Co-locate DI providers with their respective router modules.
*   **Specific Exception Handling:** Improve endpoint error handling to distinguish client (4xx) vs. server (5xx) errors.
*   **Configuration Management:** Fully implement loading sensitive data from environment variables.
*   **Remove Unused Code:** Clean up identified unused use cases, imports, and config variables after final review.
*   **Logging Review:** Replace `print()` statements in services/adapters with structured logging.

### New Features & Functionality

*   **Authentication and Authorization:** Implement robust security (e.g., OAuth2, JWT).
*   **Advanced Analytical Capabilities:** Add more sophisticated analysis (time series, decline curves).
*   **Data Validation Enhancements:** Implement more complex business rule validations.
*   **Asynchronous Operations:** Use background tasks for long-running operations.
*   **Enhanced Data Import/Export:** Provide bulk data import/export capabilities.
*   **User Management:** Add user registration and management if auth is implemented.
*   **Testing:** Develop a comprehensive unit and integration test suite.
*   **Data Versioning/Auditing:** Track data changes and critical operations.
*   **GIS/Mapping Integration:** Support geospatial queries for location-based data.

### Operational Enhancements

*   **Containerization:** Provide `Dockerfile` and `docker-compose.yml`.
*   **CI/CD Pipeline:** Set up automated testing and deployment.
*   **Monitoring and Alerting:** Integrate with monitoring tools.

# Project Technical Plan: Oil & Gas Data API

## 1. Project Overview

**Purpose:** This project provides a FastAPI-based backend API designed for managing, analyzing, and visualizing oil and gas exploration and production (E&P) data. It serves as a centralized repository for various E&P datasets, offers analytical capabilities, and automates data fetching and processing tasks.

**Goals:**
*   Provide robust CRUD (Create, Read, Update, Delete) operations for core E&P entities (Wells, Fields, Production records, Oil Prices, Exchange Rates).
*   Offer advanced analytical endpoints for filtering, aggregating, and joining data to derive insights.
*   Integrate with external APIs to fetch real-time or periodic data (e.g., oil prices, exchange rates).
*   Automate routine tasks like data fetching and financial computations using a scheduler.
*   Maintain a clean, scalable, and maintainable codebase through a layered architecture.

## 2. Architecture

The project employs a **Clean Architecture** pattern, separating concerns into distinct layers:

*   **Domain Layer (`src/domain/`):** Contains the core business logic, entities, value objects, domain services, and interfaces for repositories and external services. This layer is independent of application-specific or infrastructure-specific concerns.
*   **Application Layer (`src/application/`):** Orchestrates the use cases of the application. It contains Data Transfer Objects (DTOs) for API requests/responses and Use Case classes that implement specific application functionalities by coordinating domain objects and infrastructure services.
*   **Infrastructure Layer (`src/infrastructure/`):** Provides concrete implementations for external concerns like database interactions, external API calls, and scheduling. It adapts these external systems to the interfaces defined in the domain or application layers.
*   **Presentation Layer (`src/routers/` and `src/main.py`):** Handles HTTP requests and responses. In this project, it's represented by FastAPI routers and the main application setup. It depends on the application layer to execute business logic.

**Design Patterns Used:**
*   **Repository Pattern:** Abstracting data access logic behind interfaces (e.g., `IWellRepository`), with concrete implementations in the infrastructure layer (e.g., `WellDuckDBRepository`).
*   **Service Layer/Use Cases:** Encapsulating application-specific logic within use case classes.
*   **Dependency Injection:** FastAPI's built-in DI is used to manage dependencies between layers, primarily injecting repositories and services into use cases, and use cases into API endpoints.
*   **Adapter Pattern:** Used in the infrastructure layer to wrap external libraries/services (e.g., `DuckDBAdapter`, `ExternalApiAdapter`, `APSchedulerAdapter`).

## 3. Key Technologies

*   **Backend Framework:** FastAPI (for building asynchronous APIs with Python type hints)
*   **Database:** DuckDB (an in-process analytical data management system)
*   **Data Manipulation:** Polars (a fast DataFrame library for Rust and Python, used in `DataService`)
*   **Scheduling:** APScheduler (for scheduling background tasks)
*   **Data Validation & Serialization:** Pydantic (used for defining entities, DTOs, and request/response models)
*   **Programming Language:** Python 3.8+

## 4. Core Components & Modules

### 4.1. `src/main.py` - Application Entry Point
*   Initializes the FastAPI application (`app`).
*   Sets up global exception handlers (`AppException`, generic `Exception`).
*   Manages application lifecycle events:
    *   **`startup_event`**: Initializes logging, database connection (via `DuckDBAdapter`), creates tables, and starts the `APSchedulerAdapter`. It also schedules predefined jobs.
    *   **`shutdown_event`**: Shuts down the scheduler and closes the database connection.
*   Includes API routers defined in `src/routers/`.
*   Instantiates global adapters (`DuckDBAdapter`, `ExternalApiAdapter`). Note: `scheduler_adapter` is initialized within `startup_event`.

### 4.2. `src/config.py` - Configuration Management
*   Stores static application settings:
    *   Placeholder URLs and API keys for external services (Oil Price, Exchange Rate, Production Data).
    *   `DATABASE_PATH` for DuckDB.
    *   `DEFAULT_CHUNK_SIZE` (though not actively observed in current core logic).
    *   Database table schemas (e.g., `WELL_SCHEMA`, `PRODUCTION_SCHEMA`) used by `DuckDBAdapter` for table creation.
*   Includes commented-out examples for loading configurations from environment variables, which is recommended for production but not enforced by default.

### 4.3. `src/logging_config.py` - Logging Setup
*   Configures application-wide logging, likely setting up formatters, handlers, and log levels. (Exact implementation details would be in this file).

### 4.4. `src/core/exceptions.py` - Custom Exceptions
*   Defines custom application-specific exceptions like `AppException` and its derivatives (e.g., `DatabaseError`, `ExternalApiError`). These allow for more structured error handling and consistent API error responses.

### 4.5. Domain Layer (`src/domain/`)

*   **Entities (`src/domain/entities/`):** Pydantic models representing core business objects (e.g., `Well`, `Field`, `Production`, `OilPrice`, `ExchangeRate`). They define the structure, data types, and validation rules for these objects.
*   **Value Objects (`src/domain/value_objects/`):** Immutable objects representing descriptive aspects of the domain without a conceptual identity (e.g., `Price`, `DateVO`, `Rate`).
*   **Repository Interfaces (`src/domain/interfaces/repository.py`):** Abstract interfaces defining contracts for data persistence operations for each entity (e.g., `IWellRepository`, `IProductionRepository`).
*   **External API Interface (`src/domain/interfaces/external_api.py`):** Defines the contract (`IExternalAPI`) for fetching data from external sources.
*   **Domain Services (`src/domain/services/`):**
    *   **`DataService` (`data_service.py`):** Implements complex data operations that don't naturally fit within a single entity. It uses the Polars library for efficient in-memory data manipulation:
        *   `filter_production()`: Filters a list of `Production` entities based on dynamic criteria.
        *   `aggregate_production()`: Aggregates `Production` data using specified grouping fields and aggregation functions (sum, mean, etc.) via Polars DataFrames.
        *   `join_data()`: Joins `Production`, `OilPrice`, and `ExchangeRate` data based on `reference_date` using Polars DataFrames.
        *   *Note:* Contains `print()` statements for warnings/errors which should ideally be replaced with structured logging.
    *   **`DCAService` (`dca_service.py`):** Likely handles Decline Curve Analysis calculations, a common E&P analytical task. (Contents not fully reviewed but its presence is noted).
*   **Aggregates (`src/domain/aggregates/`):**
    *   **`Financials` (`financials.py`):** Represents a complex domain object that might group entities like production, prices, and rates to calculate financial metrics. Used by `ScheduleComputeFinancialsUseCase`.
    *   **`FieldProduction` (`field_production.py`):** Potentially an aggregate for field-level production summaries.

### 4.6. Application Layer (`src/application/`)

*   **DTOs (Data Transfer Objects) (`src/application/dtos/`):** Pydantic models specifically for API requests (`request/`) and responses (`response/`). They define the external contract of the API, handle validation of incoming data, and serialize outgoing data.
*   **Use Cases (`src/application/use_cases/`):** Classes that orchestrate specific application functionalities:
    *   **CRUD (`crud/`):** Contain use cases for Create, Read, Update, Delete, and List operations for each entity (e.g., `CreateWellUseCase`, `ReadFieldUseCase`, `ListProductionUseCase`). These use cases typically interact with repositories.
    *   **Analytical (`analytical/`):** House use cases for data analysis:
        *   `FilterProductionUseCase`: Uses `DataService` to filter production data.
        *   `AggregateProductionUseCase`: Uses `DataService` to aggregate production data.
        *   `JoinTablesUseCase`: Uses `DataService` to join different datasets.
        *   `DeclineCurveAnalysisUseCase`: Likely uses `DCAService` for decline curve calculations.
    *   **Scheduling (`scheduling/`):** Contains use cases for tasks triggered by the scheduler:
        *   `ScheduleFetchDataUseCase`: Fetches data from external APIs (using `IExternalAPI`) and saves it to the database (using relevant repositories).
        *   `ScheduleComputeFinancialsUseCase`: Computes financial metrics (likely using `DataService` and `Financials` aggregate) and potentially stores them.

### 4.7. Infrastructure Layer (`src/infrastructure/adapters/`)

*   **`DuckDBAdapter` (`duckdb_adapter.py`):**
    *   Manages connections to the DuckDB database (`DATABASE_PATH` from `config.py`).
    *   `initialize_database()`: Creates tables based on Pydantic entity models and schema definitions in `config.py` (`PYDANTIC_TO_DUCKDB_TYPES`, `PRIMARY_KEY_COLUMNS`). Uses `_create_table_if_not_exists()` for each entity.
    *   Provides concrete repository implementations (e.g., `WellDuckDBRepository`, `ProductionDuckDBRepository`) that inherit from a `DuckDBGenericRepository`.
    *   `DuckDBGenericRepository`: Provides common CRUD methods (`add`, `get`, `get_by_composite_key`, `list`, `update`, `update_by_composite_key`, `delete`, `delete_by_composite_key`) using DuckDB SQL commands.
    *   Handles mapping between Pydantic types and DuckDB SQL types.
    *   Uses `logging` for operations.
*   **`ExternalApiAdapter` (`external_api_adapter.py`):**
    *   Implements the `IExternalAPI` interface.
    *   `fetch_data()`: Makes HTTP GET requests to external APIs using the `requests` library.
    *   Loads API URLs, keys, and header templates from `src/config.py` (e.g., `OIL_PRICE_API_URL`, `OIL_PRICE_API_KEY`).
    *   Handles API errors (HTTP errors, timeouts, connection errors, JSON decoding errors) and wraps them in `ExternalApiError`.
    *   Attempts to extract list data from various common JSON response structures.
    *   Uses `logging` for operations. Relies on placeholder URLs/keys from `config.py`, so actual data fetching won't work without proper configuration.
*   **`APSchedulerAdapter` (`apscheduler_adapter.py`):**
    *   Manages background task scheduling using the `APScheduler` library.
    *   `schedule_daily_data_fetch()`: Schedules jobs to fetch data (e.g., production, oil prices, exchange rates) using `ScheduleFetchDataUseCase`.
    *   `schedule_daily_financial_computation()`: Schedules jobs to perform financial calculations using `ScheduleComputeFinancialsUseCase`.
    *   Jobs are configured to run at specific times (e.g., daily at certain hours).
    *   Includes a `job_listener` to log errors during job execution.
    *   Uses `logging` for operations.

### 4.8. Presentation Layer (`src/routers/` and `src/main.py`)

*   **Routers (`src/routers/*.py`):** FastAPI `APIRouter` instances for different resource types (e.g., `well_router.py`, `field_router.py`, `analysis_router.py`).
    *   Define API endpoints (paths, HTTP methods, request/response models).
    *   Use FastAPI's dependency injection to get instances of application use cases.
    *   Delegate request handling to the appropriate use case methods.
    *   Return responses, often using DTOs.
*   **Dependency Injection Providers (`src/routers/dependencies.py` and within each router file):**
    *   Functions that provide instances of adapters, repositories, and use cases. This was refactored from `main.py` to be co-located with routers or in a shared `dependencies.py`. For example, `get_db_adapter()` provides the `DuckDBAdapter` instance. Repository providers (e.g., `get_well_repository()`) use the `DuckDBAdapter` to get specific repository instances. Use case providers instantiate use cases with their required dependencies (repositories, services).

## 5. Data Flow Examples

### 5.1. CRUD Operation (e.g., Create Well)
1.  **HTTP Request:** Client sends a `POST` request to `/wells/` with well data in the request body.
2.  **Router (`well_router.py`):** The endpoint handler for `POST /wells/` receives the request.
3.  **Dependency Injection:** FastAPI injects an instance of `CreateWellUseCase`.
4.  **Request DTO:** The request body is validated and converted into a `WellRequest` DTO.
5.  **Use Case (`CreateWellUseCase`):** The `execute()` method is called with the `WellRequest` DTO.
    *   The use case converts the DTO to a `Well` domain entity.
    *   It calls the `add()` method on the injected `IWellRepository` (implemented by `WellDuckDBRepository`).
6.  **Repository (`WellDuckDBRepository`):** The `add()` method constructs and executes an SQL `INSERT` statement in DuckDB.
7.  **Database (`DuckDBAdapter`):** The data is persisted.
8.  **Response DTO:** The created `Well` entity is converted to a `WellResponse` DTO by the use case or router.
9.  **HTTP Response:** The router returns the `WellResponse` DTO to the client with a `201 Created` status.

### 5.2. Analytical Operation (e.g., Filter Production Data)
1.  **HTTP Request:** Client sends a `POST` request to `/analysis/production/filter` with filter criteria in the request body.
2.  **Router (`analysis_router.py`):** The endpoint handler receives the request.
3.  **Dependency Injection:** FastAPI injects an instance of `FilterProductionUseCase`.
4.  **Request DTO:** Filter criteria are validated (e.g., `ProductionFilterRequestDTO`).
5.  **Use Case (`FilterProductionUseCase`):** The `execute()` method is called.
    *   It retrieves all production data using `IProductionRepository.list()`.
    *   It calls `DataService.filter_production()` with the data and filter criteria.
6.  **Domain Service (`DataService`):**
    *   The `filter_production()` method uses Polars to efficiently filter the data in memory based on the provided criteria.
7.  **Response DTO:** The filtered list of production records (or a summary DTO) is returned by the use case.
8.  **HTTP Response:** The router returns the filtered data to the client.

## 6. Database Schema

The database schema is implicitly defined by the Pydantic models in `src/domain/entities/` and the `*_SCHEMA` dictionaries in `src/config.py`. `DuckDBAdapter` uses these to create tables:

*   **`wells` Table:** Stores well information (e.g., `well_code` (PK), `well_name`, `field_code`, `latitude`, `longitude`, `spud_date`).
*   **`fields` Table:** Stores field information (e.g., `field_code` (PK), `field_name`, `reservoir_formation`, `discovery_date`).
*   **`production` Table:** Stores production volumes (e.g., `well_code`, `reference_date` (Composite PK with `well_code`), `oil_volume_bbl`, `gas_volume_mcf`, `water_volume_bbl`).
*   **`oil_prices` Table:** Stores oil price information (e.g., `field_code`, `reference_date` (Composite PK with `field_code`), `price_usd_bbl`).
*   **`exchange_rates` Table:** Stores currency exchange rates (e.g., `reference_date` (PK), `from_currency`, `to_currency`, `rate`).

Primary keys and data types are derived from Pydantic model annotations and the `PYDANTIC_TO_DUCKDB_TYPES` mapping in `duckdb_adapter.py`.

## 7. Scheduled Tasks

Background tasks are managed by `APSchedulerAdapter` and defined via use cases in `src/application/use_cases/scheduling/`.

*   **Daily Data Fetching:**
    *   **Job IDs:** `fetch_production_data_daily`, `fetch_oil_price_daily`, `fetch_exchange_rate_daily`.
    *   **Trigger:** Cron-based, typically daily at specified times (e.g., 1:00 AM, 2:00 AM).
    *   **Action:** `ScheduleFetchDataUseCase` is executed for each source.
        1.  Calls `IExternalAPI.fetch_data()` (implemented by `ExternalApiAdapter`) to get data from the configured external API.
        2.  Transforms the fetched data into appropriate domain entities (e.g., `Production`, `OilPrice`).
        3.  Saves the entities to the database using the relevant repository (e.g., `IProductionRepository.add()`).
*   **Daily Financial Computation:**
    *   **Job ID:** `compute_financials_daily`.
    *   **Trigger:** Cron-based, daily (e.g., 3:00 AM), typically after data fetching jobs.
    *   **Action:** `ScheduleComputeFinancialsUseCase` is executed.
        1.  Fetches necessary data (production, oil prices, exchange rates) from repositories.
        2.  Uses `DataService` (and potentially `Financials` aggregate) to perform calculations (e.g., revenue, net present value).
        3.  The results might be logged or stored back into the database (specifics depend on the use case implementation).

## 8. Error Handling Strategy

*   **Custom Exceptions (`src/core/exceptions.py`):**
    *   `AppException`: Base class for application-specific errors, can include a `status_code` and `detail`.
    *   `DatabaseError`: For errors related to database operations.
    *   `ExternalApiError`: For errors during external API calls.
    *   Other specific exceptions can be derived as needed.
*   **Global Exception Handlers (`src/main.py`):**
    *   `app_exception_handler`: Catches `AppException` instances and returns a JSON response with the appropriate status code and message.
    *   `generic_exception_handler`: Catches any unhandled `Exception` and returns a generic 500 error response.
*   **Adapter-Level Handling:** Adapters (`DuckDBAdapter`, `ExternalApiAdapter`) catch library-specific exceptions and re-raise them as custom exceptions (e.g., `DatabaseError`, `ExternalApiError`) to decouple the rest of the application from infrastructure details.
*   **Logging:** Exceptions are generally logged with stack traces for debugging.

## 9. Configuration Strategy

*   **Centralized File (`src/config.py`):** Main source for application settings, including API URLs, keys, database path, and table schemas.
*   **Placeholders:** Default values in `config.py` for API keys and URLs are placeholders (e.g., `"YOUR_OIL_PRICE_API_URL_HERE"`). These **must be replaced** with actual values for the application to function correctly, especially for external data fetching.
*   **Environment Variables (Recommended):** `config.py` includes commented-out suggestions for using `os.getenv()` to load sensitive configurations from environment variables. This is the recommended approach for production deployments to avoid hardcoding secrets. Tools like `python-dotenv` can be used to manage `.env` files during development.
*   **Database Schema Configuration:** Table names and column types are partially derived from Pydantic models and partially from mappings (`PYDANTIC_TO_DUCKDB_TYPES`, `PRIMARY_KEY_COLUMNS`) within `duckdb_adapter.py` and schema dictionaries in `config.py`.

## 10. Potential Areas for Future Development (Summary)

*   **Enhanced Security:** Robust authentication and authorization (e.g., OAuth2, JWT).
*   **Advanced Analytics:** More sophisticated E&P analyses (e.g., time series forecasting, decline curve enhancements, volumetrics).
*   **Improved Data Validation:** More complex business rule validations beyond Pydantic's capabilities.
*   **Asynchronous Operations for Long Tasks:** For potentially long-running API requests, consider background tasks (beyond scheduled ones).
*   **Bulk Data Import/Export:** Features for handling large datasets.
*   **Comprehensive Testing:** Continue expanding unit, integration, and end-to-end tests.
*   **Data Versioning/Auditing:** Track changes to critical data.
*   **Containerization & CI/CD:** Dockerize the application and set up CI/CD pipelines.
*   **Logging:** Complete replacement of `print` statements with structured logging (e.g., in `DataService`).
*   **CRUD Use Case Refinement:** Consider a generic base class for CRUD use cases if boilerplate becomes significant.

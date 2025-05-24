# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2025-05-16

### Added
- Initial project creation
- .gitignore file
- README.md file
- main.py with a single endpoint for testing
- Poetry files for dependency management
- Git repository initialization

## [1.0.0] - 2025-05-18

### Added
- Initial FastAPI application creation
- Modular architecture following Hexagonal Architecture principles
- Domain layer with `Message` entity and `ExternalServiceInterface`
- Application layer with use cases (`GetGreetingUseCase`, `FetchExternalDataUseCase`) and DTOs
- Adapters layer with `HttpClient` implementation
- Infrastructure layer with dependency injection container
- Presentation layer with API controllers and setup
- Requirements file (`requirements.txt`) with necessary dependencies

### Changed
- Refactored `main.py` to be an entry point for the modular application
- Moved business logic to appropriate layers

### Removed
- Monolithic structure in favor of modular architecture

## [1.0.1] - 2025-05-19

### Added
- Comprehensive documentation structure in `docs/` including:
  - API documentation
  - Deployment guide
  - Development plan
  - Features implementation guide
  - Module descriptions
  - Optimization guide
  - Project principles and structure
  - Testing plan
  - User guide
  - Security considerations
  - Project roadmap
- Test infrastructure with pytest configuration
- Coverage reporting setup
- Application structure with modular organization (`app/` directory)
- Project initialization file (`__init__.py`)

### Changed
- Updated dependencies in `poetry.lock` and `pyproject.toml`
- Modified `requirements.txt` with new dependencies
- Updated project documentation in `readme.md`
- Enhanced `.gitignore` configuration
- Refactored `main.py`

### Removed
- Removed `STUDYME.md` in favor of new documentation structure

## [1.0.2] - 2025-05-19

### Added
- New endpoint /authenticate

## [1.0.3] - 2025-05-20

### Refactored
- Codebase to have more parametric design and follow hexagonal architecture

### Modified
- **.gitignore**: Updated to include new untracked files and directories.
- **backend/app/application/use_cases/fetch_odata_data.py**: Enhanced to handle new data fetching logic.
- **backend/app/infrastructure/di/container.py**: Updated dependency injection configuration.
- **backend/app/presentation/api/rest_controllers/odata_controllers.py**: Updated to integrate new data fetching logic.

### Removed
- **backend/app/application/use_cases/fetch_google_data.py**: Removed as part of refactoring.
- **backend/app/application/use_cases/fetch_json_data.py**: Removed as part of refactoring.

### Added
- **backend/app/domain/interfaces/o_data_repository.py**: Added new interface for data repository.
- **backend/app/infrastructure/database/**: Added new directory for database-related files.

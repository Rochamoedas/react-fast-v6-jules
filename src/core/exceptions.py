# src/core/exceptions.py

class AppException(Exception):
    """
    Base class for custom application exceptions.
    Allows for consistent error handling and response formatting.
    """
    def __init__(self, message: str, status_code: int = 500, detail: str = None): # type: ignore
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail

    def __str__(self):
        return self.message

# Example specific exceptions (can be added as needed)
class NotFoundException(AppException):
    def __init__(self, resource_name: str, resource_id: str | int):
        super().__init__(
            message=f"{resource_name} with ID '{resource_id}' not found.",
            status_code=404,
            detail=f"The requested {resource_name.lower()} resource could not be located."
        )

class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request.", detail: str = None): # type: ignore
        super().__init__(message=message, status_code=400, detail=detail)

class ConfigurationError(AppException):
    def __init__(self, message: str = "Configuration error.", detail: str = None): # type: ignore
        super().__init__(message=message, status_code=500, detail=detail)

class DatabaseError(AppException):
    def __init__(self, message: str = "Database operation failed.", detail: str = None): # type: ignore
        super().__init__(message=message, status_code=500, detail=detail)

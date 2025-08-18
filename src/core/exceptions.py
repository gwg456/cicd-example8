"""
Custom exception classes for better error handling
"""
from typing import Optional, Dict, Any


class AppException(Exception):
    """Base exception class for the application"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        retryable: bool = False
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.retryable = retryable
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/API responses"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
            "retryable": self.retryable
        }


class ConfigurationError(AppException):
    """Raised when configuration is invalid or missing"""
    
    def __init__(self, message: str, missing_keys: Optional[list] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={"missing_keys": missing_keys} if missing_keys else {},
            retryable=False
        )


class DeploymentError(AppException):
    """Raised when deployment operations fail"""
    
    def __init__(self, message: str, deployment_id: Optional[str] = None, **kwargs):
        details = {"deployment_id": deployment_id} if deployment_id else {}
        details.update(kwargs)
        super().__init__(
            message=message,
            error_code="DEPLOYMENT_ERROR",
            details=details,
            retryable=True
        )


class ConnectionError(AppException):
    """Raised when connection to external service fails"""
    
    def __init__(self, message: str, service: str, **kwargs):
        details = {"service": service}
        details.update(kwargs)
        super().__init__(
            message=message,
            error_code="CONNECTION_ERROR",
            details=details,
            retryable=True
        )


class TimeoutError(AppException):
    """Raised when operation times out"""
    
    def __init__(self, message: str, timeout: int, operation: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            details={
                "timeout": timeout,
                "operation": operation
            },
            retryable=True
        )


class AuthenticationError(AppException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            retryable=False
        )


class AuthorizationError(AppException):
    """Raised when authorization fails"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            retryable=False
        )


class ValidationError(AppException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            retryable=False
        )


class ResourceNotFoundError(AppException):
    """Raised when a requested resource is not found"""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with id '{resource_id}' not found",
            error_code="RESOURCE_NOT_FOUND",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            },
            retryable=False
        )


class RateLimitError(AppException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details=details,
            retryable=True
        )


class RetryableError(AppException):
    """Generic retryable error"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="RETRYABLE_ERROR",
            details=kwargs,
            retryable=True
        )
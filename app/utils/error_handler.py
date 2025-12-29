"""
Error Handling Utilities: Standardized error response formatting.
Includes timestamp, error_code, and retry_count in all responses.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """Standardized error response schema."""
    timestamp: str
    error_code: str
    message: str
    retry_count: int = 0
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """Standardized success response schema."""
    timestamp: str
    message: str
    data: Optional[Any] = None
    retry_count: int = 0


def create_error_response(
    error_code: str,
    message: str,
    retry_count: int = 0,
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """
    Create a standardized error response.
    
    Args:
        error_code: HTTP error code or custom code (e.g., "504", "503", "400")
        message: Error message
        retry_count: Number of retries attempted
        details: Optional additional error details
    
    Returns:
        ErrorResponse object
    """
    return ErrorResponse(
        timestamp=datetime.utcnow().isoformat() + "Z",
        error_code=error_code,
        message=message,
        retry_count=retry_count,
        details=details
    )


def create_success_response(
    message: str,
    data: Optional[Any] = None,
    retry_count: int = 0
) -> SuccessResponse:
    """
    Create a standardized success response.
    
    Args:
        message: Success message
        data: Response data
        retry_count: Number of retries attempted
    
    Returns:
        SuccessResponse object
    """
    return SuccessResponse(
        timestamp=datetime.utcnow().isoformat() + "Z",
        message=message,
        data=data,
        retry_count=retry_count
    )


def log_error(error_code: str, message: str, exception: Optional[Exception] = None):
    """
    Log an error with context.
    
    Args:
        error_code: Error code
        message: Error message
        exception: Optional exception object for stack trace
    """
    if exception:
        logger.error(f"[{error_code}] {message}", exc_info=exception)
    else:
        logger.error(f"[{error_code}] {message}")

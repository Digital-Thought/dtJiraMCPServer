"""Atlassian HTTP client layer for dtJiraMCPServer."""

from .base import AtlassianClient
from .errors import ErrorCategory, classify_http_error
from .jsm import JsmClient
from .pagination import PaginatedResponse, PaginationHandler
from .platform import PlatformClient
from .rate_limiter import RateLimiter

__all__ = [
    "AtlassianClient",
    "ErrorCategory",
    "JsmClient",
    "PaginatedResponse",
    "PaginationHandler",
    "PlatformClient",
    "RateLimiter",
    "classify_http_error",
]

"""
Tenant context middleware for multi-tenant FastAPI applications.

Provides automatic tenant extraction from paths, headers, or subdomains,
and attaches tenant_id to request state for use in endpoints and dependencies.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Callable, Optional
import re
import logging

logger = logging.getLogger(__name__)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware for extracting and validating tenant context in multi-tenant applications.
    
    Supports multiple tenant identification methods:
    1. Path-based: /tenant/{tenant_id}/...
    2. Header-based: X-Tenant-ID header
    3. Subdomain-based: {tenant_id}.example.com
    4. Query parameter: ?tenant_id=...
    """
    
    # Paths that don't require tenant context
    EXCLUDE_PATHS = {
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/status",
        "/auth/login",
        "/auth/register",
        "/auth/token",
        "/metrics",
        "/org/scans/complete",  # Complete scan endpoint (dev/testing)
        "/",  # Root endpoint
        "/git-scan",  # Git scan endpoints
        "/git-scan-detailed",
        "/ai-scan",
        "/scan-history",
        "/compliance-rules",
        "/india-compliance",  # All Indian compliance endpoints
    }
    
    # File extensions that don't require tenant context (static files)
    EXCLUDE_EXTENSIONS = {
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
        ".css", ".js", ".map", ".json", ".txt", ".xml",
        ".woff", ".woff2", ".ttf", ".eot"
    }
    
    # Pattern for path-based tenant extraction: /tenant/{tenant_id}/...
    TENANT_PATH_PATTERN = re.compile(r"^/tenant/([a-zA-Z0-9_-]+)/")
    
    def __init__(
        self,
        app,
        enable_path_extraction: bool = True,
        enable_header_extraction: bool = True,
        enable_subdomain_extraction: bool = False,
        enable_query_extraction: bool = True,
        domain: str = "example.com",
    ):
        """
        Initialize TenantContextMiddleware.
        
        Args:
            app: FastAPI application
            enable_path_extraction: Extract tenant from URL path
            enable_header_extraction: Extract tenant from X-Tenant-ID header
            enable_subdomain_extraction: Extract tenant from subdomain
            enable_query_extraction: Extract tenant from query parameter
            domain: Base domain for subdomain extraction (e.g., "example.com")
        """
        super().__init__(app)
        self.enable_path_extraction = enable_path_extraction
        self.enable_header_extraction = enable_header_extraction
        self.enable_subdomain_extraction = enable_subdomain_extraction
        self.enable_query_extraction = enable_query_extraction
        self.domain = domain

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """
        Process incoming request and extract tenant context.
        """
        # Check if path is excluded from tenant requirement
        if self._is_excluded_path(request.url.path):
            return await call_next(request)

        # Try to extract tenant ID using different methods
        tenant_id = None
        extraction_method = None

        # 1. Try path-based extraction
        if self.enable_path_extraction:
            tenant_id, extraction_method = self._extract_from_path(request.url.path)

        # 2. Try header-based extraction if not found
        if not tenant_id and self.enable_header_extraction:
            tenant_id = self._extract_from_header(request)
            if tenant_id:
                extraction_method = "header"

        # 3. Try subdomain-based extraction if not found
        if not tenant_id and self.enable_subdomain_extraction:
            tenant_id = self._extract_from_subdomain(request)
            if tenant_id:
                extraction_method = "subdomain"

        # 4. Try query parameter extraction if not found
        if not tenant_id and self.enable_query_extraction:
            tenant_id = self._extract_from_query(request)
            if tenant_id:
                extraction_method = "query"

        # If no tenant ID found and not in excluded paths, return 400
        if not tenant_id:
            logger.warning(
                f"No tenant context found for path: {request.url.path} "
                f"from {request.client}"
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Missing tenant context. Provide via path, header, subdomain, or query parameter."}
            )

        # Validate tenant ID format (alphanumeric, dash, underscore)
        if not self._is_valid_tenant_id(tenant_id):
            logger.warning(f"Invalid tenant ID format: {tenant_id}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid tenant ID format."}
            )

        # Attach tenant context to request state
        request.state.tenant_id = tenant_id
        request.state.tenant_extraction_method = extraction_method

        logger.debug(
            f"Tenant extracted: {tenant_id} via {extraction_method} "
            f"for path: {request.url.path}"
        )

        # Process the request
        response = await call_next(request)

        # Add tenant ID to response headers for debugging (optional)
        response.headers["X-Tenant-ID"] = tenant_id
        response.headers["X-Tenant-Source"] = extraction_method or "unknown"

        return response

    def _is_excluded_path(self, path: str) -> bool:
        """Check if path should be excluded from tenant requirement."""
        # Check file extensions (static files)
        if any(path.lower().endswith(ext) for ext in self.EXCLUDE_EXTENSIONS):
            return True
            
        # Exact matches
        if path in self.EXCLUDE_PATHS:
            return True

        # Prefix matches
        for excluded in self.EXCLUDE_PATHS:
            if path.startswith(excluded):
                return True

        return False

    def _extract_from_path(self, path: str) -> tuple[Optional[str], Optional[str]]:
        """Extract tenant ID from URL path: /tenant/{tenant_id}/..."""
        match = self.TENANT_PATH_PATTERN.match(path)
        if match:
            return match.group(1), "path"
        return None, None

    def _extract_from_header(self, request: Request) -> Optional[str]:
        """Extract tenant ID from X-Tenant-ID header."""
        return request.headers.get("X-Tenant-ID")

    def _extract_from_subdomain(self, request: Request) -> Optional[str]:
        """Extract tenant ID from subdomain."""
        host = request.headers.get("Host", "")
        
        if not host:
            return None

        # Remove port if present
        host = host.split(":")[0]

        # Check if host has subdomain
        parts = host.split(".")

        if len(parts) > 2:  # subdomain.example.com
            subdomain = parts[0]
            base_domain = ".".join(parts[1:])

            # Verify it matches configured domain
            if base_domain == self.domain:
                return subdomain

        return None

    def _extract_from_query(self, request: Request) -> Optional[str]:
        """Extract tenant ID from query parameter."""
        return request.query_params.get("tenant_id")

    def _is_valid_tenant_id(self, tenant_id: str) -> bool:
        """Validate tenant ID format."""
        # Allow alphanumeric, dash, underscore
        # Length between 1 and 50 characters
        pattern = re.compile(r"^[a-zA-Z0-9_-]{1,50}$")
        return bool(pattern.match(tenant_id))


def get_tenant_id(request: Request) -> str:
    """
    Dependency function to get current tenant ID.
    
    Usage in endpoint:
        @router.get("/data")
        async def get_data(tenant_id: str = Depends(get_tenant_id)):
            # Use tenant_id for filtering
            pass
    """
    tenant_id = getattr(request.state, "tenant_id", None)

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context not found in request."
        )

    return tenant_id


def get_tenant_extraction_method(request: Request) -> Optional[str]:
    """
    Get the method used to extract tenant ID from the request.
    
    Returns one of: "path", "header", "subdomain", "query", or None
    """
    return getattr(request.state, "tenant_extraction_method", None)


# ==================== Utility Functions ====================

def apply_tenant_filter(query, model, tenant_column: str = "org_id"):
    """
    Apply tenant filtering to a SQLAlchemy query.
    
    Usage:
        query = db.query(Scan)
        query = apply_tenant_filter(query, Scan, "org_id")
    """
    # This would be used with get_tenant_id dependency
    # The actual filtering happens in the endpoint using the tenant_id
    return query


class TenantAwareModel:
    """
    Base class for models that should be automatically filtered by tenant_id.
    
    Subclasses should define TENANT_FIELD = "org_id" or similar.
    """
    TENANT_FIELD = "org_id"


def create_tenant_router(
    prefix: str = "",
    tags: list = None,
    dependencies: list = None
):
    """
    Factory function to create a router with built-in tenant context dependency.
    
    Usage:
        router = create_tenant_router(
            prefix="/api/v1/scans",
            tags=["scans"]
        )
        
        @router.get("/")
        async def list_scans(tenant_id: str = Depends(get_tenant_id)):
            # tenant_id is automatically available and validated
            pass
    """
    from fastapi import APIRouter

    if dependencies is None:
        dependencies = [Depends(get_tenant_id)]
    else:
        dependencies = list(dependencies) + [Depends(get_tenant_id)]

    return APIRouter(
        prefix=prefix,
        tags=tags or [],
        dependencies=dependencies
    )


# ==================== Validation Utilities ====================

def validate_tenant_access(user_org_id: str, tenant_id: str) -> bool:
    """
    Validate that a user's organization has access to a tenant.
    
    This is a placeholder - implement based on your multi-tenancy model.
    """
    # Simple check: user_org_id should match tenant_id
    return user_org_id == tenant_id


def validate_resource_access(resource_org_id: str, tenant_id: str) -> bool:
    """
    Validate that a resource belongs to the requested tenant.
    
    Used to prevent cross-tenant data access.
    """
    return resource_org_id == tenant_id


if __name__ == "__main__":
    # Example usage demonstration
    from fastapi import FastAPI
    
    app = FastAPI()
    
    # Add middleware
    app.add_middleware(
        TenantContextMiddleware,
        enable_path_extraction=True,
        enable_header_extraction=True,
        enable_subdomain_extraction=False,
        enable_query_extraction=True,
    )
    
    @app.get("/tenant/{tenant_id}/data")
    async def get_data(request: Request):
        return {
            "tenant_id": request.state.tenant_id,
            "extraction_method": request.state.tenant_extraction_method
        }

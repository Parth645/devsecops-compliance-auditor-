"""
Multi-tenant authentication middleware for FastAPI.

Provides:
- Organization context extraction from API keys
- Redis-based caching for performance
- Org-level isolation via dependency injection
- Type-safe org context passing to routes
"""

import os
import hashlib
from typing import Optional
from uuid import UUID
from datetime import timedelta

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
import redis
import bcrypt
from sqlalchemy.orm import Session

from schema.database import SessionLocal
from schema.schema import Organization


# ============================================================================
# Pydantic Models
# ============================================================================

class OrgContext(BaseModel):
    """Organization context passed to each request."""
    id: UUID = Field(..., description="Organization UUID")
    name: str = Field(..., description="Organization name")
    tier: str = Field(..., description="Subscription tier: free/startup/team/enterprise")
    max_projects: int = Field(default=3, description="Max projects allowed")
    max_scans_per_month: int = Field(default=100, description="Max scans/month")
    is_active: bool = Field(default=True, description="Organization active status")
    
    class Config:
        from_attributes = True


# ============================================================================
# Redis Client Initialization
# ============================================================================

def get_redis_client() -> redis.Redis:
    """Get or create Redis client for caching."""
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_keepalive=True,
    )


# Initialize Redis client
try:
    _redis_client = get_redis_client()
    _redis_client.ping()
    REDIS_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Redis not available: {e}. Caching disabled.")
    _redis_client = None
    REDIS_AVAILABLE = False


# ============================================================================
# API Key Extraction & Verification
# ============================================================================

def extract_api_key(request: Request) -> str:
    """
    Extract API key from Authorization header.
    
    Expected format: "Authorization: Bearer <api_key>"
    """
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Use: Authorization: Bearer <api_key>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    api_key = auth_header.replace("Bearer ", "", 1).strip()
    
    if not api_key or len(api_key) < 10:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key


def verify_api_key(api_key: str, api_key_hash: str) -> bool:
    """
    Verify API key against bcrypt hash.
    
    Args:
        api_key: Plain text API key from request
        api_key_hash: Bcrypt hash from database
        
    Returns:
        True if key matches hash, False otherwise
    """
    try:
        # If hash is hex (from test), compare directly
        if len(api_key_hash) == 64:  # SHA256 hex
            return hashlib.sha256(api_key.encode()).hexdigest() == api_key_hash
        
        # Otherwise use bcrypt
        return bcrypt.checkpw(api_key.encode(), api_key_hash.encode())
    except Exception as e:
        print(f"⚠️  API key verification error: {e}")
        return False


# ============================================================================
# Cache Operations
# ============================================================================

def _get_cache_key(api_key: str) -> str:
    """Generate Redis cache key for API key."""
    return f"org_auth:{hashlib.sha256(api_key.encode()).hexdigest()}"


def _get_cached_org(api_key: str) -> Optional[str]:
    """
    Get cached organization UUID from Redis.
    
    Args:
        api_key: Plain text API key
        
    Returns:
        Organization UUID string if cached and valid, None otherwise
    """
    if not REDIS_AVAILABLE:
        return None
    
    try:
        cache_key = _get_cache_key(api_key)
        org_id = _redis_client.get(cache_key)
        return org_id
    except Exception as e:
        print(f"⚠️  Cache read error: {e}")
        return None


def _cache_org(api_key: str, org_id: str, ttl_seconds: int = 3600) -> None:
    """
    Cache organization UUID in Redis.
    
    Args:
        api_key: Plain text API key
        org_id: Organization UUID string
        ttl_seconds: Time-to-live in seconds (default 1 hour)
    """
    if not REDIS_AVAILABLE:
        return
    
    try:
        cache_key = _get_cache_key(api_key)
        _redis_client.setex(cache_key, ttl_seconds, org_id)
    except Exception as e:
        print(f"⚠️  Cache write error: {e}")


def _invalidate_cache(api_key: str) -> None:
    """Invalidate cached organization for API key (on logout/key revocation)."""
    if not REDIS_AVAILABLE:
        return
    
    try:
        cache_key = _get_cache_key(api_key)
        _redis_client.delete(cache_key)
    except Exception as e:
        print(f"⚠️  Cache delete error: {e}")


# ============================================================================
# Main Dependency: get_current_org
# ============================================================================

def get_current_org(
    request: Request,
    db: Session = Depends(lambda: SessionLocal())
) -> OrgContext:
    """
    FastAPI dependency to extract and verify organization from API key.
    
    Flow:
    1. Extract API key from Authorization header
    2. Check Redis cache for org_id (1 hour TTL)
    3. If not cached, query database and verify bcrypt hash
    4. Cache result in Redis
    5. Return OrgContext for use in route handlers
    
    Raises:
        HTTPException 401: Invalid or missing API key
        HTTPException 403: Organization inactive
        
    Usage in routes:
        @app.get("/scans")
        def list_scans(current_org: OrgContext = Depends(get_current_org)):
            # current_org is now available with org_id, tier, etc.
            pass
    """
    
    # Step 1: Extract API key from header
    api_key = extract_api_key(request)
    
    # Step 2: Check Redis cache first
    cached_org_id = _get_cached_org(api_key)
    if cached_org_id:
        try:
            org = db.query(Organization).filter(
                Organization.id == UUID(cached_org_id)
            ).first()
            
            if org and org.is_active:
                db.close()
                return OrgContext(
                    id=org.id,
                    name=org.name,
                    tier=org.tier,
                    max_projects=org.limits.get("max_projects", 3),
                    max_scans_per_month=org.limits.get("max_scans_per_month", 100),
                    is_active=org.is_active,
                )
            else:
                _invalidate_cache(api_key)
        except Exception as e:
            print(f"⚠️  Cache hit error: {e}")
    
    # Step 3: Not in cache, query database
    try:
        # For testing: check if api_key is a direct match (SHA256)
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        org = db.query(Organization).filter(
            Organization.api_key_hash == api_key_hash
        ).first()
        
        # If not found with SHA256, try bcrypt (for production keys)
        if not org:
            all_orgs = db.query(Organization).all()
            for candidate_org in all_orgs:
                if verify_api_key(api_key, candidate_org.api_key_hash):
                    org = candidate_org
                    break
        
        if not org:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Step 4: Verify organization is active
        if not org.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization is inactive",
            )
        
        # Step 5: Cache the result
        _cache_org(api_key, str(org.id))
        
        # Return organization context
        return OrgContext(
            id=org.id,
            name=org.name,
            tier=org.tier,
            max_projects=org.limits.get("max_projects", 3),
            max_scans_per_month=org.limits.get("max_scans_per_month", 100),
            is_active=org.is_active,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )
    finally:
        db.close()


# ============================================================================
# Org-Scoped Query Helper
# ============================================================================

def apply_org_filter(query, model, org_id: UUID):
    """
    Helper to apply org_id filter to any SQLAlchemy query.
    
    Usage:
        scans = apply_org_filter(
            db.query(Scan),
            Scan,
            current_org.id
        ).all()
    """
    if hasattr(model, 'org_id'):
        return query.filter(model.org_id == org_id)
    return query


# ============================================================================
# Testing Helpers
# ============================================================================

def create_test_api_key(org_id: str, prefix: str = "test_") -> str:
    """Create a test API key (uses SHA256 for easy testing)."""
    return f"{prefix}{org_id}"


def create_test_org_in_db(db: Session, name: str, tier: str = "free") -> tuple[Organization, str]:
    """
    Create a test organization and return (org, api_key).
    
    Note: For testing, we use SHA256 hashing instead of bcrypt.
    """
    test_org = Organization(
        name=name,
        tier=tier,
        api_key_hash=hashlib.sha256(f"test_{name}".encode()).hexdigest(),
        limits={
            "max_projects": 10,
            "max_scans_per_month": 1000,
        }
    )
    db.add(test_org)
    db.commit()
    db.refresh(test_org)
    
    return test_org, f"test_{name}"

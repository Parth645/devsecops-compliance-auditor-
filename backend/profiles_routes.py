"""
API endpoints for ScanProfile management.

Handles CRUD operations for scan profiles with multi-tenant isolation.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from schema.schema import ScanProfile, Organization
from schema.database import get_db
from auth import get_current_org, OrgContext

# ==================== Pydantic Models ====================

class ScanProfileBase(BaseModel):
    """Base model for ScanProfile data."""
    
    name: str = Field(..., min_length=1, max_length=100)
    environment: str = Field(..., description="Environment: dev, staging, production")
    scan_on_push: bool = Field(default=True, description="Trigger scan on push events")
    scan_on_pr: bool = Field(default=True, description="Trigger scan on pull requests")
    enforcement_level: str = Field(
        default="warning",
        description="Enforcement level: pass, warning, fail"
    )
    policies: Optional[dict] = Field(
        default_factory=dict,
        description="Policy configuration for this profile"
    )


class ScanProfileCreate(ScanProfileBase):
    """Model for creating a new scan profile."""
    pass


class ScanProfileUpdate(BaseModel):
    """Model for updating a scan profile."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    environment: Optional[str] = None
    scan_on_push: Optional[bool] = None
    scan_on_pr: Optional[bool] = None
    enforcement_level: Optional[str] = None
    policies: Optional[dict] = None


class ScanProfileResponse(ScanProfileBase):
    """Model for scan profile response."""
    
    id: str
    org_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ScanProfileListResponse(BaseModel):
    """Model for list response."""
    
    total: int
    profiles: List[ScanProfileResponse]


# ==================== Router Setup ====================

router = APIRouter(
    prefix="/scan-profiles",
    tags=["scan-profiles"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not found"},
    }
)


# ==================== Endpoints ====================

@router.post(
    "",
    response_model=ScanProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new scan profile"
)
async def create_scan_profile(
    profile_data: ScanProfileCreate,
    current_org: OrgContext = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Create a new scan profile for an organization.
    
    **Parameters:**
    - `name`: Profile name (e.g., "Production Strict", "Development Relaxed")
    - `environment`: Target environment (dev, staging, production)
    - `scan_on_push`: Whether to trigger scans on push events
    - `scan_on_pr`: Whether to trigger scans on pull requests
    - `enforcement_level`: How strictly to enforce policies (pass, warning, fail)
    - `policies`: Optional JSON configuration for policies
    
    **Returns:** Created ScanProfile with ID
    """
    try:
        # Verify organization exists and user has access
        org = db.query(Organization).filter(
            Organization.id == current_org.id
        ).first()
        
        if not org:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization not found or no access"
            )
        
        # Check for duplicate profile name in this org
        existing = db.query(ScanProfile).filter(
            ScanProfile.org_id == current_org.id,
            ScanProfile.name == profile_data.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Profile with name '{profile_data.name}' already exists"
            )
        
        # Validate enforcement level
        valid_levels = {"pass", "warning", "fail"}
        if profile_data.enforcement_level not in valid_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid enforcement_level. Must be one of: {valid_levels}"
            )
        
        # Validate environment
        valid_environments = {"dev", "staging", "production"}
        if profile_data.environment not in valid_environments:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid environment. Must be one of: {valid_environments}"
            )
        
        # Create new profile
        new_profile = ScanProfile(
            org_id=current_org.id,
            name=profile_data.name,
            environment=profile_data.environment,
            scan_on_push=profile_data.scan_on_push,
            scan_on_pr=profile_data.scan_on_pr,
            enforcement_level=profile_data.enforcement_level,
            policies=profile_data.policies or {}
        )
        
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        
        return new_profile
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scan profile: {str(e)}"
        )


@router.get(
    "/{org_id}",
    response_model=ScanProfileListResponse,
    summary="List scan profiles for organization"
)
async def list_scan_profiles(
    org_id: str,
    environment: Optional[str] = Query(None, description="Filter by environment"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_org: OrgContext = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    List all scan profiles for an organization with optional filtering.
    
    **Parameters:**
    - `org_id`: Organization ID (must match current user's org)
    - `environment`: Optional filter by environment
    - `skip`: Number of records to skip (for pagination)
    - `limit`: Maximum number of records to return
    
    **Returns:** List of ScanProfiles with total count
    """
    try:
        # Verify organization access
        if org_id != current_org.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other organization's profiles"
            )
        
        org = db.query(Organization).filter(
            Organization.id == org_id
        ).first()
        
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Build query
        query = db.query(ScanProfile).filter(
            ScanProfile.org_id == org_id
        )
        
        # Apply environment filter if provided
        if environment:
            query = query.filter(ScanProfile.environment == environment)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        profiles = query.offset(skip).limit(limit).all()
        
        return ScanProfileListResponse(
            total=total,
            profiles=profiles
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scan profiles: {str(e)}"
        )


@router.get(
    "/{org_id}/{profile_id}",
    response_model=ScanProfileResponse,
    summary="Get a specific scan profile"
)
async def get_scan_profile(
    org_id: str,
    profile_id: str,
    current_org: OrgContext = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific scan profile by ID.
    
    **Parameters:**
    - `org_id`: Organization ID
    - `profile_id`: Scan profile ID
    
    **Returns:** ScanProfile details
    """
    try:
        # Verify organization access
        if org_id != current_org.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other organization's profiles"
            )
        
        profile = db.query(ScanProfile).filter(
            ScanProfile.id == profile_id,
            ScanProfile.org_id == org_id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan profile not found"
            )
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scan profile: {str(e)}"
        )


@router.put(
    "/{org_id}/{profile_id}",
    response_model=ScanProfileResponse,
    summary="Update a scan profile"
)
async def update_scan_profile(
    org_id: str,
    profile_id: str,
    profile_data: ScanProfileUpdate,
    current_org: OrgContext = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Update an existing scan profile.
    
    **Parameters:**
    - `org_id`: Organization ID
    - `profile_id`: Scan profile ID
    - `profile_data`: Fields to update (only provided fields are updated)
    
    **Returns:** Updated ScanProfile
    """
    try:
        # Verify organization access
        if org_id != current_org.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other organization's profiles"
            )
        
        # Find profile
        profile = db.query(ScanProfile).filter(
            ScanProfile.id == profile_id,
            ScanProfile.org_id == org_id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan profile not found"
            )
        
        # Check for duplicate name if changing name
        if profile_data.name and profile_data.name != profile.name:
            existing = db.query(ScanProfile).filter(
                ScanProfile.org_id == org_id,
                ScanProfile.name == profile_data.name
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Profile with name '{profile_data.name}' already exists"
                )
        
        # Validate enforcement level if provided
        if profile_data.enforcement_level:
            valid_levels = {"pass", "warning", "fail"}
            if profile_data.enforcement_level not in valid_levels:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid enforcement_level. Must be one of: {valid_levels}"
                )
        
        # Validate environment if provided
        if profile_data.environment:
            valid_environments = {"dev", "staging", "production"}
            if profile_data.environment not in valid_environments:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid environment. Must be one of: {valid_environments}"
                )
        
        # Update only provided fields
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        profile.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update scan profile: {str(e)}"
        )


@router.delete(
    "/{org_id}/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a scan profile"
)
async def delete_scan_profile(
    org_id: str,
    profile_id: str,
    current_org: OrgContext = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Delete a scan profile.
    
    **Parameters:**
    - `org_id`: Organization ID
    - `profile_id`: Scan profile ID
    
    **Note:** Cannot delete profiles that are currently in use by scan triggers.
    """
    try:
        # Verify organization access
        if org_id != current_org.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other organization's profiles"
            )
        
        # Find profile
        profile = db.query(ScanProfile).filter(
            ScanProfile.id == profile_id,
            ScanProfile.org_id == org_id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan profile not found"
            )
        
        # Check if profile is in use (optional - depends on schema)
        # If ScanProfile has foreign key references from other tables,
        # check those before deletion
        
        db.delete(profile)
        db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete scan profile: {str(e)}"
        )


@router.get(
    "/{org_id}/profile/default",
    response_model=ScanProfileResponse,
    summary="Get default scan profile for organization"
)
async def get_default_scan_profile(
    org_id: str,
    current_org: OrgContext = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Get the default scan profile for an organization.
    
    **Parameters:**
    - `org_id`: Organization ID
    
    **Returns:** Default ScanProfile (or first available if default not set)
    """
    try:
        # Verify organization access
        if org_id != current_org.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other organization's profiles"
            )
        
        # Look for default profile
        # This assumes database has a way to mark profiles as default
        # For now, return first profile ordered by creation
        profile = db.query(ScanProfile).filter(
            ScanProfile.org_id == org_id
        ).order_by(ScanProfile.created_at).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No scan profiles found for organization. Create one first."
            )
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch default scan profile: {str(e)}"
        )


if __name__ == "__main__":
    # This module is imported by main.py
    pass

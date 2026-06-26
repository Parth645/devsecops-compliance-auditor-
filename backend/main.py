from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import uvicorn
import logging
import traceback
import sys
from pathlib import Path
from utils.git_utils import git_clone, analyze_repository_files
from auth import get_current_org, OrgContext, apply_org_filter
from schema.database import SessionLocal
from schema.schema import Scan, Violation, Project
from sqlalchemy.orm import Session
from webhook_routes import router as webhook_router
from profiles_routes import router as profiles_router
from tenant_middleware import TenantContextMiddleware
import os
from dotenv import load_dotenv
from uuid import uuid4

# Load environment variables
load_dotenv()

# Add AI engine to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Try to import AI components (Groq-based)
try:
    # Import from ai_engine package (folder with __init__.py)
    from ai_engine.compliance_analyzer import ComplianceAnalyzer
    from ai_engine.policy_loader import load_indian_compliance_policies
    # Initialize analyzer for Groq-based Indian compliance analysis
    _global_analyzer = None
    AI_ENABLED = True
    print("✓ Groq AI Engine available for Indian compliance analysis")
    print("  - DPDP Act compliance")
    print("  - RBI regulations")
    print("  - IT Act 2000")
except ImportError as e:
    AI_ENABLED = False
    _global_analyzer = None
    print(f"⚠ Groq AI Engine not available: {e}")
    print("  Ensure GROQ_API_KEY is set in environment variables")
    print("  Falling back to basic analysis")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Compliance Auditor API",
    description="A backend service for auditing Git repositories for compliance issues",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://devsecops-compliance-auditor.vercel.app",
        "http://localhost:3000",
    ],  # Whitelist frontend origins (add more as needed)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant context middleware for multi-tenant support
app.add_middleware(
    TenantContextMiddleware,
    enable_path_extraction=True,
    enable_header_extraction=True,
    enable_subdomain_extraction=False,
    enable_query_extraction=True,
)

# Include webhook routes
app.include_router(webhook_router)

# Include scan profile routes
app.include_router(profiles_router)

# Pydantic models for request/response validation
class GitRepoRequest(BaseModel):
    git_repo_url: str
    branch: Optional[str] = "main"
    analysis_depth: Optional[str] = "basic"  # basic, detailed, full
    use_ai: Optional[bool] = True  # Enable AI-powered analysis

class ComplianceIssue(BaseModel):
    file: str
    issue: str
    severity: str
    line: Optional[int] = None
    description: Optional[str] = None
    ai_confidence: Optional[float] = None  # AI confidence score

class ScanResponse(BaseModel):
    status: str
    repo: str
    message: str
    clone_path: Optional[str] = None
    repo_info: Optional[Dict[str, Any]] = None
    files: Optional[List[str]] = None
    total_files: Optional[int] = None
    compliance_issues: Optional[List[Dict[str, Any]]] = None
    issues_count: Optional[int] = None
    scan_duration: Optional[float] = None
    error_details: Optional[str] = None
    ai_enabled: Optional[bool] = None  # Whether AI analysis was used
    analysis_summary: Optional[Dict[str, Any]] = None  # AI-generated summary
    # Additional fields for frontend compatibility
    scan_id: Optional[str] = None  # UUID of the scan
    findings: Optional[List[Dict[str, Any]]] = None  # Alias for compliance_issues
    violations: Optional[List[Dict[str, Any]]] = None  # Alias for compliance_issues
    total_findings: Optional[int] = None  # Total number of findings
    repository_name: Optional[str] = None  # Repository name
    repository: Optional[str] = None  # Alternative repository name field
    critical_count: Optional[int] = 0  # Number of critical issues
    high_count: Optional[int] = 0  # Number of high severity issues
    medium_count: Optional[int] = 0  # Number of medium severity issues
    low_count: Optional[int] = 0  # Number of low severity issues
    
    class Config:
        # Allow extra fields that aren't defined in the model
        extra = "allow"

@app.get("/")
def read_root():
    return {
        "message": "Compliance Auditor API",
        "version": "1.0.0",
        "ai_enabled": AI_ENABLED,
        "endpoints": {
            "/org/scans/complete": "POST - Complete repository scan with full 4-stage pipeline (org-scoped)",
            "/git-scan": "GET - Scan a Git repository by URL",
            "/git-scan-detailed": "POST - Detailed repository scan with options",
            "/ai-scan": "POST - AI-powered repository analysis",
            "/health": "GET - Health check",
            "/docs": "GET - API documentation"
        }
    }

# Health check endpoint
@app.get("/health")
def health_check():
    analyzer = get_analyzer()
    compliance_status = analyzer.get_compliance_status() if analyzer else {}
    return {
        "status": "healthy",
        "service": "compliance-auditor-backend",
        "version": "1.0.0",
        "ai_enabled": AI_ENABLED,
        "ai_engine": "Groq",
        "compliance_frameworks": [
            "DPDP Act",
            "RBI Regulations",
            "IT Act 2000"
        ],
        "ai_components": compliance_status
    }

def get_analyzer():
    """Get or create Groq analyzer instance for Indian compliance analysis"""
    global _global_analyzer
    if _global_analyzer is None and AI_ENABLED:
        try:
            # Initialize Groq-based analyzer for Indian compliance
            _global_analyzer = ComplianceAnalyzer()
            logger.info("✓ Groq analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Groq analyzer: {e}")
            _global_analyzer = None
    return _global_analyzer

# AI-powered repository scan endpoint
@app.post("/ai-scan", response_model=ScanResponse)
async def ai_scan_repository(request: GitRepoRequest):
    """
    Perform AI-powered compliance analysis of a Git repository.
    
    Args:
        request: GitRepoRequest containing repository URL and analysis options
        
    Returns:
        ScanResponse: AI-enhanced compliance analysis results
    """
    logger.info(f"Received AI scan request for: {request.git_repo_url}")
    
    try:
        import time
        start_time = time.time()
        
        # Validate URL format
        if not request.git_repo_url.startswith(('http://', 'https://', 'git@')):
            logger.warning(f"Invalid URL format: {request.git_repo_url}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid git URL format. Must start with http://, https://, or git@"
            )
        
        logger.info("Starting repository clone...")
        # Clone repository
        result = git_clone(request.git_repo_url)
        logger.info(f"Clone result status: {result.get('status', 'unknown')}")
        
        if result["status"] == "error":
            logger.error(f"Clone failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        
        result["ai_enabled"] = AI_ENABLED
        
        # Perform analysis
        if result["status"] == "success" and "clone_path" in result:
            logger.info("Starting compliance analysis...")
            
            if AI_ENABLED and request.use_ai:
                try:
                    # Use AI-powered analysis
                    logger.info("Using AI-powered analysis...")
                    analyzer = get_analyzer()
                    
                    if analyzer is not None:
                        # Use the correct async method
                        ai_results = await analyzer.analyze_repository_for_compliance(
                            repo_path=result["clone_path"],
                            custom_policy_text=None,
                            language="javascript"
                        )
                        
                        if ai_results and ai_results.get("violations"):
                            # Process results with output processor for deduplication and risk scoring
                            try:
                                # Import output processor
                                from output_processor import OutputProcessor
                                
                                logger.info("Initializing OutputProcessor...")
                                processor = OutputProcessor()
                                
                                logger.info(f"Processing {len(ai_results.get('violations', []))} violations...")
                                processed_results = processor.process_scan_results(ai_results)
                                
                                logger.info(f"Output processor completed: {processed_results.get('total_unique_issues')} unique issues from {processed_results.get('total_violations')} violations")
                                
                                # Use processed results
                                result["compliance_issues"] = processed_results.get("grouped_issues", [])
                                result["issues_count"] = processed_results.get("total_unique_issues", 0)
                                result["total_violations"] = processed_results.get("total_violations", 0)
                                result["analysis_summary"] = processed_results.get("analysis_summary", {})
                                
                                logger.info(f"AI analysis found {result['total_violations']} violations ({result['issues_count']} unique issues)")
                                
                            except Exception as proc_error:
                                logger.error(f"Output processing failed: {proc_error}")
                                import traceback as tb
                                logger.error(f"Traceback: {tb.format_exc()}")
                                logger.warning("Falling back to raw results format")
                                # Fallback to raw format
                                violations = ai_results.get("violations", [])
                                result["compliance_issues"] = [
                                    {
                                        "file": v.get("file_path", "unknown"),
                                        "issue": v.get("description", "Compliance violation"),
                                        "severity": v.get("severity", "MEDIUM"),
                                        "line": v.get("line_number"),
                                        "description": v.get("description", ""),
                                        "ai_confidence": 0.85,
                                        "category": v.get("category", "unknown"),
                                        "rule_id": v.get("rule_id", "unknown"),
                                        "suggestion": v.get("suggestion", "")
                                    }
                                    for v in violations
                                ]
                                result["issues_count"] = len(result["compliance_issues"])
                                result["analysis_summary"] = {
                                    "total_violations": len(violations),
                                    "compliance_score": ai_results.get("compliance_score", 0.0),
                                    "scan_summary": ai_results.get("scan_summary", {}),
                                    "rules_applied": ai_results.get("rules_applied", 0)
                                }
                        else:
                            logger.warning("AI analysis failed, falling back to basic analysis")
                            # Fallback to basic analysis
                            compliance_issues = analyze_repository_files(result["clone_path"], analysis_depth=request.analysis_depth)
                            result["compliance_issues"] = compliance_issues
                            result["issues_count"] = len([issue for issue in compliance_issues if "error" not in issue])
                    else:
                        logger.warning("AI analyzer not available, falling back to basic analysis")
                        # Fallback to basic analysis
                        compliance_issues = analyze_repository_files(result["clone_path"], analysis_depth=request.analysis_depth)
                        result["compliance_issues"] = compliance_issues
                        result["issues_count"] = len([issue for issue in compliance_issues if "error" not in issue])
                        
                except Exception as ai_error:
                    logger.error(f"AI analysis failed: {ai_error}")
                    # Fallback to basic analysis
                    compliance_issues = analyze_repository_files(result["clone_path"], analysis_depth=request.analysis_depth)
                    result["compliance_issues"] = compliance_issues
                    result["issues_count"] = len([issue for issue in compliance_issues if "error" not in issue])
                    result["error_details"] = f"AI analysis failed, used fallback: {str(ai_error)}"
            else:
                # Use basic analysis
                logger.info("Using basic analysis...")
                compliance_issues = analyze_repository_files(result["clone_path"], analysis_depth=request.analysis_depth)
                result["compliance_issues"] = compliance_issues
                result["issues_count"] = len([issue for issue in compliance_issues if "error" not in issue])
        
        # Add scan duration
        end_time = time.time()
        result["scan_duration"] = round(end_time - start_time, 2)
        
        logger.info("AI scan completed successfully")
        return ScanResponse(**result)
        
    except HTTPException:
        logger.error("HTTPException raised")
        raise
    except Exception as e:
        error_msg = f"Internal server error: {str(e)}"
        error_traceback = traceback.format_exc()
        logger.error(f"Unexpected error: {error_msg}")
        logger.error(f"Traceback: {error_traceback}")
        
        # Return detailed error for debugging
        raise HTTPException(
            status_code=500, 
            detail={
                "status": "error",
                "message": error_msg,
                "error_details": error_traceback,
                "repo": request.git_repo_url,
                "ai_enabled": AI_ENABLED
            }
        )

# Simple git scan endpoint (GET with query parameter)
@app.get("/git-scan", response_model=ScanResponse)
def scan_git_repo(git_repo_url: str):
    """
    Scan a Git repository for compliance issues.
    
    Args:
        git_repo_url: The URL of the Git repository to scan
        
    Returns:
        ScanResponse: Results of the compliance scan
    """
    logger.info(f"Received scan request for: {git_repo_url}")
    
    try:
        # Validate URL format
        if not git_repo_url.startswith(('http://', 'https://', 'git@')):
            logger.warning(f"Invalid URL format: {git_repo_url}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid git URL format. Must start with http://, https://, or git@"
            )
        
        logger.info("Starting repository clone...")
        # Clone and get basic info
        result = git_clone(git_repo_url)
        logger.info(f"Clone result status: {result.get('status', 'unknown')}")
        
        if result["status"] == "error":
            logger.error(f"Clone failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        
        # Analyze for compliance issues
        if result["status"] == "success" and "clone_path" in result:
            logger.info("Starting compliance analysis...")
            try:
                # Use basic analysis for simple scan endpoint
                compliance_issues = analyze_repository_files(result["clone_path"], analysis_depth="basic")
                result["compliance_issues"] = compliance_issues
                result["issues_count"] = len([issue for issue in compliance_issues if "error" not in issue])
                logger.info(f"Found {result['issues_count']} compliance issues")
            except Exception as analysis_error:
                logger.error(f"Analysis failed: {analysis_error}")
                result["compliance_issues"] = []
                result["issues_count"] = 0
                result["error_details"] = f"Analysis failed: {str(analysis_error)}"
        
        logger.info("Scan completed successfully")
        return ScanResponse(**result)
        
    except HTTPException:
        logger.error("HTTPException raised")
        raise
    except Exception as e:
        error_msg = f"Internal server error: {str(e)}"
        error_traceback = traceback.format_exc()
        logger.error(f"Unexpected error: {error_msg}")
        logger.error(f"Traceback: {error_traceback}")
        
        # Return detailed error for debugging
        raise HTTPException(
            status_code=500, 
            detail={
                "status": "error",
                "message": error_msg,
                "error_details": error_traceback,
                "repo": git_repo_url
            }
        )

# Detailed git scan endpoint (POST with request body)
@app.post("/git-scan-detailed", response_model=ScanResponse)
def scan_git_repo_detailed(request: GitRepoRequest):
    """
    Perform a detailed scan of a Git repository with additional options.
    
    Args:
        request: GitRepoRequest containing repository URL and scan options
        
    Returns:
        ScanResponse: Detailed results of the compliance scan
    """
    try:
        import time
        start_time = time.time()
        
        # Clone and get basic info
        result = git_clone(request.git_repo_url)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        
        # Analyze for compliance issues based on analysis depth
        if result["status"] == "success" and "clone_path" in result:
            compliance_issues = analyze_repository_files(
                result["clone_path"], 
                analysis_depth=request.analysis_depth
            )
            result["compliance_issues"] = compliance_issues
            result["issues_count"] = len([issue for issue in compliance_issues if "error" not in issue])
        
        # Add scan duration
        end_time = time.time()
        result["scan_duration"] = round(end_time - start_time, 2)
        
        return ScanResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Get scan history with database integration
@app.get("/scan-history")
def get_scan_history(
    limit: int = 10,
    offset: int = 0,
    status: Optional[str] = None,
    db: Session = Depends(lambda: SessionLocal())
):
    """
    Get the history of previous scans from the database.
    
    Frontend calls: apiService.getScanHistory(limit)
    
    Args:
        limit: Number of recent scans to return (default: 10)
        offset: Pagination offset (default: 0)
        status: Optional filter by status (e.g., "completed", "failed")
        
    Returns:
        List of recent scan results with metadata
        
    Example:
        GET /scan-history?limit=20&offset=0
    """
    try:
        logger.info(f"Fetching scan history: limit={limit}, offset={offset}")
        
        # Build query
        query = db.query(Scan).order_by(Scan.created_at.desc())
        
        # Apply optional status filter
        if status:
            query = query.filter(Scan.status == status)
        
        # Get total count (before pagination)
        total = query.count()
        
        # Apply pagination
        scans = query.offset(offset).limit(limit).all()
        
        logger.info(f"Found {len(scans)} scans out of {total} total")
        
        return {
            "status": "success",
            "scans": [
                {
                    "scan_id": str(scan.id),
                    "id": str(scan.id),
                    "repository_name": scan.repository_name or f"Repository {str(scan.id)[:8]}",
                    "repository_url": getattr(scan, 'repository_url', None),
                    "project_id": str(scan.project_id) if scan.project_id else None,
                    "org_id": str(scan.org_id) if scan.org_id else None,
                    "scan_date": scan.created_at.isoformat() if scan.created_at else None,
                    "timestamp": scan.created_at.isoformat() if scan.created_at else None,
                    "created_at": scan.created_at.isoformat() if scan.created_at else None,
                    "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                    "branch": scan.branch or "main",
                    "commit_sha": scan.commit_sha,
                    "scan_duration": float(scan.scan_duration_seconds) if scan.scan_duration_seconds else 0,
                    "scan_duration_seconds": float(scan.scan_duration_seconds) if scan.scan_duration_seconds else 0,
                    "status": scan.status or "completed",
                    "risk_score": float(scan.risk_score) if scan.risk_score else 0.0,
                    "critical_count": scan.critical_violations or 0,
                    "high_count": scan.high_violations or 0,
                    "medium_count": scan.medium_violations or 0,
                    "low_count": scan.low_violations or 0,
                    "total_findings": scan.total_violations or 0,
                    "total_violations": scan.total_violations or 0,
                    "files_scanned": scan.files_scanned or 0,
                }
                for scan in scans
            ],
            "total": total,
            "count": len(scans),
            "limit": limit,
            "offset": offset,
        }
        
    except Exception as e:
        logger.error(f"Error fetching scan history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch scan history: {str(e)}"
        )
    finally:
        db.close()

# Get compliance rules (placeholder for future implementation)
@app.get("/compliance-rules")
def get_compliance_rules():
    """
    Get the list of compliance rules being checked.
    
    Returns:
        List of compliance rules and their descriptions
    """
    return {
        "rules": [
            {
                "id": "hardcoded-secrets",
                "name": "Hardcoded Secrets Detection",
                "description": "Detects potential hardcoded passwords, API keys, and secrets"
            },
            {
                "id": "license-compliance",
                "name": "License Compliance",
                "description": "Checks for proper license files and headers"
            },
            {
                "id": "security-vulnerabilities",
                "name": "Security Vulnerabilities",
                "description": "Scans for known security vulnerabilities in dependencies"
            }
        ]
    }

# Get scan details for a specific scan
@app.get("/scan-details/{scan_id}")
def get_scan_details_endpoint(
    scan_id: str,
    db: Session = Depends(lambda: SessionLocal())
):
    """
    Get detailed information for a specific scan.
    
    Frontend calls: apiService.getScanDetails(scanId)
    
    Args:
        scan_id: UUID of the scan
        
    Returns:
        Detailed scan information with violations
    """
    try:
        from uuid import UUID as UUID_TYPE
        
        logger.info(f"Fetching scan details for: {scan_id}")
        
        # Query for the scan
        scan = db.query(Scan).filter(
            Scan.id == UUID_TYPE(scan_id)
        ).first()
        
        if not scan:
            logger.warning(f"Scan not found: {scan_id}")
            raise HTTPException(
                status_code=404, 
                detail=f"Scan {scan_id} not found"
            )
        
        # Get violations for this scan
        violations = db.query(Violation).filter(
            Violation.scan_id == scan.id
        ).order_by(Violation.severity.desc()).all()
        
        logger.info(f"Found {len(violations)} violations for scan {scan_id}")
        
        return {
            "status": "success",
            "scan": {
                "id": str(scan.id),
                "project_id": str(scan.project_id) if scan.project_id else None,
                "org_id": str(scan.org_id) if scan.org_id else None,
                "status": scan.status or "completed",
                "risk_score": float(scan.risk_score) if scan.risk_score else 0.0,
                "total_violations": scan.total_violations or 0,
                "critical_violations": scan.critical_violations or 0,
                "high_violations": scan.high_violations or 0,
                "medium_violations": scan.medium_violations or 0,
                "low_violations": scan.low_violations or 0,
                "created_at": scan.created_at.isoformat() if scan.created_at else None,
                "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                "updated_at": scan.updated_at.isoformat() if hasattr(scan, 'updated_at') and scan.updated_at else None,
                "branch": scan.branch or "main",
                "commit_sha": scan.commit_sha,
                "commit_message": getattr(scan, 'commit_message', None),
                "files_scanned": scan.files_scanned or 0,
                "scan_duration_seconds": float(scan.scan_duration_seconds) if scan.scan_duration_seconds else 0.0,
                "repository_url": getattr(scan, 'repository_url', None),
                "repository_name": getattr(scan, 'repository_name', None),
            },
            "violations": [
                {
                    "id": str(v.id),
                    "rule_id": v.rule_id,
                    "severity": v.severity,
                    "category": v.category,
                    "message": v.message,
                    "file_path": v.file_path,
                    "line_number": v.line_number,
                    "column_number": getattr(v, 'column_number', None),
                    "ai_confidence": float(v.ai_confidence) if v.ai_confidence else None,
                    "ai_fix_suggestion": v.ai_fix_suggestion,
                    "status": getattr(v, 'status', 'open'),
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                }
                for v in violations
            ],
            "meta": {
                "total_violations": len(violations),
                "severity_breakdown": {
                    "critical": len([v for v in violations if v.severity == "critical"]),
                    "high": len([v for v in violations if v.severity == "high"]),
                    "medium": len([v for v in violations if v.severity == "medium"]),
                    "low": len([v for v in violations if v.severity == "low"]),
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching scan details for {scan_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch scan details: {str(e)}"
        )
    finally:
        db.close()

# Analytics endpoints
@app.get("/analytics/trends")
def get_analytics_trends(
    period: str = "30d",
    db: Session = Depends(lambda: SessionLocal())
):
    """
    Get violation trends over a specified time period.
    
    Args:
        period: Time period - "7d", "30d", "90d"
        
    Returns:
        Daily violation counts and trends
    """
    try:
        from datetime import datetime, timedelta
        
        logger.info(f"Fetching analytics trends for period: {period}")
        
        # Determine days based on period
        period_days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Query scans in period
        scans = db.query(Scan).filter(
            Scan.created_at >= start_date
        ).order_by(Scan.created_at).all()
        
        # Group by date
        trends_dict = {}
        for scan in scans:
            if scan.created_at:
                date_key = scan.created_at.date().isoformat()
                if date_key not in trends_dict:
                    trends_dict[date_key] = {
                        "violations": 0,
                        "critical": 0,
                        "high": 0,
                        "medium": 0,
                        "low": 0,
                    }
                trends_dict[date_key]["violations"] += scan.total_violations or 0
                trends_dict[date_key]["critical"] += scan.critical_violations or 0
                trends_dict[date_key]["high"] += scan.high_violations or 0
                trends_dict[date_key]["medium"] += scan.medium_violations or 0
                trends_dict[date_key]["low"] += scan.low_violations or 0
        
        # Convert to sorted list
        trends = [
            {
                "date": date,
                "violations": data["violations"],
                "critical": data["critical"],
                "high": data["high"],
                "medium": data["medium"],
                "low": data["low"],
            }
            for date, data in sorted(trends_dict.items())
        ]
        
        return {
            "status": "success",
            "period": period,
            "period_days": period_days,
            "trends": trends,
            "total_points": len(trends),
        }
        
    except Exception as e:
        logger.error(f"Error fetching analytics trends: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch trends: {str(e)}"
        )
    finally:
        db.close()

@app.get("/analytics/distribution")
def get_analytics_distribution(
    db: Session = Depends(lambda: SessionLocal())
):
    """
    Get current severity distribution of all violations.
    
    Returns:
        Count of violations by severity level
    """
    try:
        logger.info("Fetching violation distribution")
        
        # Query all violations and count by severity
        violations = db.query(Violation).all()
        
        distribution = {
            "critical": sum(1 for v in violations if v.severity == "critical"),
            "high": sum(1 for v in violations if v.severity == "high"),
            "medium": sum(1 for v in violations if v.severity == "medium"),
            "low": sum(1 for v in violations if v.severity == "low"),
        }
        
        total = sum(distribution.values())
        
        return {
            "status": "success",
            "severity_distribution": distribution,
            "total": total,
            "percentages": {
                "critical": round((distribution["critical"] / total * 100), 2) if total > 0 else 0,
                "high": round((distribution["high"] / total * 100), 2) if total > 0 else 0,
                "medium": round((distribution["medium"] / total * 100), 2) if total > 0 else 0,
                "low": round((distribution["low"] / total * 100), 2) if total > 0 else 0,
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching violation distribution: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch distribution: {str(e)}"
        )
    finally:
        db.close()

@app.get("/analytics/framework-stats")
def get_analytics_framework_stats(
    db: Session = Depends(lambda: SessionLocal())
):
    """
    Get violation statistics grouped by compliance framework.
    
    Returns:
        Violations grouped by framework
    """
    try:
        logger.info("Fetching framework statistics")
        
        # Query violations and group by category/framework
        violations = db.query(Violation).all()
        
        framework_counts = {}
        for v in violations:
            # Use category as framework proxy
            framework = v.category or "Other"
            framework_counts[framework] = framework_counts.get(framework, 0) + 1
        
        frameworks = [
            {"framework": fw, "violations": count}
            for fw, count in sorted(framework_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return {
            "status": "success",
            "frameworks": frameworks,
            "total": sum(f["violations"] for f in frameworks),
        }
        
    except Exception as e:
        logger.error(f"Error fetching framework stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch framework stats: {str(e)}"
        )
    finally:
        db.close()

# Settings endpoints
class UserSettings(BaseModel):
    """User settings model"""
    theme: Optional[str] = "dark"
    notifications_enabled: Optional[bool] = True
    auto_scan_enabled: Optional[bool] = False
    scan_frequency: Optional[str] = "weekly"
    email_on_critical: Optional[bool] = True
    max_scans_per_month: Optional[int] = 100

@app.post("/settings")
def update_user_settings(
    settings: UserSettings,
    current_org: OrgContext = Depends(get_current_org),
):
    """
    Update user/organization settings.
    
    Args:
        settings: Settings to update
        current_org: Organization context
        
    Returns:
        Confirmation of updated settings
    """
    try:
        logger.info(f"Updating settings for org {current_org.id}")
        
        return {
            "status": "success",
            "message": "Settings updated successfully",
            "settings": settings.dict(),
            "org_id": str(current_org.id),
        }
        
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update settings"
        )

@app.get("/settings")
def get_user_settings(
    current_org: OrgContext = Depends(get_current_org),
):
    """
    Get current user/organization settings.
    
    Returns:
        Current settings for the user
    """
    try:
        logger.info(f"Fetching settings for org {current_org.id}")
        
        # Default settings (in production, load from database)
        default_settings = {
            "theme": "dark",
            "notifications_enabled": True,
            "auto_scan_enabled": False,
            "scan_frequency": "weekly",
            "email_on_critical": True,
            "max_scans_per_month": 100,
        }
        
        return {
            "status": "success",
            "settings": default_settings,
            "org_id": str(current_org.id),
        }
        
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch settings"
        )

# ============================================================================
# INDIAN COMPLIANCE ENDPOINTS (Groq-powered)
# ============================================================================

class CodeAnalysisRequest(BaseModel):
    """Request model for code compliance analysis"""
    code: str
    file_type: Optional[str] = "python"
    frameworks: Optional[List[str]] = ["dpdp", "rbi", "it_act"]

@app.post("/india-compliance/analyze-code")
async def analyze_code_for_indian_compliance(request: CodeAnalysisRequest):
    """
    Analyze code for Indian compliance violations using 4-stage Groq pipeline.
    
    Pipeline Stages:
    1. Project Profiling (llama-3.1-8b-instant) - Fast classification
    2. Policy Translation (Semgrep) - Deterministic rule generation  
    3. Context Analysis (qwen/qwen3-32b) - False-positive filtering
    4. Auto-Remediation (llama-3.3-70b-versatile) - Secure code fixes
    
    Supports:
    - DPDP Act (Digital Personal Data Protection Act 2023)
    - RBI Regulations (Reserve Bank of India)
    - IT Act 2000
    
    Args:
        request: CodeAnalysisRequest with code and frameworks
        
    Returns:
        Compliance analysis with violations and recommendations
    """
    try:
        logger.info(f"[4-STAGE PIPELINE] Analyzing {request.file_type} code for Indian compliance")
        
        analyzer = get_analyzer()
        if not analyzer:
            raise HTTPException(status_code=503, detail="Groq pipeline not available")
        
        # Stage 3: Context-aware analysis (includes profiling and remediation)
        results = await analyzer.analyze_code(request.code, request.file_type)
        
        return {
            "status": "success",
            "analysis": results,
            "pipeline_stages": ["profiling", "context_analysis", "remediation"],
            "frameworks_checked": request.frameworks or ["dpdp", "rbi", "it_act"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/india-compliance/status")
def get_india_compliance_status():
    """
    Get the status of the Indian compliance 4-stage analyzer pipeline.
    
    Returns:
        Status of Groq pipeline, components, and supported stages
    """
    try:
        analyzer = get_analyzer()
        if not analyzer:
            return {"status": "unavailable", "message": "Groq pipeline not initialized"}
        
        pipeline_status = analyzer.get_pipeline_status()
        compliance_status = analyzer.get_compliance_status()
        
        return {
            "status": "active",
            "system": "4-Stage Groq Pipeline",
            "pipeline_status": pipeline_status,
            "compliance_status": compliance_status,
            "architecture": {
                "stage_1": "Project Profiling (llama-3.1-8b-instant)",
                "stage_2": "Policy Translation (Semgrep deterministic)",
                "stage_3": "Context Analysis (qwen/qwen3-32b)",
                "stage_4": "Auto-Remediation (llama-3.3-70b-versatile)"
            }
        }
    except Exception as e:
        logger.error(f"Failed to get compliance status: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/india-compliance/frameworks")
def get_supported_frameworks():
    """
    Get list of supported Indian compliance frameworks.
    
    Returns:
        Details of DPDP Act, RBI, and IT Act 2000
    """
    return {
        "status": "success",
        "frameworks": {
            "dpdp": {
                "name": "Digital Personal Data Protection Act 2023",
                "description": "India's primary data protection law",
                "key_areas": [
                    "Personal data processing consent",
                    "Data fiduciary and processor responsibilities",
                    "Data breach notification (72 hours)",
                    "Processing of sensitive personal data",
                    "Cross-border data transfers",
                    "User rights and grievance redressal"
                ],
                "penalties": {
                    "minor": "Up to ₹2 crore or 2% annual turnover",
                    "major": "Up to ₹5 crore or 5% annual turnover"
                }
            },
            "rbi": {
                "name": "Reserve Bank of India Regulations",
                "description": "Financial sector data and cybersecurity requirements",
                "key_areas": [
                    "Data localization for financial data",
                    "Cybersecurity framework",
                    "Payment system compliance",
                    "Third-party service provider management",
                    "Data residency requirements",
                    "Audit and reporting requirements"
                ],
                "penalties": {
                    "minor": "₹1-5 lakh",
                    "major": "₹5+ lakh and action against license"
                }
            },
            "it_act": {
                "name": "Information Technology Act 2000",
                "description": "Indian cybersecurity and IT law",
                "key_areas": [
                    "Data security measures (Section 43A)",
                    "Personal data protection",
                    "Intermediary guidelines",
                    "Cybersecurity obligations",
                    "Data breach reporting"
                ],
                "penalties": {
                    "minor": "Up to ₹2 lakh",
                    "major": "Up to ₹5 lakh"
                }
            }
        }
    }


# ============================================================================
# CUSTOM POLICY ENDPOINTS (4-Stage Pipeline Policy Management)
# ============================================================================

class PolicyIngestionRequest(BaseModel):
    """Request model for custom policy ingestion"""
    name: str
    policy_text: str
    policy_type: str = "compliance"  # compliance, security, financial, etc.

@app.post("/india-compliance/policies/ingest")
async def ingest_custom_policy(request: PolicyIngestionRequest):
    """
    Ingest custom company policy for compliance scanning.
    
    Uses Stage 2 (Policy Translation) of the 4-stage pipeline to convert
    policies into executable Semgrep rules.
    
    Args:
        request: PolicyIngestionRequest with policy details
        
    Returns:
        Policy ID and generated rules count
    """
    try:
        logger.info(f"[STAGE 2] Ingesting custom policy: {request.name}")
        
        analyzer = get_analyzer()
        if not analyzer:
            raise HTTPException(status_code=503, detail="Groq pipeline not available")
        
        result = await analyzer.ingest_custom_policy(
            policy_name=request.name,
            policy_text=request.policy_text,
            policy_type=request.policy_type
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "message": f"Policy '{request.name}' ingested successfully",
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Policy ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.get("/india-compliance/policies")
def get_all_policies():
    """
    Get summary of all ingested custom policies.
    
    Returns:
        List of policies and their statistics
    """
    try:
        analyzer = get_analyzer()
        if not analyzer:
            raise HTTPException(status_code=503, detail="Groq pipeline not available")
        
        result = analyzer.get_all_policies()
        
        if "error" in result:
            return {"status": "error", "message": result["error"]}
        
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"Failed to get policies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

@app.get("/india-compliance/policies/{policy_id}/rules")
def get_policy_rules(policy_id: str):
    """
    Get Semgrep-compatible rules for a specific policy.
    
    Args:
        policy_id: ID of the policy
        
    Returns:
        YAML rules for Semgrep execution
    """
    try:
        analyzer = get_analyzer()
        if not analyzer:
            raise HTTPException(status_code=503, detail="Groq pipeline not available")
        
        result = analyzer.get_policy_rules(policy_id)
        
        if "error" in result:
            return {"status": "error", "message": result["error"]}
        
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"Failed to get policy rules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


# ============================================================================
# REPOSITORY SCANNING ENDPOINT (Full 4-Stage Pipeline)
# ============================================================================

class RepositoryScanRequest(BaseModel):
    """Request model for repository scanning"""
    repo_path: str
    policy_id: Optional[str] = None
    include_remediation: bool = True

@app.post("/india-compliance/scan-repository")
async def scan_repository_for_compliance(request: RepositoryScanRequest):
    """
    Scan entire repository using full 4-stage compliance pipeline.
    
    Pipeline Stages:
    1. Project Profiling - Classify code and identify risk areas
    2. Policy Translation - Convert policies to Semgrep rules
    3. Context Analysis - Filter false positives with AI reasoning
    4. Auto-Remediation - Generate secure code fixes
    
    Args:
        request: RepositoryScanRequest with repo path and options
        
    Returns:
        Complete scan results with violations and remediation
    """
    try:
        logger.info(f"[4-STAGE PIPELINE] Scanning repository: {request.repo_path}")
        
        analyzer = get_analyzer()
        if not analyzer:
            raise HTTPException(status_code=503, detail="Groq pipeline not available")
        
        # Run full pipeline with Indian compliance policies
        policies = load_indian_compliance_policies()
        result = await analyzer.analyze_repository_for_compliance(
            repo_path=request.repo_path,
            custom_policy_text=policies
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "message": "Repository scan completed",
            "result": result,
            "pipeline_executed": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Repository scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

# ============================================================================
# MULTI-TENANT ENDPOINTS (Org-Scoped)
# ============================================================================

@app.get("/org/scans")
def list_org_scans(
    current_org: OrgContext = Depends(get_current_org),
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(lambda: SessionLocal())
):
    """
    Get all scans for the current organization.
    
    Multi-tenant: Returns only scans where org_id matches current_org.id
    
    Args:
        current_org: OrgContext from dependency injection
        limit: Number of scans to return
        offset: Pagination offset
        
    Returns:
        List of scans for the organization
    """
    try:
        scans = db.query(Scan).filter(
            Scan.org_id == current_org.id
        ).order_by(Scan.created_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "status": "success",
            "org_id": str(current_org.id),
            "org_name": current_org.name,
            "scans": [
                {
                    "id": str(scan.id),
                    "project_id": str(scan.project_id),
                    "status": scan.status,
                    "risk_score": scan.risk_score,
                    "total_violations": scan.total_violations,
                    "created_at": scan.created_at.isoformat() if scan.created_at else None,
                    "branch": scan.branch,
                    "commit_sha": scan.commit_sha
                }
                for scan in scans
            ],
            "count": len(scans)
        }
    except Exception as e:
        logger.error(f"Error fetching scans for org {current_org.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scans")
    finally:
        db.close()


@app.get("/org/scans/{scan_id}")
def get_org_scan_details(
    scan_id: str,
    current_org: OrgContext = Depends(get_current_org),
    db: Session = Depends(lambda: SessionLocal())
):
    """
    Get detailed information for a specific scan.
    
    Multi-tenant: Verifies scan belongs to current organization before returning.
    
    Args:
        scan_id: UUID of the scan
        current_org: OrgContext from dependency injection
        
    Returns:
        Detailed scan information including all violations
    """
    try:
        from uuid import UUID as UUID_TYPE
        
        scan = db.query(Scan).filter(
            Scan.id == UUID_TYPE(scan_id),
            Scan.org_id == current_org.id  # ← Org isolation
        ).first()
        
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found or access denied")
        
        # Get violations for this scan
        violations = db.query(Violation).filter(
            Violation.scan_id == scan.id
        ).all()
        
        return {
            "status": "success",
            "org_id": str(current_org.id),
            "scan": {
                "id": str(scan.id),
                "project_id": str(scan.project_id),
                "status": scan.status,
                "risk_score": scan.risk_score,
                "total_violations": scan.total_violations,
                "critical_violations": scan.critical_violations,
                "high_violations": scan.high_violations,
                "medium_violations": scan.medium_violations,
                "low_violations": scan.low_violations,
                "created_at": scan.created_at.isoformat() if scan.created_at else None,
                "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                "branch": scan.branch,
                "commit_sha": scan.commit_sha,
                "files_scanned": scan.files_scanned,
                "scan_duration_seconds": scan.scan_duration_seconds,
            },
            "violations": [
                {
                    "id": str(v.id),
                    "rule_id": v.rule_id,
                    "severity": v.severity,
                    "category": v.category,
                    "message": v.message,
                    "file_path": v.file_path,
                    "line_number": v.line_number,
                    "ai_confidence": v.ai_confidence,
                    "ai_fix_suggestion": v.ai_fix_suggestion,
                }
                for v in violations
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching scan details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scan details")
    finally:
        db.close()


@app.get("/org/violations")
def list_org_violations(
    current_org: OrgContext = Depends(get_current_org),
    severity: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(lambda: SessionLocal())
):
    """
    Get violations for the current organization.
    
    Multi-tenant: Returns only violations where org_id matches current_org.id
    
    Args:
        current_org: OrgContext from dependency injection
        severity: Filter by severity (critical/high/medium/low)
        category: Filter by category
        limit: Max violations to return
        
    Returns:
        List of violations for the organization
    """
    try:
        query = db.query(Violation).filter(
            Violation.org_id == current_org.id  # ← Org isolation
        )
        
        if severity:
            query = query.filter(Violation.severity == severity)
        
        if category:
            query = query.filter(Violation.category == category)
        
        violations = query.order_by(
            Violation.created_at.desc()
        ).limit(limit).all()
        
        # Aggregate stats
        stats = db.query(Violation.severity).filter(
            Violation.org_id == current_org.id
        ).all()
        
        severity_counts = {
            "critical": sum(1 for v in stats if v.severity == "critical"),
            "high": sum(1 for v in stats if v.severity == "high"),
            "medium": sum(1 for v in stats if v.severity == "medium"),
            "low": sum(1 for v in stats if v.severity == "low"),
        }
        
        return {
            "status": "success",
            "org_id": str(current_org.id),
            "stats": severity_counts,
            "violations": [
                {
                    "id": str(v.id),
                    "scan_id": str(v.scan_id),
                    "rule_id": v.rule_id,
                    "severity": v.severity,
                    "category": v.category,
                    "file_path": v.file_path,
                    "line_number": v.line_number,
                    "status": v.status,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                }
                for v in violations
            ],
            "count": len(violations)
        }
    except Exception as e:
        logger.error(f"Error fetching violations for org {current_org.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch violations")
    finally:
        db.close()


@app.get("/org/info")
def get_org_info(current_org: OrgContext = Depends(get_current_org)):
    """
    Get current organization information.
    
    Args:
        current_org: OrgContext from dependency injection
        
    Returns:
        Organization details and limits
    """
    return {
        "status": "success",
        "org": {
            "id": str(current_org.id),
            "name": current_org.name,
            "tier": current_org.tier,
            "is_active": current_org.is_active,
            "limits": {
                "max_projects": current_org.max_projects,
                "max_scans_per_month": current_org.max_scans_per_month,
            }
        }
    }

# ============================================================================
# UNIFIED COMPLETE REPOSITORY SCAN ENDPOINT
# ============================================================================

@app.post("/org/scans/complete", response_model=ScanResponse)
async def complete_repository_scan(request: GitRepoRequest):
    """
    Complete repository scan with full 4-stage compliance pipeline.
    
    Combines all scanning and analysis stages in a single request:
    1. Git repository cloning from URL
    2. Project profiling & classification (Stage 1)
    3. Policy translation to Semgrep rules (Stage 2)
    4. Context analysis & false positive filtering (Stage 3)
    5. Auto-remediation suggestions (Stage 4)
    
    Args:
        request: GitRepoRequest containing:
            - git_repo_url: Repository URL to scan
            - branch: Git branch to scan (default: "main")
            - analysis_depth: "basic", "detailed", or "full"
            - use_ai: Enable AI-powered analysis (default: True)
    
    Returns:
        ScanResponse with:
        - Complete compliance analysis results
        - Detected violations and issues
        - AI-generated remediation suggestions
        - Risk scores and severity classifications
    """
    logger.info(f"[COMPLETE SCAN] Starting unified scan for: {request.git_repo_url}")
    
    try:
        import time
        start_time = time.time()
        
        # Generate scan ID for tracking
        scan_id = str(uuid4())
        logger.info(f"[COMPLETE SCAN] Generated scan ID: {scan_id}")
        
        # Validate URL format
        if not request.git_repo_url.startswith(('http://', 'https://', 'git@')):
            logger.warning(f"Invalid URL format: {request.git_repo_url}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid git URL format. Must start with http://, https://, or git@"
            )
        
        logger.info("Step 1: Cloning repository...")
        # Clone repository
        result = git_clone(request.git_repo_url)
        
        if result["status"] == "error":
            logger.error(f"Clone failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])
        
        result["ai_enabled"] = AI_ENABLED
        
        # Run full 4-stage pipeline
        if result["status"] == "success" and "clone_path" in result:
            logger.info("Step 2-5: Running 4-stage compliance pipeline...")
            
            if AI_ENABLED and request.use_ai:
                try:
                    analyzer = get_analyzer()
                    
                    if analyzer is not None:
                        logger.info("  - Stage 1: Project Profiling")
                        logger.info("  - Stage 2: AI-driven Code Analysis")
                        logger.info("  - Stage 3: Semantic Compliance Checking")
                        logger.info("  - Stage 4: Auto-Remediation")
                        
                        # Run AI-driven compliance analysis on cloned repository with Indian compliance policies
                        logger.info(f"  [ANALYZING] Scanning {result['total_files']} files for compliance violations...")
                        policies = load_indian_compliance_policies()
                        pipeline_result = await analyzer.analyze_repository_for_compliance(
                            repo_path=result["clone_path"],
                            custom_policy_text=policies
                        )
                        
                        if "error" not in pipeline_result:
                            violations = pipeline_result.get("violations", [])
                            files_analyzed = pipeline_result.get("total_files_analyzed", 0)
                            
                            logger.info(f"  [RESULTS] Files analyzed: {files_analyzed}")
                            logger.info(f"  [RESULTS] Violations detected: {len(violations)}")
                            logger.info(f"  [DEBUG] Pipeline result keys: {pipeline_result.keys()}")
                            logger.info(f"  [DEBUG] First violation sample: {violations[0] if violations else 'No violations'}")
                            
                            if violations:
                                severity_breakdown = pipeline_result.get("severity_breakdown", {})
                                logger.info(f"  [SEVERITY] Critical: {severity_breakdown.get('critical', 0)}, "
                                           f"High: {severity_breakdown.get('high', 0)}, "
                                           f"Medium: {severity_breakdown.get('medium', 0)}")
                            
                            # Calculate severity counts
                            severity_breakdown = pipeline_result.get("severity_breakdown", {})
                            critical_count = severity_breakdown.get("critical", 0)
                            high_count = severity_breakdown.get("high", 0)
                            medium_count = severity_breakdown.get("medium", 0)
                            low_count = severity_breakdown.get("low", 0)
                            
                            # Merge pipeline results with clone results
                            result["compliance_issues"] = violations
                            result["findings"] = violations  # Add findings field for frontend compatibility
                            result["violations"] = violations  # Add violations field for frontend compatibility
                            result["issues_count"] = len(violations)
                            result["total_findings"] = len(violations)
                            result["total_violations"] = len(violations)
                            
                            # Add severity counts
                            result["critical_count"] = critical_count
                            result["high_count"] = high_count
                            result["medium_count"] = medium_count
                            result["low_count"] = low_count
                            
                            result["analysis_summary"] = {
                                "total_violations": len(violations),
                                "severity_breakdown": severity_breakdown,
                                "remediations_available": len(pipeline_result.get("remediations", [])),
                                "files_analyzed": files_analyzed,
                                "scan_method": "AI-driven semantic analysis (Groq)",
                                "pipeline_status": "completed",
                                "policy_framework": "Indian Compliance (DPDPA, RBI, IT Act 2000)"
                            }
                            logger.info(f"  ✓ Compliance analysis completed - {len(violations)} violations detected")
                            logger.info(f"  ✓ Severity breakdown - Critical: {critical_count}, High: {high_count}, Medium: {medium_count}, Low: {low_count}")
                            logger.info(f"  [DEBUG] Response structure:")
                            logger.info(f"    - compliance_issues: {len(result.get('compliance_issues', []))}")
                            logger.info(f"    - findings: {len(result.get('findings', []))}")
                            logger.info(f"    - violations: {len(result.get('violations', []))}")
                            logger.info(f"    - critical_count: {result.get('critical_count')}")
                            logger.info(f"    - high_count: {result.get('high_count')}")
                            logger.info(f"    - total_findings: {result.get('total_findings')}")
                        else:
                            logger.error(f"Analysis error: {pipeline_result['error']}")
                            result["error_details"] = pipeline_result["error"]
                            result["compliance_issues"] = []
                            result["issues_count"] = 0
                    else:
                        logger.warning("Analyzer not available, skipping compliance analysis")
                        result["error_details"] = "AI analyzer unavailable"
                        result["compliance_issues"] = []
                        result["issues_count"] = 0
                        
                except Exception as e:
                    logger.error(f"Compliance analysis failed: {e}", exc_info=True)
                    result["error_details"] = f"Analysis error: {str(e)}"
                    result["compliance_issues"] = []
                    result["issues_count"] = 0
            else:
                if not AI_ENABLED:
                    logger.warning("AI not enabled, skipping compliance analysis")
                    result["error_details"] = "AI engine not available"
                elif not request.use_ai:
                    logger.info("AI analysis disabled for this scan")
                    result["error_details"] = "AI analysis skipped"
                result["compliance_issues"] = []
                result["issues_count"] = 0
        
        # Add scan duration
        end_time = time.time()
        result["scan_duration"] = round(end_time - start_time, 2)
        
        # Ensure all fields for frontend compatibility
        result["scan_id"] = scan_id
        
        # Add repository_name if not present
        if "repository_name" not in result:
            result["repository_name"] = result.get("repo", "Unknown Repository")
        
        # Ensure findings/violations fields are populated
        if "findings" not in result and "compliance_issues" in result:
            result["findings"] = result["compliance_issues"]
        if "violations" not in result and "compliance_issues" in result:
            result["violations"] = result["compliance_issues"]
        if "total_findings" not in result:
            result["total_findings"] = result.get("issues_count", 0)
        
        # Ensure severity counts are present
        if "critical_count" not in result:
            result["critical_count"] = 0
        if "high_count" not in result:
            result["high_count"] = 0
        if "medium_count" not in result:
            result["medium_count"] = 0
        if "low_count" not in result:
            result["low_count"] = 0
        
        logger.info(f"[COMPLETE SCAN] Completed in {result['scan_duration']}s")
        logger.info(f"[COMPLETE SCAN] Response contains:")
        logger.info(f"  - scan_id: {result.get('scan_id')}")
        logger.info(f"  - findings: {len(result.get('findings', []))}")
        logger.info(f"  - violations: {len(result.get('violations', []))}")
        logger.info(f"  - total_findings: {result.get('total_findings')}")
        
        return ScanResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete scan failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Exception handlers
@app.exception_handler(404)
def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "message": "Endpoint not found",
            "available_endpoints": [
                "/",
                "/health",
                "/org/scans/complete",
                "/git-scan",
                "/git-scan-detailed",
                "/ai-scan",
                "/scan-history",
                "/compliance-rules",
                "/docs"
            ]
        }
    )

@app.exception_handler(500)
def internal_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": "Please try again later or contact support"
        }
    )

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000,  # Changed to port 8001
        reload=True,
        log_level="info"
    )
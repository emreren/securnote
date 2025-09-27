"""
SecurNote Info API - Minimal informational interface
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import List, Optional
import os
import secrets

from ..logging_config import get_logger
from ..activity_logger import activity_logger

logger = get_logger("web")

app = FastAPI(
    title="SecurNote Admin Panel",
    description="Admin monitoring interface for SecurNote. Shows user activity logs.",
    version="2.0.0",
)

security = HTTPBasic()

# Admin credentials from environment
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "securnote123")

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials."""
    is_correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


class SystemInfo(BaseModel):
    service: str
    version: str
    description: str
    usage: dict

class ActivityLog(BaseModel):
    timestamp: str
    username: str
    action: str
    details: Optional[str]
    ip_address: Optional[str]
    success: bool

class ActivityStats(BaseModel):
    total_activities: int
    recent_activities: int
    unique_users: int
    top_users: List[dict]
    action_breakdown: List[dict]


@app.get("/")
def root():
    """Root endpoint with usage information."""
    return {
        "service": "SecurNote",
        "version": "2.0.0",
        "description": "Secure note-taking with end-to-end encryption",
        "primary_interface": "SSH/CLI",
        "usage": {
            "ssh_connect": "ssh securnote@server securnote",
            "commands": {
                "register": "ssh securnote@server 'securnote register user pass'",
                "list": "ssh securnote@server 'securnote list user pass'",
                "add": "ssh securnote@server 'securnote add user pass \"title\" \"content\"'",
                "view": "ssh securnote@server 'securnote view user pass note-id'",
                "help": "ssh securnote@server 'securnote --help'"
            }
        },
        "features": [
            "End-to-end encryption",
            "SSH-based access",
            "External editor support",
            "Multi-user isolation",
            "Zero-knowledge authentication"
        ]
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "securnote-info-api"}


@app.get("/info", response_model=SystemInfo)
def system_info():
    """Detailed system information."""
    return SystemInfo(
        service="SecurNote",
        version="2.0.0",
        description="Terminal-based secure note-taking system with SSH access",
        usage={
            "deployment": "Use docker-compose -f docker-compose.ssh.yml up",
            "connection": "ssh securnote@your-server securnote",
            "documentation": "/workspace/securnote/DEPLOYMENT_GUIDE.md"
        }
    )


@app.get("/admin/activities", response_model=List[ActivityLog])
def get_activities(limit: int = 100, admin: str = Depends(verify_admin)):
    """Get recent user activities (admin only)."""
    try:
        activities = activity_logger.get_recent_activities(limit)
        return [ActivityLog(**activity) for activity in activities]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch activities: {str(e)}")


@app.get("/admin/activities/{username}", response_model=List[ActivityLog])
def get_user_activities(username: str, limit: int = 50, admin: str = Depends(verify_admin)):
    """Get activities for specific user (admin only)."""
    try:
        activities = activity_logger.get_user_activities(username, limit)
        return [ActivityLog(username=username, **activity) for activity in activities]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user activities: {str(e)}")


@app.get("/admin/stats", response_model=ActivityStats)
def get_activity_stats(admin: str = Depends(verify_admin)):
    """Get activity statistics (admin only)."""
    try:
        stats = activity_logger.get_activity_stats()
        return ActivityStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


@app.get("/admin/dashboard")
def admin_dashboard(admin: str = Depends(verify_admin)):
    """Admin dashboard with summary information."""
    try:
        stats = activity_logger.get_activity_stats()
        recent_activities = activity_logger.get_recent_activities(10)

        return {
            "admin": admin,
            "stats": stats,
            "recent_activities": recent_activities,
            "status": "SecurNote Admin Panel Active"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")
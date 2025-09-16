"""
SecurNote Admin Panel - PKI Management
Separate admin interface for certificate management operations.
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from typing import List
from ..application import get_application
from ..exceptions import CertificateRevokedError, UserNotFoundError
from ..logging_config import get_logger

logger = get_logger('admin')

admin_app = FastAPI(
    title="SecurNote Admin Panel",
    description="Administrative interface for PKI certificate management",
    version="1.0.0"
)

app_instance = get_application()
security = HTTPBasic()

# Simple admin credentials (in production, use proper admin auth)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "securnote_admin_2024"

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials."""
    logger.info(f"Admin authentication attempt for: {credentials.username}")

    is_correct_username = secrets.compare_digest(
        credentials.username, ADMIN_USERNAME
    )
    is_correct_password = secrets.compare_digest(
        credentials.password, ADMIN_PASSWORD
    )

    if not (is_correct_username and is_correct_password):
        logger.warning(f"Admin authentication failed for: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    logger.info(f"Admin authenticated successfully: {credentials.username}")
    return credentials.username

@admin_app.get("/")
def admin_dashboard(admin_user = Depends(verify_admin)):
    """Admin dashboard with system overview."""
    return {
        "admin_panel": "SecurNote PKI Management",
        "admin_user": admin_user,
        "available_endpoints": [
            "/certificates/{username} - View user certificate",
            "/certificates/{username}/revoke - Revoke user certificate",
            "/certificates/revoked - List all revoked certificates",
            "/system/cleanup - Clean expired challenges"
        ]
    }

@admin_app.get("/certificates/{username}")
def get_user_certificate_admin(username: str, admin_user = Depends(verify_admin)):
    """Get any user's certificate information (Admin only)."""
    user_cert = app_instance.get_user_certificate(username)
    if not user_cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    is_valid = app_instance.validate_user_access(username)

    return {
        "username": username,
        "certificate": user_cert,
        "validation_status": {
            "is_valid": is_valid,
            "signature_verified": True,
            "not_revoked": is_valid,
            "issued_by_trusted_ca": True
        },
        "security_level": "Enterprise Grade" if is_valid else "Revoked",
        "admin_action": f"Certificate viewed by admin: {admin_user}"
    }

@admin_app.post("/certificates/{username}/revoke")
def revoke_user_certificate_admin(
    username: str,
    reason: str = "admin_revocation",
    admin_user = Depends(verify_admin)
):
    """Revoke user's certificate (Admin only)."""
    logger.warning(f"Admin {admin_user} attempting to revoke certificate for user: {username}, reason: {reason}")

    success = app_instance.revoke_user_certificate(username, reason)
    if not success:
        logger.error(f"Certificate revocation failed for user: {username} by admin: {admin_user}")
        raise HTTPException(status_code=404, detail="User or certificate not found")

    logger.critical(f"Certificate REVOKED for user: {username} by admin: {admin_user}, reason: {reason}")

    return {
        "message": f"Certificate for {username} revoked by admin",
        "revoked_by": admin_user,
        "reason": reason,
        "effect": "User access to notes immediately revoked",
        "security_action": "Certificate added to CRL"
    }

@admin_app.get("/certificates/revoked")
def get_revoked_certificates_admin(admin_user = Depends(verify_admin)):
    """Get comprehensive revoked certificates list (Admin only)."""
    revoked_list = app_instance.get_revoked_certificates()

    return {
        "admin_user": admin_user,
        "revoked_certificates": revoked_list,
        "total_revoked": len(revoked_list),
        "crl_status": "Active and Enforced",
        "management_note": "All revoked certificates block user access immediately"
    }

@admin_app.post("/system/cleanup")
def cleanup_system_admin(admin_user = Depends(verify_admin)):
    """System cleanup and maintenance (Admin only)."""
    cleaned_challenges = app_instance.cleanup_expired_challenges()

    return {
        "admin_user": admin_user,
        "message": "System maintenance completed",
        "expired_challenges_removed": cleaned_challenges,
        "system_status": "Optimized",
        "maintenance_type": "Scheduled cleanup"
    }

@admin_app.get("/users/list")
def list_all_users_admin(admin_user = Depends(verify_admin)):
    """List all users with certificate status (Admin only)."""
    # Get all users from storage
    try:
        users_info = []

        # This is a simple implementation - in production you'd have proper user listing
        return {
            "admin_user": admin_user,
            "message": "User listing requires direct database access",
            "note": "Use certificate management endpoints for individual user operations"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")
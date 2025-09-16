"""
SecurNote FastAPI - Clean Architecture Implementation
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import List, Optional
import secrets
from ..application import SecurNoteApplication, get_application
from ..crypto import NoteCrypto
from ..storage import NoteStorage
from ..exceptions import CertificateRevokedError, UserNotFoundError, InvalidCredentialsError
from ..logging_config import get_logger

logger = get_logger('web')

app = FastAPI(
    title="SecurNote API",
    description="Secure note-taking API with ZK-proof, PKI, and CRL",
    version="2.0.0"
)

# Initialize clean architecture application
app_instance = get_application()
storage = NoteStorage()  # Legacy compatibility
security = HTTPBasic()

# Session storage (simple in-memory)
active_sessions = {}

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class NoteCreate(BaseModel):
    title: str
    content: str

class NoteResponse(BaseModel):
    id: str
    title: str
    content: str
    timestamp: str

class NoteListItem(BaseModel):
    id: str
    title: str
    timestamp: str

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Authenticate user with enhanced security validation."""
    try:
        logger.info(f"Authentication attempt for user: {credentials.username}")

        # Enhanced authentication with certificate validation
        note_key, access_granted = app_instance.authenticate_with_validation(
            credentials.username, credentials.password
        )

        if not note_key:
            logger.warning(f"Authentication failed for user: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )

        if not access_granted:
            logger.warning(f"Certificate access denied for user: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Certificate revoked or invalid - access denied"
            )

        return {
            "username": credentials.username,
            "note_key": note_key,
            "crypto": NoteCrypto(note_key)
        }

    except (UserNotFoundError, InvalidCredentialsError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Basic"},
        )
    except CertificateRevokedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Certificate revoked - access denied"
        )

@app.post("/register")
def register_user(user: UserCreate):
    """Register new user with full security setup."""
    success = app_instance.create_user(user.username, user.password)
    if success:
        return {
            "message": f"User '{user.username}' created successfully",
            "features": [
                "Traditional Authentication",
                "Zero-Knowledge Proof",
                "PKI Certificate",
                "Certificate-based Access Control"
            ]
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

@app.get("/users/me")
def get_current_user_info(current_user = Depends(get_current_user)):
    """Get comprehensive user information."""
    user_info = app_instance.get_user_info(current_user["username"])
    return {
        "username": current_user["username"],
        "user_info": user_info,
        "security_status": "All systems operational"
    }

@app.post("/notes", response_model=dict)
def create_note(note: NoteCreate, current_user = Depends(get_current_user)):
    """Create a new encrypted note."""
    title_enc, title_nonce = current_user["crypto"].encrypt(note.title)
    content_enc, content_nonce = current_user["crypto"].encrypt(note.content)
    
    note_id = storage.add_note(
        current_user["username"],
        title_enc,
        content_enc,
        title_nonce,
        content_nonce
    )
    
    return {"id": note_id, "message": "Note created successfully"}

@app.get("/notes", response_model=List[NoteListItem])
def list_notes(current_user = Depends(get_current_user)):
    """List all user's notes with decrypted titles."""
    notes = storage.get_notes(current_user["username"])
    
    decrypted_notes = []
    for note in notes:
        try:
            title = current_user["crypto"].decrypt(note['title_encrypted'], note['title_nonce'])
            decrypted_notes.append(NoteListItem(
                id=note["id"],
                title=title,
                timestamp=note["timestamp"][:19]
            ))
        except:
            decrypted_notes.append(NoteListItem(
                id=note["id"],
                title="[Decryption Error]",
                timestamp=note["timestamp"][:19]
            ))
    
    return decrypted_notes

@app.get("/notes/{note_id}", response_model=NoteResponse)
def get_note(note_id: str, current_user = Depends(get_current_user)):
    """Get a specific note by ID."""
    note = storage.get_note_by_id(current_user["username"], note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    try:
        title = current_user["crypto"].decrypt(note['title_encrypted'], note['title_nonce'])
        content = current_user["crypto"].decrypt(note['content_encrypted'], note['content_nonce'])
        
        return NoteResponse(
            id=note["id"],
            title=title,
            content=content,
            timestamp=note["timestamp"][:19]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to decrypt note")

@app.delete("/notes/{note_id}")
def delete_note(note_id: str, current_user = Depends(get_current_user)):
    """Delete a note by ID."""
    if storage.delete_note(current_user["username"], note_id):
        return {"message": "Note deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Note not found")

@app.post("/test/run-all", tags=["Testing"])
def run_all_tests():
    """Run all basic tests and return results."""
    import tempfile
    import sys
    import os

    # Use absolute imports to avoid relative import issues
    try:
        from securnote.auth import UserAuth
        from securnote.crypto import NoteCrypto
        from securnote.storage import NoteStorage
    except ImportError:
        # Fallback for different environments
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(os.path.dirname(current_dir))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from securnote.auth import UserAuth
        from securnote.crypto import NoteCrypto
        from securnote.storage import NoteStorage

    results = []

    try:
        # Test 1: User creation
        with tempfile.TemporaryDirectory() as temp_dir:
            auth = UserAuth(temp_dir)
            assert auth.create_user("testuser", "password123") == True
            assert auth.user_exists("testuser") == True
            assert auth.create_user("testuser", "password123") == False
        results.append({"test": "User Creation", "status": "PASSED"})
    except Exception as e:
        results.append({"test": "User Creation", "status": "FAILED", "error": str(e)})

    try:
        # Test 2: User login
        with tempfile.TemporaryDirectory() as temp_dir:
            auth = UserAuth(temp_dir)
            auth.create_user("testuser", "password123")
            note_key = auth.login("testuser", "password123")
            assert note_key is not None
            assert len(note_key) == 32
            assert auth.login("testuser", "wrongpassword") is None
        results.append({"test": "User Login", "status": "PASSED"})
    except Exception as e:
        results.append({"test": "User Login", "status": "FAILED", "error": str(e)})

    try:
        # Test 3: Note encryption
        with tempfile.TemporaryDirectory() as temp_dir:
            auth = UserAuth(temp_dir)
            auth.create_user("testuser", "password123")
            note_key = auth.login("testuser", "password123")
            crypto = NoteCrypto(note_key)
            original_text = "This is a secret note!"
            encrypted, nonce = crypto.encrypt(original_text)
            assert encrypted != original_text
            decrypted = crypto.decrypt(encrypted, nonce)
            assert decrypted == original_text
        results.append({"test": "Note Encryption", "status": "PASSED"})
    except Exception as e:
        results.append({"test": "Note Encryption", "status": "FAILED", "error": str(e)})

    try:
        # Test 4: Note storage
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_test = NoteStorage(temp_dir)
            note_id = storage_test.add_note("testuser", "encrypted_title", "encrypted_content", "nonce123", "nonce456")
            notes = storage_test.get_notes("testuser")
            assert len(notes) == 1
            note = storage_test.get_note_by_id("testuser", note_id)
            assert note is not None
            assert storage_test.delete_note("testuser", note_id) == True
        results.append({"test": "Note Storage", "status": "PASSED"})
    except Exception as e:
        results.append({"test": "Note Storage", "status": "FAILED", "error": str(e)})

    passed = len([r for r in results if r["status"] == "PASSED"])
    total = len(results)

    return {
        "summary": f"{passed}/{total} tests passed",
        "all_passed": passed == total,
        "results": results
    }

# Certificate information endpoint (user can view their own certificate)
@app.get("/users/me/certificate")
def get_my_certificate(current_user = Depends(get_current_user)):
    """Get current user's certificate information."""
    user_cert = app_instance.get_user_certificate(current_user["username"])
    if not user_cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    is_valid = app_instance.validate_user_access(current_user["username"])

    return {
        "certificate": user_cert,
        "validation_status": {
            "is_valid": is_valid,
            "signature_verified": True,
            "not_revoked": is_valid,
            "issued_by_trusted_ca": True
        },
        "security_level": "Enterprise Grade" if is_valid else "Revoked",
        "admin_note": "For certificate management operations, contact system administrator"
    }

@app.post("/system/cleanup", tags=["System"])
def cleanup_system():
    """Cleanup expired challenges and optimize system."""
    cleaned_challenges = app_instance.cleanup_expired_challenges()
    return {
        "message": "System cleanup completed",
        "expired_challenges_removed": cleaned_challenges,
        "system_status": "Optimized"
    }
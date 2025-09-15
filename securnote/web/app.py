"""
Simple FastAPI API for SecurNote.
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import List, Optional
import secrets
from ..auth import UserAuth
from ..crypto import NoteCrypto
from ..storage import NoteStorage

app = FastAPI(
    title="SecurNote API",
    description="Simple encrypted note-taking API",
    version="1.0.0"
)

# Initialize components
auth = UserAuth()
storage = NoteStorage()
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
    """Authenticate user with basic auth."""
    note_key = auth.login(credentials.username, credentials.password)
    if not note_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return {
        "username": credentials.username,
        "note_key": note_key,
        "crypto": NoteCrypto(note_key)
    }

@app.post("/register")
def register_user(user: UserCreate):
    """Register a new user."""
    if auth.create_user(user.username, user.password):
        return {"message": f"User '{user.username}' created successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )

@app.get("/users/me")
def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information."""
    return {"username": current_user["username"]}

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

@app.post("/test/run-all")
def run_all_tests():
    """Run all basic tests and return results."""
    import tempfile
    from ..auth import UserAuth
    from ..crypto import NoteCrypto
    from ..storage import NoteStorage

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
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
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import Base, engine, get_db
from models import User, Note, NoteShare
from schemas import (
    UserCreate,
    UserLogin,
    TokenResponse,
    MessageResponse,
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    ShareNoteRequest,
)
from auth import hash_password, verify_password, create_access_token, get_current_user


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Notes App Backend APIs")


@app.get("/")
def root():
    return {"message": "Notes API is running"}


@app.post("/register", status_code=status.HTTP_201_CREATED, response_model=MessageResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully"}


@app.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token({"user_id": user.id})

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.post("/notes", status_code=status.HTTP_201_CREATED, response_model=NoteResponse)
def create_note(
    note_data: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_note = Note(
        title=note_data.title,
        content=note_data.content,
        owner_id=current_user.id
    )

    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    return new_note


@app.get("/notes", response_model=list[NoteResponse])
def get_notes(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    owned_notes_query = db.query(Note).filter(Note.owner_id == current_user.id)

    shared_notes_query = (
        db.query(Note)
        .join(NoteShare)
        .filter(NoteShare.shared_with_user_id == current_user.id)
    )

    all_notes = owned_notes_query.union(shared_notes_query)

    notes = (
        all_notes
        .order_by(Note.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return notes


@app.get("/notes/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = db.query(Note).filter(Note.id == note_id).first()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    is_owner = note.owner_id == current_user.id

    is_shared = (
        db.query(NoteShare)
        .filter(
            NoteShare.note_id == note_id,
            NoteShare.shared_with_user_id == current_user.id
        )
        .first()
        is not None
    )

    if not is_owner and not is_shared:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this note"
        )

    return note


@app.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    note_data: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = db.query(Note).filter(Note.id == note_id).first()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    if note.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can update this note"
        )

    note.title = note_data.title
    note.content = note_data.content

    db.commit()
    db.refresh(note)

    return note


@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = db.query(Note).filter(Note.id == note_id).first()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    if note.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can delete this note"
        )

    db.delete(note)
    db.commit()

    return None


@app.post("/notes/{note_id}/share", response_model=MessageResponse)
def share_note(
    note_id: int,
    share_data: ShareNoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = db.query(Note).filter(Note.id == note_id).first()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    if note.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can share this note"
        )

    user_to_share = db.query(User).filter(User.email == share_data.share_with_email).first()

    if not user_to_share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User to share with not found"
        )

    if user_to_share.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot share a note with yourself"
        )

    existing_share = (
        db.query(NoteShare)
        .filter(
            NoteShare.note_id == note_id,
            NoteShare.shared_with_user_id == user_to_share.id
        )
        .first()
    )

    if existing_share:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note already shared with this user"
        )

    new_share = NoteShare(
        note_id=note_id,
        shared_with_user_id=user_to_share.id
    )

    db.add(new_share)
    db.commit()

    return {"message": "Note shared successfully"}


@app.get("/search", response_model=list[NoteResponse])
def search_notes(
    q: str = Query(min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    owned_note_ids = db.query(Note.id).filter(Note.owner_id == current_user.id)

    shared_note_ids = (
        db.query(NoteShare.note_id)
        .filter(NoteShare.shared_with_user_id == current_user.id)
    )

    notes = (
        db.query(Note)
        .filter(
            Note.id.in_(owned_note_ids.union(shared_note_ids)),
            or_(
                Note.title.ilike(f"%{q}%"),
                Note.content.ilike(f"%{q}%")
            )
        )
        .all()
    )

    return notes


@app.get("/about")
def about():
    return {
        "name": "Koushik",
        "email": "koushikravipati83@gmail.com",
        "my features": {
            "Full-text note search": "I added search because a notes app becomes more useful when users can quickly find old notes by title or content."
        }
    }
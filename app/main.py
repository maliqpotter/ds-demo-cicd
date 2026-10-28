"""FastAPI application entrypoint."""

from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .database import Base, Note, SessionLocal, engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Notes App", lifespan=lifespan)
templates = Jinja2Templates(directory="app/templates")


def get_db() -> Generator[Session, None, None]:
    """Yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/", response_class=HTMLResponse)
def read_notes(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Render the notes list page."""
    notes = db.query(Note).order_by(Note.id.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"notes": notes},
    )


@app.post("/add")
def add_note(
    title: str = Form(..., min_length=1, max_length=100),
    content: str = Form(..., min_length=1, max_length=2000),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Add a new note."""
    new_note = Note(title=title.strip(), content=content.strip())
    db.add(new_note)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/delete/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)) -> RedirectResponse:
    """Delete a note by ID."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if note:
        db.delete(note)
        db.commit()
    return RedirectResponse(url="/", status_code=303)

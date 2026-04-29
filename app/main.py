from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import SessionLocal, Note

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def read_notes(request: Request, db: Session = Depends(get_db)):
    notes = db.query(Note).all()
    return templates.TemplateResponse("index.html", {"request": request, "notes": notes})

@app.post("/add")
def add_note(title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    new_note = Note(title=title, content=content)
    db.add(new_note)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/delete/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if note:
        db.delete(note)
        db.commit()
    return RedirectResponse(url="/", status_code=303)

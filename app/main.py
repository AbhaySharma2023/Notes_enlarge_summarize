import json
import os
from datetime import datetime
from typing import Dict, Optional, List
from fastapi import FastAPI, HTTPException, Depends
from dotenv import load_dotenv
from app.models import (
    Note, 
    ProcessNoteRequest, 
    ProcessNoteResponse, 
    ProfileInsightRequest,
    ErrorResponse,
    TiptapDoc
)
from app.llm import GroqService, get_groq_service
from app.converters import plain_text_to_tiptap

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Sticky Notes Processing API",
    description="A FastAPI service for summarizing and enlarging sticky notes using Groq LLM",
    version="1.0.0"
)


async def get_recent_notes(self, limit: int = 15) -> List[Note]:
        """Get recent notes sorted by creation date."""
        all_notes = list(self._notes.values())
        # Sort by created_at descending (most recent first)
        sorted_notes = sorted(all_notes, key=lambda x: x.created_at, reverse=True)
        return sorted_notes[:limit]


class NoteRepository:
    """In-memory note repository with data loaded from JSON file."""
    
    def __init__(self):
        self._notes: Dict[str, Note] = {}
        self._load_data()
    
    def _load_data(self) -> None:
        """Load notes from data.json file."""
        try:
            data_path = os.path.join(os.path.dirname(__file__), "data.json")
            with open(data_path, 'r') as f:
                data = json.load(f)
                for note_data in data["notes"]:
                    note = Note(**note_data)
                    self._notes[note.id] = note
        except FileNotFoundError:
            # Create some default notes if file doesn't exist
            self._notes = {
                "note-1": Note(
                    id="note-1",
                    content="Python is a high-level programming language.",
                    tags=["programming", "python"]
                )
            }
    
    async def get_by_id(self, note_id: str) -> Optional[Note]:
        """Get a note by ID."""
        return self._notes.get(note_id)
    
    async def list_all(self) -> Dict[str, Note]:
        """Get all notes."""
        return self._notes.copy()


# Global repository instance
_repository = NoteRepository()


def save_tiptap_json(note_id: str, action: str, tiptap_doc: dict) -> str:
    """Save Tiptap JSON to file and return filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tiptap_{note_id}_{action}_{timestamp}.json"
    
    # Create output directory if it doesn't exist
    output_dir = "tiptap_output"
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(tiptap_doc, f, indent=2, ensure_ascii=False)
    
    return filename


def get_repository() -> NoteRepository:
    """Dependency to get repository instance."""
    return _repository


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Sticky Notes Processing API is running"}


@app.get("/notes")
async def list_notes(repo: NoteRepository = Depends(get_repository)):
    """List all available notes."""
    notes = await repo.list_all()
    return {"notes": list(notes.values())}


@app.post(
    "/process-note",
    response_model=ProcessNoteResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Note not found"},
        422: {"model": ErrorResponse, "description": "Invalid command"},
        503: {"model": ErrorResponse, "description": "LLM service unavailable"}
    }
)
async def process_note(
    request: ProcessNoteRequest,
    repo: NoteRepository = Depends(get_repository),
    groq_service: GroqService = Depends(get_groq_service)
) -> ProcessNoteResponse:
    """Process a note with summarize, enlarge, or format command."""
    
    # Get the note
    note = await repo.get_by_id(request.note_id)
    if not note:
        raise HTTPException(
            status_code=404,
            detail=f"Note with ID '{request.note_id}' not found"
        )
    
    try:
        # Process with Groq LLM
        processed_content = await groq_service.process_note(note, request.command)
        
        # Convert to Tiptap format
        tiptap_doc_dict = plain_text_to_tiptap(processed_content)
        tiptap_doc = TiptapDoc(**tiptap_doc_dict)
        
        # Save Tiptap JSON to file
        filename = save_tiptap_json(request.note_id, request.command, tiptap_doc_dict)
        
        return ProcessNoteResponse(
            note_id=request.note_id,
            action=request.command,
            tiptap_doc=tiptap_doc,
            filename=filename
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"LLM service error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
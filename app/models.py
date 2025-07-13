from pydantic import BaseModel, Field
from typing import List, Literal, Any, Dict, Optional


class ProfileInsightRequest(BaseModel):
    command: Literal["profile_insight"] = Field(..., description="Profile insight command")
    # For profile insight, we don't need note_id as we analyze all recent notesfrom pydantic import BaseModel, Field
from typing import List, Literal, Any, Dict, Optional
from datetime import datetime


class Note(BaseModel):
    id: str
    title: Optional[str] = None
    content: str
    tags: List[str]
    created_at: datetime


class ProcessNoteRequest(BaseModel):
    note_id: str = Field(..., description="ID of the note to process")
    command: Literal["summarize", "enlarge", "format", "profile_insight"] = Field(..., description="Action to perform")


class TiptapDoc(BaseModel):
    type: str = "doc"
    content: List[Dict[str, Any]]


class ProcessNoteResponse(BaseModel):
    note_id: str
    action: Literal["summarize", "enlarge", "format", "profile_insight"]
    tiptap_doc: TiptapDoc
    filename: Optional[str] = None  # Optional filename of saved JSON


class ErrorResponse(BaseModel):
    error: str
    detail: str
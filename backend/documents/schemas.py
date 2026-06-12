from pydantic import BaseModel
from typing import Optional, List
import datetime

class DocumentBase(BaseModel):
    title: str
    access_level: int

class DocumentCreate(DocumentBase):
    pass

class DocumentOut(DocumentBase):
    id: str
    file_path: str
    doc_type: str
    uploaded_by: int
    uploaded_at: datetime.datetime
    status: str

    class Config:
        from_attributes = True

class ChunkOut(BaseModel):
    id: str
    document_id: str
    page_number: Optional[int]
    section_title: Optional[str]
    chunk_index: int

    class Config:
        from_attributes = True

class DocumentWithChunks(DocumentOut):
    chunks: List[ChunkOut] = []


class DocumentContentOut(BaseModel):
    id: str
    title: str
    doc_type: str
    content: str


class CitationOut(BaseModel):
    id: str
    document_id: str
    title: str
    text: str
    section_title: Optional[str] = None
    chunk_index: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None

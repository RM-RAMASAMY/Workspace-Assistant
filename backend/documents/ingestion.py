import os
import uuid
import fitz  # PyMuPDF
import docx
from sentence_transformers import SentenceTransformer

from .chunk_metadata import build_chunks_with_metadata
from retrieval.vector_store import add_chunks_to_vector_store
from documents.models import Document, Chunk, DocumentStatus
from sqlalchemy.ext.asyncio import AsyncSession

# Load embedding model globally to avoid reloading
# all-MiniLM-L6-v2 is small and fast
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    return text

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

async def ingest_document(document: Document, db: AsyncSession):
    try:
        # 1. Parse Document
        ext = os.path.splitext(document.file_path)[1].lower()
        if ext == ".pdf":
            text = extract_text_from_pdf(document.file_path)
        elif ext == ".docx":
            text = extract_text_from_docx(document.file_path)
        elif ext in [".txt", ".md"]:
            with open(document.file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            raise ValueError(f"Unsupported file type: {ext}")
            
        # 2. Chunking with section/line metadata for citations and document viewer
        enriched_chunks = build_chunks_with_metadata(text, chunk_size=1000, chunk_overlap=100)
        chunk_texts = [chunk["text"] for chunk in enriched_chunks]

        # 3. Embeddings
        embeddings = embedder.encode(chunk_texts).tolist()

        # 4. Save to ChromaDB & SQLite
        chunk_ids = []
        metadatas = []
        documents_text = []

        for chunk in enriched_chunks:
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)
            documents_text.append(chunk["text"])
            metadatas.append({
                "document_id": document.id,
                "title": document.title,
                "access_level": int(document.access_level),
                "chunk_index": int(chunk["chunk_index"]),
                "section_title": chunk["section_title"] or "",
                "line_start": int(chunk["line_start"]),
                "line_end": int(chunk["line_end"]),
            })

            db_chunk = Chunk(
                id=chunk_id,
                document_id=document.id,
                chunk_index=chunk["chunk_index"],
                section_title=chunk["section_title"] or None,
                page_number=chunk["line_start"] or None,
            )
            db.add(db_chunk)
            
        # Add to vector store
        add_chunks_to_vector_store(chunk_ids, embeddings, documents_text, metadatas)
        
        # Update status
        document.status = DocumentStatus.INDEXED.value
        await db.commit()
        
    except Exception as e:
        document.status = DocumentStatus.FAILED.value
        await db.commit()
        print(f"Ingestion failed for {document.id}: {e}")

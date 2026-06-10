import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from auth.dependencies import get_current_user, require_role
from auth.models import User, AccessLevel
from . import models, schemas
from .ingestion import ingest_document
from retrieval.vector_store import delete_document_from_vector_store

router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=schemas.DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    access_level: int = Form(...),
    current_user: User = Depends(require_role(AccessLevel.INTERNAL)),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.role or not current_user.role.can_upload_docs:
        raise HTTPException(status_code=403, detail="Not authorized to upload documents")

    doc_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{file.filename}")
    
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    ext = os.path.splitext(file.filename)[1].lower()
    
    new_doc = models.Document(
        id=doc_id,
        title=file.filename,
        file_path=file_path,
        doc_type=ext,
        access_level=access_level,
        uploaded_by=current_user.id
    )
    
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    
    # Trigger async ingestion
    background_tasks.add_task(ingest_document, new_doc, db)
    
    return new_doc

@router.get("/", response_model=List[schemas.DocumentOut])
async def list_documents(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Users can only see documents they have access to
    result = await db.execute(select(models.Document).filter(models.Document.access_level <= current_user.access_level))
    return result.scalars().all()

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: User = Depends(require_role(AccessLevel.CONFIDENTIAL)),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.role or not current_user.role.can_manage_users:
        # Simplification: assuming manage_users correlates with admin privileges here
        raise HTTPException(status_code=403, detail="Not authorized to delete documents")
        
    result = await db.execute(select(models.Document).filter(models.Document.id == doc_id))
    doc = result.scalars().first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Delete from vector store
    delete_document_from_vector_store(doc.id)
    
    # Delete from DB
    await db.delete(doc)
    await db.commit()
    
    # Optionally delete file
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
        
    return {"status": "deleted"}

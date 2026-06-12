import asyncio
import os
import sys
import uuid
import shutil
from database import AsyncSessionLocal
from documents.ingestion import ingest_document
from sqlalchemy.future import select
from sqlalchemy import delete
from auth.models import User, AccessLevel
from documents.models import Document, Chunk, DocumentStatus
from retrieval.vector_store import delete_document_from_vector_store

# Per-document access levels so role-based access is actually demonstrable.
# Employees (INTERNAL=2) can see PUBLIC/INTERNAL docs; the board notes stay
# RESTRICTED (4) and are only visible to admins.
SAMPLE_ACCESS_LEVELS = {
    "employee_handbook.md": AccessLevel.PUBLIC,
    "product_spec_v3.md": AccessLevel.INTERNAL,
    "board_meeting_june.md": AccessLevel.RESTRICTED,
}


def _access_level_for(filename: str) -> int:
    if filename in SAMPLE_ACCESS_LEVELS:
        return int(SAMPLE_ACCESS_LEVELS[filename])
    if filename.startswith("hanuinnotech_"):
        return int(AccessLevel.PUBLIC)
    return int(AccessLevel.INTERNAL)

REINDEX = "--reindex" in sys.argv or os.environ.get("REINDEX_SAMPLES") == "1"


async def _reindex_document(db, doc: Document):
    delete_document_from_vector_store(doc.id)
    await db.execute(delete(Chunk).where(Chunk.document_id == doc.id))
    doc.status = DocumentStatus.PENDING.value
    await db.commit()
    await db.refresh(doc)
    await ingest_document(doc, db)


async def _purge_raw_documents(db):
    result = await db.execute(select(Document).where(Document.title.startswith("_")))
    for doc in result.scalars().all():
        delete_document_from_vector_store(doc.id)
        await db.delete(doc)
    await db.commit()


async def _purge_stale_samples(db, active_filenames: set[str]):
    result = await db.execute(select(Document))
    for doc in result.scalars().all():
        if doc.title in active_filenames:
            continue
        if doc.title.startswith("_") or doc.title.startswith("hanuinnotech"):
            delete_document_from_vector_store(doc.id)
            await db.delete(doc)
    await db.commit()


async def ingest_samples():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).filter(User.email == "admin@demo.com"))
        admin = res.scalars().first()
        if not admin:
            print("Admin user not found.")
            return

        sample_dir = "sample_docs"
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        if not os.path.exists(sample_dir):
            print("No sample_docs directory found.")
            return

        active_filenames = {
            f for f in os.listdir(sample_dir)
            if f.endswith(".md") and not f.startswith("_")
        }
        await _purge_raw_documents(db)
        await _purge_stale_samples(db, active_filenames)

        for filename in sorted(active_filenames):
            if not filename.endswith(".md") or filename.startswith("_"):
                continue

            existing = await db.execute(
                select(Document).filter(
                    Document.title == filename,
                    Document.status == "INDEXED",
                )
            )
            existing_doc = existing.scalars().first()
            if existing_doc:
                if REINDEX:
                    print(f"Re-indexing {filename}...")
                    await _reindex_document(db, existing_doc)
                else:
                    print(f"Skipping {filename} (already indexed).")
                continue

            file_path = os.path.join(sample_dir, filename)
            doc_id = str(uuid.uuid4())
            upload_path = os.path.join(upload_dir, f"{doc_id}_{filename}")

            shutil.copy2(file_path, upload_path)

            new_doc = Document(
                id=doc_id,
                title=filename,
                file_path=upload_path,
                doc_type=".md",
                access_level=_access_level_for(filename),
                uploaded_by=admin.id,
            )
                
            db.add(new_doc)
            await db.commit()
            await db.refresh(new_doc)

            print(f"Ingesting {filename}...")
            await ingest_document(new_doc, db)

        print("Finished ingesting sample documents!")

if __name__ == "__main__":
    asyncio.run(ingest_samples())

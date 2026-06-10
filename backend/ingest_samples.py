import asyncio
import os
import uuid
import shutil
from database import AsyncSessionLocal
from documents.ingestion import ingest_document
from sqlalchemy.future import select
from auth.models import User
from documents.models import Document

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
            
        for filename in os.listdir(sample_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(sample_dir, filename)
                doc_id = str(uuid.uuid4())
                upload_path = os.path.join(upload_dir, f"{doc_id}_{filename}")
                
                shutil.copy2(file_path, upload_path)
                
                new_doc = Document(
                    id=doc_id,
                    title=filename,
                    file_path=upload_path,
                    doc_type=".md",
                    access_level=admin.access_level,
                    uploaded_by=admin.id
                )
                
                db.add(new_doc)
                await db.commit()
                await db.refresh(new_doc)
                
                print(f"Ingesting {filename}...")
                await ingest_document(new_doc, db)
                
        print("Finished ingesting sample documents!")

if __name__ == "__main__":
    asyncio.run(ingest_samples())

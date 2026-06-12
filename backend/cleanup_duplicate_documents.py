"""Remove duplicate documents (same title), keeping the newest indexed copy."""
import asyncio
import os
from collections import defaultdict

from sqlalchemy.future import select

from database import AsyncSessionLocal
from auth.models import User  # noqa: F401 — register users table for FK resolution
from documents.models import Document
from retrieval.vector_store import delete_document_from_vector_store


async def cleanup_duplicates() -> int:
  async with AsyncSessionLocal() as db:
    result = await db.execute(select(Document).order_by(Document.uploaded_at.desc()))
    documents = result.scalars().all()

    by_title: dict[str, list[Document]] = defaultdict(list)
    for doc in documents:
      by_title[doc.title].append(doc)

    removed = 0
    for title, docs in by_title.items():
      if len(docs) <= 1:
        continue

      # Prefer the newest document that was successfully indexed.
      indexed = [d for d in docs if d.status == "INDEXED"]
      keep = indexed[0] if indexed else docs[0]
      duplicates = [d for d in docs if d.id != keep.id]

      for doc in duplicates:
        delete_document_from_vector_store(doc.id)
        await db.delete(doc)  # chunks cascade via relationship
        if doc.file_path and os.path.exists(doc.file_path):
          os.remove(doc.file_path)
        removed += 1
        print(f"Removed duplicate: {title} ({doc.id})")

    await db.commit()
    return removed


if __name__ == "__main__":
  count = asyncio.run(cleanup_duplicates())
  print(f"Cleanup complete. Removed {count} duplicate document(s).")

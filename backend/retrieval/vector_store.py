import chromadb
from config import settings

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)

# We use the default embedding function or sentence-transformers in ingestion
collection = chroma_client.get_or_create_collection(
    name="documents_v1",
    metadata={"hnsw:space": "cosine"}
)

def add_chunks_to_vector_store(chunk_ids, embeddings, documents, metadatas):
    collection.add(
        ids=chunk_ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )

def search_vector_store(query_embedding, access_level, n_results=40):
    # Retrieve using metadata filter for access level
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={"access_level": {"$lte": access_level}}
    )
    return results

def delete_document_from_vector_store(document_id):
    collection.delete(
        where={"document_id": document_id}
    )

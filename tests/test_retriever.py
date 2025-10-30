import pytest
from app.rag.embeddings import EmbeddingService
from app.rag.retriever import DocumentRetriever

@pytest.mark.asyncio
async def test_retrieve_documents():
    embedding_service = EmbeddingService()
    retriever = DocumentRetriever(embedding_service)
    query = "sostenibilidad"  # Cambia por una palabra clave relevante de tus PDFs
    results = await retriever.retrieve(query, top_k=2)
    assert isinstance(results, list)
    assert len(results) > 0
    for doc in results:
        assert "content" in doc
        assert "metadata" in doc

"""
Unit Tests for RAG Components
Sample test suite for EcoMarket RAG solution
"""

import pytest
from unittest.mock import Mock, patch
import numpy as np

from app.rag.embeddings import EmbeddingService
from app.rag.retriever import DocumentRetriever
from app.rag.generator import ResponseGenerator


class TestEmbeddingService:
    """Tests for EmbeddingService"""
    
    def test_embedding_service_initialization(self):
        """Test embedding service initializes correctly"""
        service = EmbeddingService()
        assert service is not None
        assert service.embedding_dim > 0
    
    def test_embed_text(self):
        """Test single text embedding generation"""
        service = EmbeddingService()
        text = "Test product description"
        embedding = service.embed_text(text)
        
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) == service.embedding_dim
    
    def test_embed_batch(self):
        """Test batch embedding generation"""
        service = EmbeddingService()
        texts = ["Product 1", "Product 2", "Product 3"]
        embeddings = service.embed_batch(texts)
        
        assert embeddings.shape[0] == len(texts)
        assert embeddings.shape[1] == service.embedding_dim
    
    def test_similarity(self):
        """Test cosine similarity calculation"""
        service = EmbeddingService()
        text1 = "Eco-friendly product"
        text2 = "Sustainable item"
        
        emb1 = service.embed_text(text1)
        emb2 = service.embed_text(text2)
        similarity = service.similarity(emb1, emb2)
        
        assert 0.0 <= similarity <= 1.0


class TestDocumentRetriever:
    """Tests for DocumentRetriever"""
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Create mock embedding service"""
        service = Mock(spec=EmbeddingService)
        service.embed_text.return_value = np.random.rand(384)
        return service
    
    @pytest.mark.asyncio
    async def test_retrieve_documents(self, mock_embedding_service):
        """Test document retrieval"""
        retriever = DocumentRetriever(mock_embedding_service)
        query = "eco-friendly products"
        
        # Mock collection.query response
        with patch.object(retriever.collection, 'query') as mock_query:
            mock_query.return_value = {
                'documents': [['Doc 1', 'Doc 2']],
                'metadatas': [[{'id': 1}, {'id': 2}]],
                'distances': [[0.1, 0.2]]
            }
            
            results = await retriever.retrieve(query, top_k=2)
            
            assert len(results) == 2
            assert 'content' in results[0]
            assert 'metadata' in results[0]
            assert 'distance' in results[0]


class TestResponseGenerator:
    """Tests for ResponseGenerator"""
    
    @pytest.mark.asyncio
    async def test_response_generation(self):
        """Test response generation"""
        generator = ResponseGenerator()
        query = "What eco-friendly products do you have?"
        documents = [
            {'content': 'Eco product 1', 'metadata': {}, 'distance': 0.1},
            {'content': 'Eco product 2', 'metadata': {}, 'distance': 0.2}
        ]
        
        with patch('openai.ChatCompletion.acreate') as mock_llm:
            mock_llm.return_value.choices = [
                Mock(message=Mock(content="We have various eco-friendly products"))
            ]
            
            response = await generator.generate(query, documents)
            
            assert 'answer' in response
            assert 'sources' in response
            assert 'confidence' in response
            assert isinstance(response['sources'], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

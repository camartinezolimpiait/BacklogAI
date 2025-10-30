"""
Document Retriever Module
Retrieves relevant documents using vector similarity search
"""

import chromadb
from typing import List, Dict, Any
from loguru import logger
from app.rag.embeddings import EmbeddingService
from app.rag.embeddings_hugging_face import EmbeddingHuggingFaceService
from app.config.settings import get_settings



class DocumentRetriever:  
    """
    Retrieves relevant documents using ChromaDB vector store
    """
    def __init__(self, embedding_service: EmbeddingHuggingFaceService, 
                 collection_name: str = "ecomarketdocs"):
        """
        Initialize the document retriever and populate collection with PDF contents
        Si prefiere usar la biblioteca Hugging Face Transformers, puede manejar manualmente 
        la tokenización y la agrupación cambia el embedding_service a EmbeddingHuggingFaceService de lo
        contrario, use EmbeddingService de sentence-transformers.
        Args:
            embedding_service: Service for generating embeddings
            collection_name: Name of the ChromaDB collection
        """
        import os
        from glob import glob
        try:
            logger.info(f"Initializing document retriever with collection: {collection_name}")
            self.embedding_service = embedding_service
            settings = get_settings()
            self.client = chromadb.Client()
            self.collection = self.client.get_or_create_collection(collection_name)
            self.load_and_index_pdfs()
            self.load_and_index_pdfs_from_blob(
                connection_string=settings.blob_storage_connection_string,
                container_name=settings.blob_container_name
            )
            logger.info("DocumentRetriever initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing DocumentRetriever: {str(e)}")
            raise
   
    def load_and_index_pdfs(self, docs_folder: str = None):
        """
        Load and register PDF documents from docs_folder, splitting into chunks and indexing.
        """
        import os
        from glob import glob
        from pypdf import PdfReader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        try:
            pdf_folder = docs_folder or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs")
            pdf_files = glob(os.path.join(pdf_folder, "*.pdf"))
            logger.info(f"Found {len(pdf_files)} PDF files in {pdf_folder}")
            for pdf_path in pdf_files:
                try:
                    reader = PdfReader(pdf_path)
                    text = "\n".join(page.extract_text() or "" for page in reader.pages)
                    text_temp = text.replace("\n", " ").replace("\r", " ")
                    if text_temp.strip():
                        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                        docs = text_splitter.create_documents([text])
                        for idx, doc in enumerate(docs):
                            chunk_text = doc.page_content if hasattr(doc, 'page_content') else str(doc)
                            embedding = self.embedding_service.embed_text(chunk_text)
                            self.collection.add(
                                documents=[chunk_text],
                                embeddings=[embedding.tolist()],
                                metadatas=[{"filename": os.path.basename(pdf_path), "chunk": idx}],
                                ids=[f"{os.path.splitext(os.path.basename(pdf_path))[0]}_chunk{idx}"]
                            )
                        logger.info(f"Indexed PDF in {len(docs)} chunks: {pdf_path}")
                    else:
                        logger.warning(f"No text extracted from: {pdf_path}")
                except Exception as pdf_err:
                    logger.error(f"Error processing PDF {pdf_path}: {pdf_err}")
        except Exception as e:
            logger.error(f"Error loading and indexing PDFs: {str(e)}")
            raise

    def load_and_index_pdfs_from_blob(self, connection_string: str, container_name: str):
        """
        Load and register PDF documents from Azure Blob Storage, splitting into chunks and indexing.
        """
        from azure.storage.blob import BlobServiceClient
        from tempfile import TemporaryDirectory
        from pypdf import PdfReader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        import os
        try:
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            container_client = blob_service_client.get_container_client(container_name)
            blobs = container_client.list_blobs()
            with TemporaryDirectory() as temp_dir:
                pdf_files = []
                for blob in blobs:
                    if blob.name.lower().endswith('.pdf'):
                        file_path = os.path.join(temp_dir, os.path.basename(blob.name))
                        with open(file_path, "wb") as f:
                            f.write(container_client.download_blob(blob.name).readall())
                        pdf_files.append(file_path)
                logger.info(f"Downloaded {len(pdf_files)} PDF files from Azure Blob Storage")
                for pdf_path in pdf_files:
                    try:
                        reader = PdfReader(pdf_path)
                        text = "\n".join(page.extract_text() or "" for page in reader.pages)
                        text_temp = text.replace("\n", " ").replace("\r", " ")
                        if text_temp.strip():
                            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                            docs = text_splitter.create_documents([text])
                            for idx, doc in enumerate(docs):
                                chunk_text = doc.page_content if hasattr(doc, 'page_content') else str(doc)
                                embedding = self.embedding_service.embed_text(chunk_text)
                                self.collection.add(
                                    documents=[chunk_text],
                                    embeddings=[embedding.tolist()],
                                    metadatas=[{"filename": os.path.basename(pdf_path), "chunk": idx}],
                                    ids=[f"{os.path.splitext(os.path.basename(pdf_path))[0]}_chunk{idx}"]
                                )
                            logger.info(f"Indexed PDF in {len(docs)} chunks: {pdf_path}")
                        else:
                            logger.warning(f"No text extracted from: {pdf_path}")
                    except Exception as pdf_err:
                        logger.error(f"Error processing PDF {pdf_path}: {pdf_err}")
        except Exception as e:
            logger.error(f"Error loading and indexing PDFs from blob: {str(e)}")
            raise

    async def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            
        Returns:
            List of relevant documents with metadata
        """
        try:
            logger.info(f"Retrieving documents for query: {query[:50]}...")
            
            
            # Generate query embedding
            query_embedding = self.embedding_service.embed_text(query)
            
            # Search in vector store
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k
            )
            
            documents = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    documents.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0.0
                    })
            
            logger.info(f"Retrieved {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            raise

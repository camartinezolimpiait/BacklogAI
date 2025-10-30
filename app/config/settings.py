"""
Configuration Settings Module
Centralized configuration using pydantic-settings
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # LangSmith / LangChain Tracing
    langchain_tracing_v2: Optional[str] = Field(None, env="LANGCHAIN_TRACING_V2")
    langchain_api_key: Optional[str] = Field(None, env="LANGCHAIN_API_KEY")
    langchain_project: Optional[str] = Field(None, env="LANGCHAIN_PROJECT")
    """Application settings"""
    
    # Application
    app_name: str = "EcoMarket RAG"
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8000
    
    # OpenAI
    embedding_model: str = "all-MiniLM-L6-v2"

    # Azure OpenAI
    azure_openai_key: Optional[str] = Field(None, env="AZURE_OPENAI_KEY")
    azure_openai_secret: Optional[str] = Field(None, env="AZURE_OPENAI_SECRET")
    azure_openai_endpoint: Optional[str] = Field(None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment_name: Optional[str] = Field(None, env="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_api_version: Optional[str] = Field(None, env="AZURE_OPENAI_API_VERSION")
    

    # Pinecone
    pinecone_api_key: Optional[str] = Field(None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(None, env="PINECONE_ENVIRONMENT")

    # Azure Blob Storage
    blob_storage_connection_string: Optional[str] = Field(None, env="BLOB_STORAGE_CONNECTION_STRING")
    blob_account_name: Optional[str] = Field(None, env="BLOB_ACCOUNT_NAME")
    blob_container_name: Optional[str] = Field(None, env="BLOB_CONTAINER_NAME")
    blob_storage_connection_key: Optional[str] = Field(None, env="BLOB_STORAGE_CONNECTION_KEY")
    blob_url: Optional[str] = Field(None, env="BLOB_URL")
    
    # Vector Store
    vector_store_path: str = "./data/vectorstore"
    collection_name: str = "ecomarket_docs"
    
    # RAG Parameters
    top_k_documents: int = 4
    max_context_length: int = 4000
    temperature: float = 0.7
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = "logs/ecomarket_rag.log"
    
    endpointdataset: str = "https://datasets-server.huggingface.co/rows?dataset=cam2149%2FEcoMarket&config=default&split=train&offset=0&length=100"

    # Orders dataset (populated at app startup)
    rows_dataset: Optional[list] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

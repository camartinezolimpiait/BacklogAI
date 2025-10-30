"""
Response Generator Module
Generates responses using LLM based on retrieved documents
"""

import os
#import openai
from typing import List, Dict, Any
from loguru import logger
# from streamlit import context
from app.config import settings
from app.config.settings import get_settings
from azure.ai.inference.models import SystemMessage, UserMessage

class ResponseGenerator:
    """
    Generates responses using OpenAI LLM with retrieved context
    """
    
    def __init__(self):
        """Initialize the response generator"""
        logger.info("Initializing response generator")
        settings = get_settings()
        self.client = self.init_client()
        self.model = settings.azure_openai_deployment_name or "gpt-4.1-mini"

    def init_client(self):
        """Inicializa el cliente de Azure OpenAI."""
        import os
        from openai import AzureOpenAI, api_version
        settings = get_settings()
        endpoint = settings.azure_openai_endpoint
        subscription_key = settings.azure_openai_key
        api_version = settings.azure_openai_api_version

        return AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=subscription_key,
        )
    
    def get_prompt(self, name):
        """Obtiene el texto de un prompt desde prompts.txt dado el nombre."""
        import re
        ruta = os.path.join(os.path.dirname(__file__), "prompts.txt")
        with open(ruta, encoding="utf-8") as f:
            contenido = f.read()
        patron = rf'{name}\s*=\s*"""(.*?)"""'
        match = re.search(patron, contenido, re.DOTALL)
        if match:
            return match.group(1).strip()
        raise ValueError(f"Prompt '{name}' no encontrado en prompts.txt")
    
   
     
    async def generate(self, query: str, documents: List[Dict[str, Any]], 
                      temperature: float = 0.7) -> Dict[str, Any]:
        """
        Generate response using LLM with document context
        
        Args:
            query: User query
            documents: Retrieved documents
            temperature: LLM temperature parameter
            
        Returns:
            Dict containing answer, sources, and confidence
        """
        try:
            logger.info(f"Generating response for query: {query[:50]}...")
            # Build context from documents
            context = self._build_context(documents)
            logger.info(f"Context from documents: {context[:100]}...")
            # Create prompt
            prompt = self._create_prompt_improved(query, context)
            logger.info(f"Prompt created: {prompt[:100]}...")         
            # Prepare messages for chat completion
            messages = [
                        SystemMessage(content=prompt),
                        UserMessage(content=query)
                 ]
            
            logger.info("Prepare messages for chat completion")

            # Call OpenAI API          
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            
            # Extract answer
            answer = response.choices[0].message['content'] if isinstance(response.choices[0].message, dict) else response.choices[0].message.content

            # Extract sources
            sources = self._format_sources(documents)

            # Calculate confidence (simplified)
            confidence = self._calculate_confidence(documents)

            logger.info("Response generated successfully")
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context string from documents"""
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"Document {i}: {doc['content']}")
        return "\n\n".join(context_parts)
    
    def _create_prompt_basic(self, query: str, context: str) -> str:
        """Create prompt for LLM"""
        prompt_template = self.get_prompt("BASIC").format(context=context)
        return f"".join({prompt_template})

    def _create_prompt_improved(self, query: str, context: str) -> str:
        """Create prompt for LLM"""
        prompt_template = self.get_prompt("IMPROVED").format(context=context)
        return f"""{prompt_template}

Context:
{context}

Question: {query}

Answer:"""
    
    def _format_sources(self, documents: List[Dict[str, Any]]) -> List[Dict]:
        """Format document sources for response"""
        return [
            {
                "content": doc['content'][:200],
                "metadata": doc.get('metadata', {})
            }
            for doc in documents
        ]
    
    def _calculate_confidence(self, documents: List[Dict[str, Any]]) -> float:
        """Calculate confidence score"""
        if not documents:
            return 0.0
        avg_distance = sum(doc.get('distance', 1.0) for doc in documents) / len(documents)
        return max(0.0, min(1.0, 1.0 - avg_distance))

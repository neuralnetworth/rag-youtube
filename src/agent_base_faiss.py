#!/usr/bin/env python3
"""
Modified AgentBase that uses FAISS vector store with OpenAI embeddings.
This is a lightweight alternative to the ChromaDB implementation.
"""
import config
import requests
import langchain
from database import Database
from chain_base import ChainParameters
from vector_store_faiss import FAISSVectorStore
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.llms import Ollama

class AgentBase:
    def __init__(self, config):
        if config.debug():
            langchain.verbose = True
            langchain.debug = True
        self.config = config
        self.embeddings = None
        self.vectorstore = None
    
    def list_ollama_models(self) -> dict:
        base_url = self.config.ollama_url()
        if base_url == 'disabled':
            return {'models': []}
        return requests.get(f'{base_url}/api/tags').json()
    
    def list_openai_models(self) -> dict:
        # TODO: Implement OpenAI model listing
        return {'models': []}
    
    def _build_database(self):
        self.database = Database(self.config)
    
    def _build_embedder(self) -> None:
        """Build embedder - for FAISS we handle this internally."""
        # With FAISS vector store, embeddings are handled by the store itself
        pass
    
    def _build_vectorstore(self) -> None:
        """Build FAISS vector store with OpenAI embeddings."""
        print('[agent] building FAISS vector store with OpenAI embeddings')
        self.vectorstore = FAISSVectorStore(
            config=self.config,
            persist_directory=self.config.db_persist_dir()
        )
    
    def _build_retriever(self, parameters: ChainParameters):
        """Build a retriever from the FAISS vector store."""
        # Create a simple retriever that wraps our FAISS store
        class FAISSRetriever:
            def __init__(self, store, k=4):
                self.store = store
                self.k = k
            
            def get_relevant_documents(self, query):
                results = self.store.similarity_search(query, k=self.k)
                # Convert to LangChain document format
                from langchain.schema import Document
                return [
                    Document(page_content=text, metadata=meta)
                    for text, meta in results
                ]
        
        return FAISSRetriever(
            self.vectorstore, 
            k=parameters.document_count
        )
    
    def _build_llm(self, parameters: ChainParameters) -> BaseLanguageModel:
        """Build LLM based on configuration."""
        if parameters.llm == 'openai':
            return ChatOpenAI(
                model=parameters.llm_model(),
                temperature=parameters.llm_temperature,
                openai_api_key=self.config.openai_api_key(),
                openai_organization=self.config.openai_org_id(),
                max_completion_tokens=4096  # Use o3-compatible parameter
            )
        else:
            # Ollama support (if needed later)
            return Ollama(
                base_url=self.config.ollama_url(),
                model=parameters.llm_model(),
                temperature=parameters.llm_temperature
            )
    
    def _check_embeddings(self):
        """Check if embeddings configuration has changed."""
        # For FAISS with OpenAI, we don't need to check local model changes
        pass
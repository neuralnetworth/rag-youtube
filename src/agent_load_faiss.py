#!/usr/bin/env python3
from agent_base_faiss import AgentBase
from vector_store_faiss import FAISSVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter

class LoaderFAISS(AgentBase):

  def __init__(self, config):
    super().__init__(config)
    self._build_embedder()
    self._build_vectorstore()
    self.splitter = RecursiveCharacterTextSplitter(
      chunk_size=config.split_chunk_size(),
      chunk_overlap=config.split_chunk_overlap()
    )

  def add_text(self, content, metadata) -> None:

    # log
    #print(f'[database] adding {id} to database with metadata {metadata} and content of length {len(content)}')

    # split
    #print('[agent] splitting text')
    all_splits = self.splitter.split_text(content)
    metadatas = [metadata] * len(all_splits)
    
    # create embeddings
    #print('[agent] creating embeddings')
    self.vectorstore.add_texts(all_splits, metadatas=metadatas)

    # done - FAISS saves automatically

  def add_documents(self, documents, metadata) -> None:

    # log
    #print(f'[database] adding {id} to database with metadata {metadata} and content of length {len(content)}')

    # split
    #print('[agent] splitting text')
    all_splits = self.splitter.split_documents(documents)

    # create embeddings
    #print('[agent] creating embeddings')
    texts = [doc.page_content for doc in all_splits]
    metadatas = [doc.metadata for doc in all_splits]
    self.vectorstore.add_texts(texts, metadatas=metadatas)

    # done - FAISS saves automatically
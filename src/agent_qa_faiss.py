#!/usr/bin/env python3
import os
import json
import html
import utils
from agent_base_faiss import AgentBase
from callback import CallbackHandler
from chain_base import ChainParameters
from chain_qa_base import QAChainBase
from chain_qa_sources import QAChainBaseWithSources
from chain_qa_conversation import QAChainConversational
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory, ConversationSummaryMemory

class AgentQA(AgentBase):

  def __init__(self, config):
    super().__init__(config)
    self._build_database()
    self._build_vectorstore()
    # LLM is built per request with specific parameters

  def ask(self, question: str, parameters: ChainParameters) -> dict:

    # init
    self.parameters = parameters
    self.question = question
    response = None
    callback = CallbackHandler(question, parameters)
    
    # Build LLM for this request
    self.llm = self._build_llm(parameters)

    # default to similarity
    if parameters.search_type is None:
      parameters.search_type = 'similarity'

    # build retriever
    retriever = self._build_retriever(parameters)

    # compression retriever
    if parameters.llm_retriever_compression:
      retriever = self._build_compression_retriever(retriever, callback)

    # multi query retriever
    if parameters.llm_retriever_multiquery:
      retriever = self._build_multiquery_retriever(retriever, callback)

    # eval - map 'base' and 'sources' to the correct chain types
    if parameters.chain_type in ['qa_sources', 'sources'] or (parameters.chain_type is None and parameters.memory is None):
      chain = QAChainBaseWithSources(self.llm, retriever, callback, parameters)
      response = chain.invoke(question)
    elif parameters.chain_type in ['qa_basic', 'base'] or (parameters.chain_type is None and parameters.memory):
      chain = QAChainBase(self.llm, retriever, callback, parameters)
      memory = self._build_memory(parameters.memory, parameters.memory_window_size)
      response = chain.invoke(question)
    elif parameters.chain_type in ['qa_conversational', 'conversational']:
      chain = QAChainConversational(self.llm, retriever, callback, parameters)
      memory = self._build_memory(parameters.memory, parameters.memory_window_size)
      response = chain.invoke(question)
    else:
      raise ValueError(f'Unknown chain: {parameters.chain_type}')

    # make URLs clickable
    if response['answer']:
      response['answer'] = utils.make_links_clickable(response['answer'])

    # save to database
    self.database.save({
      'question': question,
      'answer': response['answer'],
      'sources': response['sources'] if 'sources' in response else [],
      'callbacks': callback.get(),
      'parameters': parameters.to_dict(),
    })

    # done
    return response

  def _build_compression_retriever(self, retriever, callback):

    # log
    print('[agent] building compression retriever')

    # build
    compressor = LLMChainExtractor.from_llm(self.llm, callbacks=[callback])
    return ContextualCompressionRetriever(base_compressor=compressor, base_retriever=retriever)

  def _build_multiquery_retriever(self, retriever, callback):

    # log
    print('[agent] building multiquery retriever')

    # build
    return MultiQueryRetriever.from_llm(retriever=retriever, llm=self.llm, callbacks=[callback])

  def _build_memory(self, memory_type, window_size):

    # log
    print(f'[agent] building memory: {memory_type}')

    # build
    if memory_type == 'buffer':
      return ConversationBufferMemory(
        return_messages=True,
        output_key='answer',
        input_key='question'
      )
    elif memory_type == 'buffer_window':
      return ConversationBufferWindowMemory(
        k=window_size,
        return_messages=True,
        output_key='answer',
        input_key='question'
      )
    elif memory_type == 'summary':
      return ConversationSummaryMemory(
        llm=self.llm,
        return_messages=True,
        output_key='answer',
        input_key='question'
      )
    else:
      raise ValueError(f'Unknown memory type: {memory_type}')
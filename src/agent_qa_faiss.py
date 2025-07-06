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

  def ask(self, parameters: ChainParameters) -> dict:

    # init
    self.parameters = parameters
    response = None
    callback = CallbackHandler(parameters.question, parameters)
    
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

    # eval
    if parameters.chain == 'qa_sources' or (parameters.chain is None and parameters.memory is None):
      chain = QAChainBaseWithSources(self.llm, retriever, callback, self.config)
      response = chain.run(parameters)
    elif parameters.chain == 'qa_basic' or (parameters.chain is None and parameters.memory):
      chain = QAChainBase(self.llm, retriever, callback, self.config)
      memory = self._build_memory(parameters.memory, parameters.memory_window_size)
      response = chain.run(parameters, memory)
    elif parameters.chain == 'qa_conversational':
      chain = QAChainConversational(self.llm, retriever, callback, self.config)
      memory = self._build_memory(parameters.memory, parameters.memory_window_size)
      response = chain.run(parameters, memory)
    else:
      raise ValueError(f'Unknown chain: {parameters.chain}')

    # make URLs clickable
    if response['answer']:
      response['answer'] = utils.make_links_clickable(response['answer'])

    # save to database
    self.database.save({
      'question': parameters.question,
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
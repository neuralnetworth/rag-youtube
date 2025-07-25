
from chain_base import ChainBase, ChainParameters
from langchain.chains import ConversationalRetrievalChain

class QAChainConversational(ChainBase):
  
  def __init__(self, llm, retriever, memory, callback, parameters: ChainParameters):
  
    # save callback
    self.callback = callback
    
    # build chain
    print(f'[chain] building conversational retrieval chain of type {parameters.doc_chain_type}')
    self.chain = ConversationalRetrievalChain.from_llm(
      llm=llm,
      chain_type=parameters.doc_chain_type,
      retriever=retriever,
      memory=memory,
      return_source_documents=parameters.return_sources,
      combine_docs_chain_kwargs=self._get_prompt_kwargs(parameters),
    )

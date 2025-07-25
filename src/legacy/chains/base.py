
import utils
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig

class ChainParameters:
  def __init__(self, config, overrides):
    self.llm = overrides['llm'] if 'llm' in overrides else config.llm()
    self.ollama_model = overrides['ollama_model'] if 'ollama_model' in overrides else config.ollama_model()
    self.openai_model = overrides['openai_model'] if 'openai_model' in overrides else config.openai_model()
    self.llm_temperature = float(overrides['llm_temperature']) if 'llm_temperature' in overrides else config.llm_temperature()
    self.chain_type = overrides['chain_type'] if 'chain_type' in overrides else config.chain_type()
    self.doc_chain_type = overrides['doc_chain_type'] if 'doc_chain_type' in overrides else config.doc_chain_type()
    self.search_type = overrides['search_type'] if 'search_type' in overrides else config.search_type()
    self.retriever_type = overrides['retriever_type'] if 'retriever_type' in overrides else config.retriever_type()
    self.score_threshold = float(overrides['score_threshold']) if 'score_threshold' in overrides else config.score_threshold()
    self.document_count = int(overrides['document_count']) if 'document_count' in overrides else config.document_count()
    self.custom_prompts = utils.is_true(overrides['custom_prompts']) if 'custom_prompts' in overrides else config.custom_prompts()
    self.return_sources = utils.is_true(overrides['return_sources']) if 'return_sources' in overrides else config.return_sources()
    
    # Additional parameters needed by agent_qa_faiss
    self.llm_retriever_compression = utils.is_true(overrides['llm_retriever_compression']) if 'llm_retriever_compression' in overrides else False
    self.llm_retriever_multiquery = utils.is_true(overrides['llm_retriever_multiquery']) if 'llm_retriever_multiquery' in overrides else False
    self.memory = overrides.get('memory', None)
    self.memory_window_size = int(overrides['memory_window_size']) if 'memory_window_size' in overrides else 10

  def llm_model(self):
    return self.openai_model if self.llm == 'openai' else self.ollama_model
  
  def to_dict(self):
    return {
      'llm': self.llm,
      'llm_model': self.llm_model(),
      'llm_temperature': self.llm_temperature,
      'chain_type': self.chain_type,
      'doc_chain_type': self.doc_chain_type,
      'search_type': self.search_type,
      'retriever_type': self.retriever_type,
      'score_threshold': self.score_threshold,
      'document_count': self.document_count,
      'custom_prompts': self.custom_prompts,
      'return_sources': self.return_sources,
    }

class ChainBase:

  def __init__(self):
    self.chain = None
    self.callback = None

  def invoke(self, prompt: str):

    # get prompts
    self.callback.templates = self._get_chain_prompt_templates()
    
    # now invoke
    return self.chain.invoke(
      input={ self._get_input_key(): prompt },
      config=RunnableConfig(callbacks=[self.callback])
    )

  def _get_input_key(self):
    return 'question'
  
  def _get_prompt_kwargs(self, parameters: ChainParameters):
    if parameters.custom_prompts:
      if parameters.doc_chain_type == 'stuff':
        return { 'prompt': self.__get_question_prompt() }
      elif parameters.doc_chain_type == 'map_reduce':
        return {
          'question_prompt': self.__get_question_prompt(),
          'combine_prompt': self.__get_combine_prompt(),
        }
    return {}
  
  def __get_question_prompt(self):
    with open('prompts/base.txt', 'r') as f:
      return PromptTemplate(input_variables=['context', 'question'], template=f.read())

  def __get_combine_prompt(self):
    with open('prompts/combine.txt', 'r') as f:
      return PromptTemplate(input_variables=['summaries', 'question'], template=f.read())

  def _get_chain_prompt_templates(self):

    try:

      # we need a chain
      prompts = {}
      if self.chain is None:
        return
      
      # base prompt
      try:
        prompts['chain'] = self.chain.prompt.template
      except:
        pass

      # generator
      try:
        prompts['generator'] = self.chain.question_generator.prompt.template
      except:
        pass

      # retriever
      try:
        prompts['retriever'] = self.chain.retriever.llm_chain.prompt.template
      except:
        pass

      # find the combine chain
      combine_chain = None
      try:
        combine_chain = self.chain.combine_documents_chain
      except:
        pass
      if combine_chain is None:
        try:
          combine_chain = self.chain.combine_docs_chain
        except:
          pass

      # combine chain
      if combine_chain is not None:
        
        # llm
        try:
          prompts['llm'] = combine_chain.llm_chain.prompt.template,
        except:
          pass

        # llm
        try:
          key = 'initial_llm' if 'llm' in prompts else 'llm'
          prompts[key] = combine_chain.initial_llm_chain.prompt.template,
        except:
          pass

        # collapse
        try:
          prompts['collapse'] = combine_chain.collapse_document_chain.llm_chain.prompt.template
        except:
          pass

        # combine
        try:
          prompts['combine'] = combine_chain.combine_document_chain.llm_chain.prompt.template
        except:
          pass

        # refine
        try:
          prompts['refine'] = combine_chain.refine_llm_chain.prompt.template
        except:
          pass
      
      # done
      return prompts

    except:
      print('[chain] failed to get chain prompts')
      return {}

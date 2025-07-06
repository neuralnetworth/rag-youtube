#!/usr/bin/env python3
from agent_base_faiss import AgentBase
from chain_base import ChainParameters
from chain_eval_qa import EvalQAChain
from chain_eval_criteria import EvalCriteriaChain

class AgentEval(AgentBase):

  def __init__(self, config):
    super().__init__(config)
    self._build_llm()
    self._build_vectorstore()

  def evaluate_qa(self, question: str, answer: str, context: str) -> dict:
    return EvalQAChain(self.llm, self.config).run(question, answer, context)

  def evaluate_criteria(self, input: str, output: str, criteria: list) -> dict:
    return EvalCriteriaChain(self.llm, self.config).run(input, output, criteria)
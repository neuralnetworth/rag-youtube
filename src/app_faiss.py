#!/usr/bin/env python3
import os
import json
import consts
import utils
from bottle import Bottle, request, response, run, static_file
from config import Config
from agent_qa_faiss import AgentQA
from chain_base import ChainParameters

# init
config = Config(consts.CONFIG_PATH)
agent = AgentQA(config)
app = Bottle()

# cors
def enable_cors(fn):
  def _enable_cors(*args, **kwargs):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
    if request.method != 'OPTIONS':
      return fn(*args, **kwargs)
  return _enable_cors

# static
@app.route('/')
def index():
  return static_file('index.html', root='public')

@app.route('/<path:path>')
def static(path):
  return static_file(path, root='public')

# dynamic configuration
@app.route('/api/config/models', method='GET')
@enable_cors
def get_config_models():
  llm = config.llm()
  if llm == 'ollama':
    return agent.list_ollama_models()
  elif llm == 'openai':
    return agent.list_openai_models()
  else:
    return {'models': []}

# agent
@app.route('/ask', method='POST')
def ask():
  params = request.json
  parameters = ChainParameters(params)
  return agent.ask(parameters)

@app.route('/dashboard', method='GET')
def dashboard():
  return static_file('dashboard.html', root='public')

# start server
if __name__ == '__main__':
  port = config.value('port', 5555)
  print(f'[app] starting server on port {port}')
  run(app, host='0.0.0.0', port=port, debug=config.debug())
#!/usr/bin/env python3
"""
Start the FAISS-based RAG application.
This wrapper ensures proper module paths are set.
"""
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the FAISS app
from app_faiss import app, config

if __name__ == '__main__':
    from bottle import run
    port = config.value('port', 5555)
    print(f'[app] starting FAISS-based server on port {port}')
    print(f'[app] Open http://localhost:{port} in your browser')
    run(app, host='0.0.0.0', port=port, debug=config.debug())
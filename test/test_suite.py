#!/usr/bin/env python3
"""
Comprehensive test suite for FAISS RAG system.
Run all tests with: ./test_suite.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
from test_vector_store import TestVectorStore
from test_agent_qa import TestAgentQA
from test_chains import TestChains
from test_end_to_end import TestEndToEnd

def main():
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestVectorStore))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentQA))
    suite.addTests(loader.loadTestsFromTestCase(TestChains))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEnd))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == '__main__':
    main()
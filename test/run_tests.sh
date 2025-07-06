#!/bin/bash
# Run all tests with different options

echo "RAG-YouTube FAISS Test Suite"
echo "============================"
echo ""

# Run all tests
echo "Running full test suite..."
python test_suite.py

# Run individual test modules if full suite fails
if [ $? -ne 0 ]; then
    echo ""
    echo "Full suite failed. Running individual test modules:"
    echo ""
    
    echo "1. Testing Vector Store..."
    python test_vector_store.py -v
    echo ""
    
    echo "2. Testing Agent QA..."
    python test_agent_qa.py -v
    echo ""
    
    echo "3. Testing Chains..."
    python test_chains.py -v
    echo ""
    
    echo "4. Testing End-to-End..."
    python test_end_to_end.py -v
fi

echo ""
echo "Test run complete!"
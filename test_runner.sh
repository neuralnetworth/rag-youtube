#!/bin/bash
# RAG-YouTube Test Runner
# Quick access to different test suites

set -e

show_help() {
    echo "RAG-YouTube Test Runner"
    echo ""
    echo "Usage: ./test_runner.sh [command]"
    echo ""
    echo "Commands:"
    echo "  quick      - Run essential FastAPI test (fast)"
    echo "  core       - Run core FastAPI tests"
    echo "  full       - Run comprehensive test suite"  
    echo "  pytest     - Run modern pytest-based tests"
    echo "  performance - Run performance benchmarks"
    echo "  api        - Run API integration tests (requires server)"
    echo "  legacy     - Run legacy LangChain tests"
    echo "  all        - Run all tests except legacy and API"
    echo ""
    echo "Examples:"
    echo "  ./test_runner.sh quick"
    echo "  ./test_runner.sh core"
    echo "  ./test_runner.sh pytest --verbose"
}

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "Error: UV package manager not found. Install from https://docs.astral.sh/uv/"
    exit 1
fi

# Set working directory to project root
cd "$(dirname "$0")"

case "${1:-help}" in
    "quick")
        echo "🚀 Running Quick Test (Essential FastAPI functionality)"
        uv run python test/test_basic_functionality_fastapi.py
        ;;
    
    "core")
        echo "🧪 Running Core FastAPI Tests"
        uv run python test/run_all_tests.py --category "Core FastAPI Tests"
        ;;
    
    "full")
        echo "🔬 Running Comprehensive Test Suite"
        uv run python test/test_comprehensive.py
        ;;
    
    "pytest")
        echo "⚡ Running Pytest-based Tests"
        # Install pytest if not available
        uv add pytest --dev --quiet 2>/dev/null || true
        shift  # Remove 'pytest' from arguments
        uv run pytest test/test_pytest_core.py "$@"
        ;;
    
    "performance")
        echo "📊 Running Performance Benchmarks"
        uv run python test/test_performance.py
        ;;
    
    "api")
        echo "🌐 Running API Integration Tests"
        echo "Note: Make sure FastAPI server is running at http://localhost:8000"
        read -p "Is the server running? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            uv run python test/test_fastapi.py
        else
            echo "Start server with: ./run_fastapi.sh"
            exit 1
        fi
        ;;
    
    "legacy")
        echo "🔧 Running Legacy LangChain Tests"
        uv run python test/run_all_tests.py --category "Legacy Tests"
        ;;
    
    "all")
        echo "🎯 Running All Tests (excluding legacy and API)"
        uv run python test/run_all_tests.py --skip-legacy --skip-api
        ;;
    
    "help"|"--help"|"-h")
        show_help
        ;;
    
    *)
        echo "Error: Unknown command '$1'"
        echo ""
        show_help
        exit 1
        ;;
esac
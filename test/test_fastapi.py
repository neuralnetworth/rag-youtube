#!/usr/bin/env python3
"""
Test script for FastAPI implementation.
"""
import sys
import os
import asyncio
import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Base URL for the API
BASE_URL = "http://localhost:8000"


async def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        assert response.json()["status"] in ["healthy", "unhealthy"]
    print("✓ Health check passed\n")


async def test_stats():
    """Test stats endpoint."""
    print("Testing stats endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/stats")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total documents: {data['total_documents']}")
        print(f"Model: {data['model']}")
        print(f"Embeddings model: {data['embeddings_model']}")
        assert response.status_code == 200
        assert data["total_documents"] > 0
    print("✓ Stats endpoint passed\n")


async def test_filter_options():
    """Test filter options endpoint."""
    print("Testing filter options endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/filters/options")
        print(f"Status: {response.status_code}")
        data = response.json()
        
        print(f"Total documents: {data['total_documents']}")
        print(f"Caption coverage: {data['caption_coverage']}")
        print(f"Categories: {list(data['categories'].keys())}")
        print(f"Quality levels: {list(data['quality_levels'].keys())}")
        
        assert response.status_code == 200
        assert "total_documents" in data
        assert "caption_coverage" in data
        assert "categories" in data
        assert "quality_levels" in data
        assert "date_range" in data
        
        # Check caption coverage structure
        coverage = data['caption_coverage']
        assert "with_captions" in coverage
        assert "without_captions" in coverage
        assert "percentage" in coverage
        
    print("✓ Filter options endpoint passed\n")


async def test_ask():
    """Test ask endpoint (non-streaming)."""
    print("Testing ask endpoint...")
    async with httpx.AsyncClient() as client:
        question = "What is gamma in options trading?"
        
        response = await client.post(
            f"{BASE_URL}/api/ask",
            json={
                "question": question,
                "num_sources": 4,
                "search_type": "similarity",
                "temperature": 0.7,
                "stream": False
            }
        )
        
        print(f"Status: {response.status_code}")
        data = response.json()
        
        print(f"\nQuestion: {question}")
        print(f"Answer preview: {data['answer'][:200]}...")
        print(f"Number of sources: {len(data['sources'])}")
        print(f"Processing time: {data['processing_time']:.2f} seconds")
        
        assert response.status_code == 200
        assert len(data["answer"]) > 0
        assert len(data["sources"]) > 0
    print("✓ Ask endpoint passed\n")


async def test_ask_with_filters():
    """Test ask endpoint with filters."""
    print("Testing ask endpoint with filters...")
    async with httpx.AsyncClient() as client:
        question = "How do gamma squeezes work?"
        
        # Test with caption filter
        response = await client.post(
            f"{BASE_URL}/api/ask",
            json={
                "question": question,
                "num_sources": 3,
                "search_type": "similarity",
                "temperature": 0.7,
                "stream": False,
                "filters": {
                    "require_captions": True
                }
            }
        )
        
        print(f"Status: {response.status_code}")
        data = response.json()
        
        print(f"\nQuestion: {question}")
        print(f"Answer preview: {data['answer'][:150]}...")
        print(f"Number of sources (with caption filter): {len(data['sources'])}")
        print(f"Processing time: {data['processing_time']:.2f} seconds")
        
        # Check that sources have caption metadata
        for i, source in enumerate(data['sources']):
            has_captions = source['metadata'].get('has_captions')
            print(f"  Source {i+1}: has_captions = {has_captions}")
        
        assert response.status_code == 200
        assert len(data["answer"]) > 0
        assert len(data["sources"]) > 0
    print("✓ Ask endpoint with filters passed\n")


async def test_ask_stream():
    """Test streaming ask endpoint."""
    print("Testing streaming ask endpoint...")
    async with httpx.AsyncClient() as client:
        question = "How do gamma squeezes work?"
        
        response = await client.post(
            f"{BASE_URL}/api/ask/stream",
            json={
                "question": question,
                "num_sources": 3,
                "search_type": "similarity",
                "temperature": 0.7,
                "stream": True
            }
        )
        
        print(f"Status: {response.status_code}")
        print(f"Question: {question}")
        print("Streaming response:")
        
        sources_count = 0
        tokens_count = 0
        
        # Process streaming response
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                import json
                data = json.loads(line[6:])
                
                if data["type"] == "source":
                    sources_count += 1
                    print(f"  [Source {sources_count}] received")
                elif data["type"] == "token":
                    tokens_count += 1
                    print(data["content"], end="", flush=True)
                elif data["type"] == "done":
                    print("\n  [Streaming complete]")
                    break
                elif data["type"] == "error":
                    print(f"\n  [Error] {data['content']}")
                    break
        
        assert response.status_code == 200
        assert sources_count > 0
        assert tokens_count > 0
    print("✓ Streaming endpoint passed\n")


async def test_ask_stream_with_filters():
    """Test streaming ask endpoint with filters."""
    print("Testing streaming ask endpoint with filters...")
    async with httpx.AsyncClient() as client:
        question = "What does SpotGamma say about 0DTE options?"
        
        response = await client.post(
            f"{BASE_URL}/api/ask/stream",
            json={
                "question": question,
                "num_sources": 3,
                "search_type": "similarity",
                "temperature": 0.7,
                "stream": True,
                "filters": {
                    "require_captions": True
                }
            }
        )
        
        print(f"Status: {response.status_code}")
        print(f"Question: {question}")
        print("Streaming response with filters:")
        
        sources_count = 0
        tokens_count = 0
        
        # Process streaming response
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                import json
                data = json.loads(line[6:])
                
                if data["type"] == "source":
                    sources_count += 1
                    # Parse source to check metadata
                    source_data = json.loads(data["content"])
                    has_captions = source_data.get('metadata', {}).get('has_captions')
                    print(f"  [Source {sources_count}] received (has_captions: {has_captions})")
                elif data["type"] == "token":
                    tokens_count += 1
                    print(data["content"], end="", flush=True)
                elif data["type"] == "done":
                    print("\n  [Streaming complete]")
                    break
                elif data["type"] == "error":
                    print(f"\n  [Error] {data['content']}")
                    break
        
        assert response.status_code == 200
        assert sources_count > 0
        assert tokens_count > 0
    print("✓ Streaming endpoint with filters passed\n")


async def test_ui():
    """Test that UI is served."""
    print("Testing UI endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        
        # Check if it's HTML or JSON
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type:
            print("✓ UI HTML page served successfully")
            assert "RAG-YouTube" in response.text
        else:
            # If static files aren't set up yet, API info is returned
            print("✓ API info returned (static files not found)")
        
        assert response.status_code == 200
    print("✓ UI endpoint passed\n")


async def run_all_tests():
    """Run all tests."""
    print("="*60)
    print("FastAPI RAG-YouTube Test Suite")
    print("="*60)
    print("\nMake sure the FastAPI server is running at http://localhost:8000")
    print("Start it with: uvicorn src.api.main:app --reload\n")
    
    try:
        # First check if server is running
        async with httpx.AsyncClient() as client:
            try:
                await client.get(f"{BASE_URL}/api/health", timeout=2.0)
            except (httpx.ConnectError, httpx.TimeoutException):
                print("❌ ERROR: Cannot connect to FastAPI server!")
                print("Please start the server first with:")
                print("  cd /path/to/rag-youtube")
                print("  uvicorn src.api.main:app --reload")
                return
        
        # Run tests
        await test_health()
        await test_stats()
        await test_filter_options()
        await test_ask()
        await test_ask_with_filters()
        await test_ask_stream()
        await test_ask_stream_with_filters()
        await test_ui()
        
        print("="*60)
        print("✅ All tests passed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
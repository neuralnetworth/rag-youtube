#!/usr/bin/env python3
"""
Performance and benchmark tests for RAG-YouTube.
Tests response times, memory usage, and scalability.
"""
import sys
import os
import time
import asyncio
import concurrent.futures
from typing import List, Dict, Any
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.config import Config
from api.rag_engine import RAGEngine


class PerformanceBenchmark:
    """Performance testing and benchmarking utilities."""
    
    def __init__(self):
        self.config = Config()
        self.rag_engine = RAGEngine(self.config)
        self.results = []
    
    def measure_time(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        return result, duration
    
    async def measure_time_async(self, func, *args, **kwargs):
        """Measure execution time of an async function."""
        start_time = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start_time
        return result, duration
    
    def record_result(self, test_name: str, duration: float, details: Dict[str, Any] = None):
        """Record a performance test result."""
        self.results.append({
            'test': test_name,
            'duration': duration,
            'details': details or {}
        })
    
    def print_results(self):
        """Print performance test results."""
        print(f"\n{'='*80}")
        print("PERFORMANCE BENCHMARK RESULTS")
        print(f"{'='*80}")
        
        for result in self.results:
            test = result['test']
            duration = result['duration']
            details = result['details']
            
            print(f"\n{test}:")
            print(f"  Duration: {duration:.3f} seconds")
            
            if details:
                for key, value in details.items():
                    print(f"  {key}: {value}")
        
        # Summary statistics
        if self.results:
            durations = [r['duration'] for r in self.results]
            print(f"\nSUMMARY:")
            print(f"  Total tests: {len(self.results)}")
            print(f"  Total time: {sum(durations):.3f} seconds")
            print(f"  Average time: {statistics.mean(durations):.3f} seconds")
            print(f"  Median time: {statistics.median(durations):.3f} seconds")
            if len(durations) > 1:
                print(f"  Std deviation: {statistics.stdev(durations):.3f} seconds")


def test_vector_search_performance():
    """Test vector search performance with different query sizes."""
    print("\n" + "="*60)
    print("Testing Vector Search Performance")
    print("="*60)
    
    benchmark = PerformanceBenchmark()
    
    # Test queries of different complexity
    test_queries = [
        "gamma",
        "gamma options",
        "gamma options trading",
        "gamma options trading strategies market",
        "gamma options trading strategies market volatility analysis"
    ]
    
    for query in test_queries:
        result, duration = benchmark.measure_time(
            benchmark.rag_engine.retrieve_sources,
            query,
            num_sources=5
        )
        
        benchmark.record_result(
            f"Vector Search: '{query[:30]}...'",
            duration,
            {
                'query_length': len(query),
                'sources_found': len(result),
                'sources_per_second': len(result) / duration if duration > 0 else 0
            }
        )
        
        print(f"  Query: '{query}' -> {len(result)} sources in {duration:.3f}s")
    
    benchmark.print_results()
    return benchmark


def test_answer_generation_performance():
    """Test answer generation performance."""
    print("\n" + "="*60)
    print("Testing Answer Generation Performance")
    print("="*60)
    
    benchmark = PerformanceBenchmark()
    
    # Test questions of varying complexity
    test_questions = [
        "What is gamma?",
        "How do gamma squeezes work in options trading?",
        "Explain the relationship between gamma, delta, and dealer positioning in options markets during high volatility periods"
    ]
    
    for question in test_questions:
        # Get sources first
        sources = benchmark.rag_engine.retrieve_sources(question, num_sources=3)
        context = benchmark.rag_engine.build_context(sources)
        
        # Measure answer generation
        answer, duration = benchmark.measure_time(
            benchmark.rag_engine.generate_answer,
            question,
            context
        )
        
        benchmark.record_result(
            f"Answer Generation: {len(question)} chars",
            duration,
            {
                'question_length': len(question),
                'answer_length': len(answer),
                'context_length': len(context),
                'chars_per_second': len(answer) / duration if duration > 0 else 0
            }
        )
        
        print(f"  Question: {len(question)} chars -> {len(answer)} char answer in {duration:.3f}s")
    
    benchmark.print_results()
    return benchmark


async def test_async_performance():
    """Test async operation performance."""
    print("\n" + "="*60)
    print("Testing Async Performance")
    print("="*60)
    
    benchmark = PerformanceBenchmark()
    
    questions = [
        "What is gamma?",
        "How do gamma squeezes work?",
        "Explain dealer positioning"
    ]
    
    # Test sequential async
    start_time = time.time()
    for question in questions:
        result = await benchmark.rag_engine.ask_async(question, num_sources=2)
    sequential_time = time.time() - start_time
    
    print(f"  Sequential async: {sequential_time:.3f}s for {len(questions)} questions")
    
    # Test concurrent async (if multiple providers available)
    providers = benchmark.rag_engine.llm_manager.list_providers()
    if len(providers) > 1:
        start_time = time.time()
        tasks = []
        for i, question in enumerate(questions):
            provider = providers[i % len(providers)]
            task = benchmark.rag_engine.ask_async(question, num_sources=2, provider=provider)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        concurrent_time = time.time() - start_time
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        print(f"  Concurrent async: {concurrent_time:.3f}s for {success_count}/{len(questions)} questions")
        
        if success_count > 0:
            speedup = sequential_time / concurrent_time
            print(f"  Speedup: {speedup:.2f}x")
    
    return benchmark


def test_streaming_performance():
    """Test streaming performance."""
    print("\n" + "="*60)
    print("Testing Streaming Performance")
    print("="*60)
    
    benchmark = PerformanceBenchmark()
    
    async def test_streaming():
        question = "Explain dealer gamma positioning in detail"
        sources = benchmark.rag_engine.retrieve_sources(question, num_sources=3)
        context = benchmark.rag_engine.build_context(sources)
        
        start_time = time.time()
        first_token_time = None
        chunks = []
        
        async for chunk in benchmark.rag_engine.generate_answer_stream(question, context):
            if first_token_time is None:
                first_token_time = time.time() - start_time
            chunks.append(chunk)
        
        total_time = time.time() - start_time
        full_answer = ''.join(chunks)
        
        benchmark.record_result(
            "Streaming Generation",
            total_time,
            {
                'first_token_latency': first_token_time,
                'total_chunks': len(chunks),
                'total_characters': len(full_answer),
                'chunks_per_second': len(chunks) / total_time if total_time > 0 else 0,
                'chars_per_second': len(full_answer) / total_time if total_time > 0 else 0
            }
        )
        
        print(f"  First token: {first_token_time:.3f}s")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Chunks: {len(chunks)}")
        print(f"  Characters: {len(full_answer)}")
    
    asyncio.run(test_streaming())
    benchmark.print_results()
    return benchmark


def test_concurrent_users():
    """Test performance under concurrent user load."""
    print("\n" + "="*60)
    print("Testing Concurrent User Performance")
    print("="*60)
    
    benchmark = PerformanceBenchmark()
    
    def single_user_request(user_id: int):
        """Simulate a single user request."""
        question = f"What is gamma? (User {user_id})"
        start_time = time.time()
        result = benchmark.rag_engine.ask(question, num_sources=2)
        duration = time.time() - start_time
        return {
            'user_id': user_id,
            'duration': duration,
            'answer_length': len(result['answer']),
            'sources_count': len(result['sources'])
        }
    
    # Test with different concurrent user counts
    user_counts = [1, 2, 5]
    
    for num_users in user_counts:
        print(f"\n  Testing {num_users} concurrent users...")
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(single_user_request, i) for i in range(num_users)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        durations = [r['duration'] for r in results]
        avg_duration = statistics.mean(durations)
        max_duration = max(durations)
        throughput = num_users / total_time
        
        benchmark.record_result(
            f"Concurrent Users: {num_users}",
            total_time,
            {
                'avg_response_time': avg_duration,
                'max_response_time': max_duration,
                'throughput_users_per_sec': throughput,
                'successful_requests': len(results)
            }
        )
        
        print(f"    Total time: {total_time:.3f}s")
        print(f"    Avg response: {avg_duration:.3f}s")
        print(f"    Max response: {max_duration:.3f}s")
        print(f"    Throughput: {throughput:.2f} users/sec")
    
    benchmark.print_results()
    return benchmark


def test_memory_usage():
    """Test memory usage patterns."""
    print("\n" + "="*60)
    print("Testing Memory Usage")
    print("="*60)
    
    try:
        import psutil
        process = psutil.Process()
        
        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"  Baseline memory: {baseline_memory:.1f} MB")
        
        benchmark = PerformanceBenchmark()
        
        # Test memory during operations
        questions = ["What is gamma?"] * 10
        
        for i, question in enumerate(questions):
            result = benchmark.rag_engine.ask(question, num_sources=3)
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - baseline_memory
            
            if i % 5 == 0:  # Print every 5th iteration
                print(f"    After {i+1} requests: {current_memory:.1f} MB (+{memory_increase:.1f} MB)")
        
        # Final memory
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - baseline_memory
        
        print(f"  Final memory: {final_memory:.1f} MB")
        print(f"  Total increase: {total_increase:.1f} MB")
        print(f"  Memory per request: {total_increase/len(questions):.2f} MB")
        
    except ImportError:
        print("  psutil not available - skipping memory tests")
        print("  Install with: pip install psutil")


def main():
    """Run all performance tests."""
    print("RAG-YouTube Performance Benchmark Suite")
    print("=" * 80)
    
    # Check if vector store is available
    if not os.path.exists('db/faiss.index'):
        print("❌ No FAISS index found - run document_loader_faiss.py first")
        return 1
    
    start_time = time.time()
    
    # Run performance tests
    test_vector_search_performance()
    test_answer_generation_performance()
    asyncio.run(test_async_performance())
    asyncio.run(test_streaming_performance())
    test_concurrent_users()
    test_memory_usage()
    
    total_time = time.time() - start_time
    
    print(f"\n{'='*80}")
    print(f"PERFORMANCE BENCHMARK COMPLETE")
    print(f"Total benchmark time: {total_time:.2f} seconds")
    print(f"{'='*80}")
    
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
#!/usr/bin/env python3
"""
Master test runner for RAG-YouTube test suite.
Runs tests in logical order with proper error handling and reporting.
"""
import sys
import os
import subprocess
import time
from typing import List, Dict, Any

# Test categories and their files
TEST_CATEGORIES = {
    "Core FastAPI Tests": [
        "test_basic_functionality_fastapi.py",
        "test_filtering.py",
    ],
    "Comprehensive Tests": [
        "test_comprehensive.py",
    ],
    "API Integration Tests": [
        "test_fastapi.py",  # Requires server running
    ],
    "Legacy Tests": [
        "test_basic_functionality.py",
        "test_minimal.py",
        "test_faiss_simple.py",
    ]
}

# Tests that require external services
REQUIRES_SERVER = {
    "test_fastapi.py": "FastAPI server at http://localhost:8000"
}


class TestRunner:
    """Manages test execution and reporting."""
    
    def __init__(self):
        self.results = []
        self.total_time = 0
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(self.test_dir)
    
    def run_test(self, test_file: str, category: str) -> Dict[str, Any]:
        """Run a single test file and return results."""
        test_path = os.path.join(self.test_dir, test_file)
        
        print(f"\n{'='*80}")
        print(f"Running: {test_file} ({category})")
        print(f"{'='*80}")
        
        # Check if test file exists
        if not os.path.exists(test_path):
            result = {
                'test': test_file,
                'category': category,
                'status': 'SKIP',
                'duration': 0,
                'message': 'Test file not found'
            }
            print(f"⚠️  SKIPPED: {test_file} - File not found")
            return result
        
        # Check if external service is required
        if test_file in REQUIRES_SERVER:
            service = REQUIRES_SERVER[test_file]
            print(f"ℹ️  Note: This test requires {service}")
            
            # For FastAPI tests, check if server is running
            if "fastapi" in test_file.lower():
                try:
                    import httpx
                    import asyncio
                    
                    async def check_server():
                        async with httpx.AsyncClient() as client:
                            response = await client.get("http://localhost:8000/api/health", timeout=2.0)
                            return response.status_code == 200
                    
                    if not asyncio.run(check_server()):
                        raise Exception("Server not responding")
                        
                except Exception:
                    result = {
                        'test': test_file,
                        'category': category,
                        'status': 'SKIP',
                        'duration': 0,
                        'message': f'Required service not available: {service}'
                    }
                    print(f"⚠️  SKIPPED: {test_file} - {service} not available")
                    return result
        
        # Run the test
        start_time = time.time()
        try:
            # Change to project root for consistent imports
            result = subprocess.run(
                [sys.executable, test_path],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                status = 'PASS'
                message = 'All tests passed'
                print(f"✅ PASSED: {test_file} ({duration:.2f}s)")
            else:
                status = 'FAIL'
                message = f'Exit code: {result.returncode}'
                print(f"❌ FAILED: {test_file} ({duration:.2f}s)")
                print(f"STDERR: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            status = 'FAIL'
            message = 'Test timed out (5 minutes)'
            print(f"⏰ TIMEOUT: {test_file} ({duration:.2f}s)")
            
        except Exception as e:
            duration = time.time() - start_time
            status = 'FAIL'
            message = str(e)
            print(f"💥 ERROR: {test_file} ({duration:.2f}s) - {e}")
        
        return {
            'test': test_file,
            'category': category,
            'status': status,
            'duration': duration,
            'message': message
        }
    
    def run_category(self, category: str, test_files: List[str]) -> None:
        """Run all tests in a category."""
        print(f"\n{'#'*80}")
        print(f"CATEGORY: {category}")
        print(f"{'#'*80}")
        
        for test_file in test_files:
            result = self.run_test(test_file, category)
            self.results.append(result)
            self.total_time += result['duration']
    
    def print_summary(self) -> None:
        """Print test execution summary."""
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        skipped = sum(1 for r in self.results if r['status'] == 'SKIP')
        
        print(f"\n{'='*80}")
        print(f"TEST EXECUTION SUMMARY")
        print(f"{'='*80}")
        print(f"Total Tests:   {len(self.results)}")
        print(f"Passed:        {passed}")
        print(f"Failed:        {failed}")
        print(f"Skipped:       {skipped}")
        print(f"Total Time:    {self.total_time:.2f} seconds")
        print(f"Success Rate:  {(passed/(passed+failed)*100):.1f}%" if (passed+failed) > 0 else "N/A")
        print(f"{'='*80}")
        
        # Category breakdown
        print(f"\nRESULTS BY CATEGORY:")
        for category in TEST_CATEGORIES.keys():
            cat_results = [r for r in self.results if r['category'] == category]
            if cat_results:
                cat_passed = sum(1 for r in cat_results if r['status'] == 'PASS')
                cat_total = len(cat_results)
                print(f"  {category}: {cat_passed}/{cat_total}")
        
        # Failed tests detail
        failed_tests = [r for r in self.results if r['status'] == 'FAIL']
        if failed_tests:
            print(f"\nFAILED TESTS:")
            for result in failed_tests:
                print(f"  ❌ {result['test']}: {result['message']}")
        
        # Skipped tests detail
        skipped_tests = [r for r in self.results if r['status'] == 'SKIP']
        if skipped_tests:
            print(f"\nSKIPPED TESTS:")
            for result in skipped_tests:
                print(f"  ⚠️  {result['test']}: {result['message']}")
        
        print(f"\n{'='*80}")
    
    def run_all(self, skip_legacy: bool = False, skip_api: bool = False) -> int:
        """Run all test categories."""
        print("RAG-YouTube Test Suite")
        print("=" * 80)
        print(f"Project Root: {self.project_root}")
        print(f"Test Directory: {self.test_dir}")
        
        # Check environment
        self.check_environment()
        
        for category, test_files in TEST_CATEGORIES.items():
            # Skip categories based on flags
            if skip_legacy and "Legacy" in category:
                print(f"\n⚠️  Skipping {category} (--skip-legacy)")
                continue
            if skip_api and "API Integration" in category:
                print(f"\n⚠️  Skipping {category} (--skip-api)")
                continue
                
            self.run_category(category, test_files)
        
        self.print_summary()
        
        # Return exit code
        failed_count = sum(1 for r in self.results if r['status'] == 'FAIL')
        return 0 if failed_count == 0 else 1
    
    def check_environment(self) -> None:
        """Check test environment prerequisites."""
        print(f"\nEnvironment Check:")
        
        # Check for required files
        required_files = [
            'src/core/config.py',
            'src/api/rag_engine.py',
            'rag-youtube.conf'
        ]
        
        for file_path in required_files:
            full_path = os.path.join(self.project_root, file_path)
            if os.path.exists(full_path):
                print(f"  ✅ {file_path}")
            else:
                print(f"  ❌ {file_path} (missing)")
        
        # Check for vector database
        faiss_path = os.path.join(self.project_root, 'db', 'faiss.index')
        if os.path.exists(faiss_path):
            print(f"  ✅ Vector database (FAISS)")
        else:
            print(f"  ⚠️  Vector database (FAISS) - run document_loader_faiss.py first")
        
        # Check for API keys
        env_path = os.path.join(self.project_root, '.env')
        if os.path.exists(env_path):
            print(f"  ✅ Environment file (.env)")
        else:
            print(f"  ⚠️  Environment file (.env) - copy from .env.sample")
        
        print()


def main():
    """Main test runner entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run RAG-YouTube test suite')
    parser.add_argument('--skip-legacy', action='store_true', 
                       help='Skip legacy LangChain tests')
    parser.add_argument('--skip-api', action='store_true',
                       help='Skip API integration tests that require server')
    parser.add_argument('--category', type=str,
                       help='Run only tests from specific category')
    parser.add_argument('--list-categories', action='store_true',
                       help='List available test categories')
    
    args = parser.parse_args()
    
    if args.list_categories:
        print("Available test categories:")
        for category, tests in TEST_CATEGORIES.items():
            print(f"  {category}:")
            for test in tests:
                print(f"    - {test}")
        return 0
    
    runner = TestRunner()
    
    if args.category:
        if args.category in TEST_CATEGORIES:
            runner.run_category(args.category, TEST_CATEGORIES[args.category])
            runner.print_summary()
            failed_count = sum(1 for r in runner.results if r['status'] == 'FAIL')
            return 0 if failed_count == 0 else 1
        else:
            print(f"Error: Unknown category '{args.category}'")
            print("Use --list-categories to see available categories")
            return 1
    
    return runner.run_all(
        skip_legacy=args.skip_legacy,
        skip_api=args.skip_api
    )


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
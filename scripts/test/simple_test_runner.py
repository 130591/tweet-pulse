#!/usr/bin/env python3
"""
Simple test runner that avoids problematic pytest plugins.
Run with: python3 scripts/simple_test_runner.py
"""
import sys
import os
import asyncio
from pathlib import Path

# Add both src and tests to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'tests'))

# Mock redis to use fakeredis
sys.modules['redis'] = __import__('fakeredis.aioredis', fromlist=['FakeRedis'])

def run_single_test(test_module, test_class, test_method):
    """Run a single test method."""
    print(f"Running {test_module}.{test_class}.{test_method}...")

    try:
        # Import test module
        module_path = f"test_integration.{test_module}"
        test_module_obj = __import__(module_path, fromlist=[test_class])

        # Get test class
        test_cls = getattr(test_module_obj, test_class)

        # Create test instance (without fixtures)
        test_instance = test_cls()

        # Get test method
        test_method_obj = getattr(test_instance, test_method)

        # Run test
        if asyncio.iscoroutinefunction(test_method_obj):
            result = asyncio.run(test_method_obj())
        else:
            result = test_method_obj()

        print(f"✅ {test_module}.{test_class}.{test_method} PASSED")
        return True

    except Exception as e:
        print(f"❌ {test_module}.{test_class}.{test_method} FAILED: {e}")
        return False

def main():
    """Run integration tests."""
    print("=" * 60)
    print("Tweet Pulse - Simple Test Runner")
    print("=" * 60)
    print()

    # Test files to run
    tests = [
        ("test_storage_integration", "TestStorageIntegration", "test_store_tweet_to_cache"),
        ("test_enrichment_integration", "TestEnrichmentIntegration", "test_enrich_tweet_basic"),
        ("test_deduplication_integration", "TestDeduplicationIntegration", "test_first_tweet_not_duplicate"),
        ("test_pipeline_integration", "TestPipelineIntegration", "test_pipeline_processes_tweet_end_to_end"),
    ]

    passed = 0
    total = len(tests)

    for test_module, test_class, test_method in tests:
        if run_single_test(test_module, test_class, test_method):
            passed += 1

    print()
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

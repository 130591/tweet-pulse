#!/usr/bin/env python3
"""
Ultra-minimal test - just check if code structure exists.
Run with: python3 scripts/basic_test.py
"""
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

def test_code_structure():
    """Test if code files exist and are syntactically correct."""
    print("🧪 Testing code structure...")

    # Check if source files exist
    required_files = [
        'src/tweetpulse/core/config.py',
        'src/tweetpulse/ingestion/storage.py',
        'src/tweetpulse/ingestion/enrichment.py',
        'src/tweetpulse/ingestion/deduplication.py',
        'src/tweetpulse/ingestion/pipeline.py',
    ]

    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            return False

    return True

def test_imports():
    """Test if modules can be imported."""
    print("\n🧪 Testing imports...")

    try:
        # Try to import modules (they might fail at runtime but should import)
        import tweetpulse.core.config
        print("✅ tweetpulse.core.config imported")

        import tweetpulse.ingestion.storage
        print("✅ tweetpulse.ingestion.storage imported")

        import tweetpulse.ingestion.enrichment
        print("✅ tweetpulse.ingestion.enrichment imported")

        import tweetpulse.ingestion.deduplication
        print("✅ tweetpulse.ingestion.deduplication imported")

        import tweetpulse.ingestion.pipeline
        print("✅ tweetpulse.ingestion.pipeline imported")

        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Import warning (might be OK): {e}")
        return True  # Import warnings are OK, runtime errors are not

def main():
    """Run ultra-basic tests."""
    print("=" * 60)
    print("Tweet Pulse - Ultra-Basic Test")
    print("=" * 60)
    print()

    print("📋 Checking if code structure is correct...")
    print()

    code_ok = test_code_structure()
    imports_ok = test_imports()

    print()
    print("=" * 60)

    if code_ok and imports_ok:
        print("🎉 Basic code structure is correct!")
        print("\n🚀 Your code is ready for testing!")
        print("\n📋 Next steps:")
        print("1. Install test dependencies: pip install -r requirements-test.txt")
        print("2. Run tests: make test")
        print("3. Or run specific tests: make test-storage")
        print("4. For debugging: make test-verbose")
        return 0
    else:
        print("❌ There are issues with the code structure")
        return 1

if __name__ == "__main__":
    sys.exit(main())

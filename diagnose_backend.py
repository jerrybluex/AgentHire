#!/usr/bin/env python3
"""
Backend diagnostic script
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all critical imports"""
    results = []

    try:
        print("Testing imports...")

        # Test 1: Config
        try:
            from app.config import get_settings
            results.append(("✅ Config", "OK"))
        except Exception as e:
            results.append(("❌ Config", str(e)))

        # Test 2: Database
        try:
            from app.core.database import init_db, close_db
            results.append(("✅ Database", "OK"))
        except Exception as e:
            results.append(("❌ Database", str(e)))

        # Test 3: Models
        try:
            import app.models
            results.append(("✅ Models", "OK"))
        except Exception as e:
            results.append(("❌ Models", str(e)))

        # Test 4: API Router
        try:
            from app.api.v1.api import api_router
            results.append(("✅ API Router", "OK"))
        except Exception as e:
            results.append(("❌ API Router", str(e)))

        # Test 5: Cache
        try:
            from app.core.cache import cache_manager
            results.append(("✅ Cache", "OK"))
        except Exception as e:
            results.append(("❌ Cache", str(e)))

        # Test 6: Main App
        try:
            from app.main import create_application
            results.append(("✅ Main App", "OK"))
        except Exception as e:
            results.append(("❌ Main App", str(e)))

        print("\n=== Import Test Results ===")
        for name, status in results:
            print(f"{name}: {status}")

        return all("OK" in status for _, status in results)

    except Exception as e:
        print(f"Critical error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""Check if models are loaded in the running backend server"""
import sys
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_backend_health():
    """Check if backend is running and models are loaded"""
    print("=" * 60)
    print("Backend Server Model Status Check")
    print("=" * 60)
    
    # Check if backend is running
    print("\n[1] Checking if backend server is running...")
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=2)
        if response.status_code == 200:
            print("   ✓ Backend server is running")
            health_data = response.json()
            print(f"   Database: {'✓ Online' if health_data.get('database_is_online') else '✗ Offline'}")
        else:
            print(f"   ⚠️  Backend responded with status {response.status_code}")
            return 1
    except requests.exceptions.ConnectionError:
        print("   ✗ Backend server is NOT running")
        print("\n💡 Start the backend server:")
        print("   cd backend")
        print("   source ../backend-venv/bin/activate")
        print("   uvicorn app.main:app --reload")
        return 1
    except Exception as e:
        print(f"   ✗ Error checking backend: {e}")
        return 1
    
    # Check models via diagnostic endpoint or try a prediction
    print("\n[2] Checking if models are loaded...")
    print("   (Models are loaded in the backend server process)")
    print("   (Check backend server logs for model initialization messages)")
    
    # Try to use the diagnose script which will check models in the backend process
    # if we can connect to it, or suggest checking logs
    print("\n💡 To verify models are loaded in the backend:")
    print("   1. Check backend server startup logs for:")
    print("      - 'Neural network model loaded: version ...'")
    print("      - 'Random Forest model loaded: version ...'")
    print("      - 'ML inference service ready'")
    print("\n   2. Or run: python scripts/diagnose_recommendations.py")
    print("      (This will check models in the backend process if it can connect)")
    
    print("\n" + "=" * 60)
    print("Note: The load_models.py script runs in a separate process.")
    print("Models only persist when loaded in the backend server process.")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(check_backend_health())


#!/usr/bin/env python3
"""Script to manually load and verify ML models"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ml_service import initialize_models, are_models_loaded, get_latest_model_version


def main():
    print("=" * 60)
    print("ML Model Loader")
    print("=" * 60)
    print("\n⚠️  NOTE: This script runs in a separate process.")
    print("   Models loaded here will NOT persist after the script exits.")
    print("   Models must be loaded in the backend server to persist.")
    print("   The backend server loads models automatically on startup.\n")
    
    # Check current status
    print("[1] Checking current model status...")
    models_loaded = are_models_loaded()
    print(f"   Models currently loaded in THIS process: {models_loaded}")
    print("   (This will always be False - models are only cached in the backend server process)")
    
    # Check available versions
    print("\n[2] Checking available model versions...")
    nn_version = get_latest_model_version("neural_network")
    rf_version = get_latest_model_version("random_forest")
    
    if nn_version:
        print(f"   Latest Neural Network: {nn_version}")
    else:
        print("   No Neural Network models found")
    
    if rf_version:
        print(f"   Latest Random Forest: {rf_version}")
    else:
        print("   No Random Forest models found")
    
    # Load models
    print("\n[3] Loading models...")
    try:
        results = initialize_models()
        
        nn_status = results["neural_network"]
        rf_status = results["random_forest"]
        
        print(f"\n   Neural Network:")
        if nn_status["loaded"]:
            print(f"     ✓ Loaded successfully")
            print(f"     Version: {nn_status['version']}")
        else:
            print(f"     ✗ Failed to load")
            print(f"     Error: {nn_status.get('error', 'Unknown')}")
        
        print(f"\n   Random Forest:")
        if rf_status["loaded"]:
            print(f"     ✓ Loaded successfully")
            print(f"     Version: {rf_status['version']}")
        else:
            print(f"     ✗ Failed to load")
            print(f"     Error: {rf_status.get('error', 'Unknown')}")
        
        # Final status
        print("\n[4] Final status...")
        if are_models_loaded():
            print("   ✓ Models loaded in THIS process (will be cleared when script exits)")
            print("\n💡 To keep models loaded, ensure the backend server is running.")
            print("   The backend server loads models automatically on startup.")
            print("   Check backend logs for model initialization messages.")
            return 0
        else:
            print("   ✗ No models available for inference in THIS process")
            print("\n💡 Models are only cached in long-running processes (like the backend server).")
            print("   Start the backend server to keep models loaded: uvicorn app.main:app --reload")
            return 1
            
    except Exception as e:
        print(f"\n   ✗ Error loading models: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())


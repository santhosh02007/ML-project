import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

import pytest

if __name__ == "__main__":
    print("[*] Running Fake Job Detector Test Suite...")
    exit_code = pytest.main([
        "tests",
        "-v",
        "-s",
        "--tb=short"
    ])
    sys.exit(exit_code)

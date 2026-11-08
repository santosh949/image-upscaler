import os
import sys
import pytest
from pathlib import Path

# Ensure root directory is on PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.config import settings
from backend.app.database import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_database(tmp_path_factory):
    """
    Configures an isolated SQLite database and job dispatcher for the test session.
    Prevents tests from clearing or modifying the production storage/aether.db.
    """
    test_db_dir = tmp_path_factory.mktemp("test_db")
    test_db_path = str(test_db_dir / "test_aether.db")
    
    # Override settings and environment to point to isolated test DB
    os.environ["DATABASE_PATH"] = test_db_path
    settings.DATABASE_PATH = test_db_path
    init_db()

    from backend.app.services.job_manager import job_manager
    job_manager.start_dispatcher()

    yield test_db_path

    job_manager.stop_dispatcher()

def is_ncnn_installed() -> bool:
    if os.environ.get("SIMULATE_CLEAN_CLONE") == "1":
        return False
    bin_name = "realesrgan-ncnn-vulkan.exe" if sys.platform.startswith("win") else "realesrgan-ncnn-vulkan"
    exe_path = ROOT_DIR / "tools" / "realesrgan-ncnn-vulkan" / bin_name
    return exe_path.is_file()

def is_frontend_built() -> bool:
    if os.environ.get("SIMULATE_CLEAN_CLONE") == "1":
        return False
    dist_dir = ROOT_DIR / "frontend" / "dist"
    return dist_dir.is_dir() and (dist_dir / "index.html").is_file()

def are_weights_installed() -> bool:
    if os.environ.get("SIMULATE_CLEAN_CLONE") == "1":
        return False
    models_dir = ROOT_DIR / "tools" / "realesrgan-ncnn-vulkan" / "models"
    return (models_dir / "realesrgan-x4plus.bin").is_file()

@pytest.fixture
def requires_ncnn():
    if not is_ncnn_installed():
        pytest.skip("Real-ESRGAN NCNN Vulkan binary not present. Run scripts/setup_environment.py to install.")

@pytest.fixture
def requires_weights():
    if not is_ncnn_installed():
        pytest.skip("Real-ESRGAN NCNN Vulkan binary not present. Run scripts/setup_environment.py to install.")
    if not are_weights_installed():
        pytest.skip("Model weights not present. Run scripts/setup_environment.py to download.")

@pytest.fixture
def requires_frontend():
    if not is_frontend_built():
        pytest.skip("Frontend dist not built. Run npm --prefix frontend run build.")

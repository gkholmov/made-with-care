"""Optional pytest support (the suite also runs under stdlib `python -m unittest`).
Sets path + env before importing ph. Tests themselves use tests/_bootstrap.Base."""
import os
import sys
import pathlib
import tempfile

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.gettempdir()}/ph_pytest.db")
os.environ.setdefault("LLM_PROVIDER", "stub")
os.environ.setdefault("STT_PROVIDER", "stub")
os.environ.setdefault("TTS_PROVIDER", "stub")
os.environ.setdefault("EMAIL_PROVIDER", "stub")

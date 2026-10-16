"""Vercel entry point for the ADJUST API.

Vercel runs this file as a Python function. It only puts the backend package
on the import path and re-exports the existing FastAPI app, so the API code in
backend/adjust_api stays unchanged and still runs locally via scripts/start.py.
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from adjust_api.main import app  # noqa: E402  (path must be set first)

__all__ = ["app"]

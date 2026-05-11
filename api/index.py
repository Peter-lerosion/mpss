"""
Vercel serverless entry point for MPSS FastAPI backend.
Vercel's Python runtime looks for an `app` variable in this file.
"""
import sys
import os

# Add project root to sys.path so `backend.main` can be imported
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from backend.main import app  # noqa: F401 – re-exported for Vercel

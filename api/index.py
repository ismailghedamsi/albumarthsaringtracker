"""
Vercel serverless function entry point for Flask app
"""
import sys
import os
from pathlib import Path

# Add parent directory to path so we can import app modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Change to parent directory so relative paths work
os.chdir(parent_dir)

# Import the Flask app
from app import app

# Vercel Python runtime expects the Flask app to be exported directly
# The @vercel/python builder will automatically wrap it


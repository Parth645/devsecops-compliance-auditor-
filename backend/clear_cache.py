#!/usr/bin/env python3
"""
Clear Python cache files to ensure fresh imports
"""

import os
import shutil
from pathlib import Path

def clear_pycache():
    """Remove all __pycache__ directories and .pyc files"""
    
    backend_dir = Path(__file__).parent
    
    print("Clearing Python cache files...")
    
    removed_dirs = 0
    removed_files = 0
    
    # Remove __pycache__ directories
    for pycache_dir in backend_dir.rglob("__pycache__"):
        try:
            shutil.rmtree(pycache_dir)
            removed_dirs += 1
            print(f"  Removed: {pycache_dir}")
        except Exception as e:
            print(f"  Failed to remove {pycache_dir}: {e}")
    
    # Remove .pyc files
    for pyc_file in backend_dir.rglob("*.pyc"):
        try:
            pyc_file.unlink()
            removed_files += 1
            print(f"  Removed: {pyc_file}")
        except Exception as e:
            print(f"  Failed to remove {pyc_file}: {e}")
    
    print(f"\n✓ Removed {removed_dirs} __pycache__ directories")
    print(f"✓ Removed {removed_files} .pyc files")
    print("\nCache cleared! Please restart the server.")

if __name__ == "__main__":
    clear_pycache()

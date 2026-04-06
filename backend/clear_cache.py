#!/usr/bin/env python
"""
Clear all Python caches in the project
Resolves stale bytecode issues
"""

import os
import shutil
from pathlib import Path

def clear_pycache():
    """Remove all __pycache__ directories"""
    count = 0
    for pycache_dir in Path('.').rglob('__pycache__'):
        try:
            shutil.rmtree(pycache_dir)
            print(f"Removed: {pycache_dir}")
            count += 1
        except Exception as e:
            print(f"Error removing {pycache_dir}: {e}")
    return count

def clear_pyc_files():
    """Remove all .pyc files"""
    count = 0
    for pyc_file in Path('.').rglob('*.pyc'):
        try:
            pyc_file.unlink()
            print(f"Removed: {pyc_file}")
            count += 1
        except Exception as e:
            print(f"Error removing {pyc_file}: {e}")
    return count

def clear_pyo_files():
    """Remove all .pyo files"""
    count = 0
    for pyo_file in Path('.').rglob('*.pyo'):
        try:
            pyo_file.unlink()
            print(f"Removed: {pyo_file}")
            count += 1
        except Exception as e:
            print(f"Error removing {pyo_file}: {e}")
    return count

def main():
    print("=" * 60)
    print("CLEARING PYTHON CACHES")
    print("=" * 60)
    print()
    
    print("Clearing __pycache__ directories...")
    pycache_count = clear_pycache()
    print(f"  Removed {pycache_count} __pycache__ directories")
    print()
    
    print("Clearing .pyc files...")
    pyc_count = clear_pyc_files()
    print(f"  Removed {pyc_count} .pyc files")
    print()
    
    print("Clearing .pyo files...")
    pyo_count = clear_pyo_files()
    print(f"  Removed {pyo_count} .pyo files")
    print()
    
    total = pycache_count + pyc_count + pyo_count
    print("=" * 60)
    print(f"✓ Total items cleared: {total}")
    print("=" * 60)
    print()
    print("NEXT STEPS:")
    print("1. Stop any running servers (Ctrl+C)")
    print("2. Restart the application: python main.py")
    print("3. The application will recompile with fresh bytecode")
    print()

if __name__ == "__main__":
    main()

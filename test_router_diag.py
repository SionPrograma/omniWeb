import sys
import os
import importlib
from fastapi import APIRouter

# Mock what main.py does
sys.path.append(os.getcwd())

def test_import(slug, path):
    try:
        print(f"Testing {slug} at {path}...")
        module = importlib.import_module(path)
        if hasattr(module, "router"):
            obj = getattr(module, "router")
            if isinstance(obj, APIRouter):
                print(f"SUCCESS: Found APIRouter in {path}")
            else:
                print(f"FAIL: {path}.router is not APIRouter")
        else:
            print(f"FAIL: {path} has no 'router' attribute")
    except Exception as e:
        print(f"ERROR: Failed to import {path}: {e}")

if __name__ == "__main__":
    test_import("reparto", "chips.chip-reparto.core.router")
    test_import("safety_test", "chips.chip-safety_test.core.router")
    test_import("safety_test", "chips.chip-safety_test.backend.router")

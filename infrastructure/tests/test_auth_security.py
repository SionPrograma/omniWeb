
import pytest
import sys
import os
from datetime import datetime

# Add root to sys.path
sys.path.append(os.getcwd())

from backend.core.auth import get_password_hash, verify_password, get_current_user
from backend.core.config import settings

def test_password_hashing():
    password = "secret-password"
    hashed = get_password_hash(password)
    
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)

def test_legacy_hash_fallback():
    # Test 'admin-hash' fallback
    assert verify_password("admin", "admin-hash")
    
    # Test 'hash_' prefix fallback
    assert verify_password("test", "hash_test")

def test_admin_token_validation():
    # Test against default token
    token = settings.ADMIN_TOKEN
    user = get_current_user(token)
    
    assert user.username == "admin"
    assert user.role == "admin"

def test_invalid_token_rejection():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        get_current_user("invalid-token")
    assert exc.value.status_code == 401

if __name__ == "__main__":
    # Manual execution if pytest not available
    try:
        test_password_hashing()
        print("PASS: test_password_hashing")
        test_legacy_hash_fallback()
        print("PASS: test_legacy_hash_fallback")
        test_admin_token_validation()
        print("PASS: test_admin_token_validation")
        test_invalid_token_rejection()
        print("PASS: test_invalid_token_rejection")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

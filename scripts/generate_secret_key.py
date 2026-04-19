#!/usr/bin/env python
"""
Generate a secure Django secret key.
Usage: python scripts/generate_secret_key.py
"""
import secrets

def generate_secret_key():
    """Generate a cryptographically secure random secret key."""
    return secrets.token_urlsafe(50)

if __name__ == "__main__":
    key = generate_secret_key()
    print(f"Generated secret key:")
    print(key)
    print(f"\nAdd this to your .env file:")
    print(f"DJANGO_SECRET_KEY={key}")

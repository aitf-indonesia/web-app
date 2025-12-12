#!/usr/bin/env python3
"""
Test login endpoint directly
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set environment
os.environ.setdefault("DB_URL", "postgresql://postgres:root@localhost:5432/prd")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

print("Testing login endpoint...")
print("="*50)

response = client.post(
    "/api/auth/login",
    json={"username": "admin", "password": "secret"}
)

print(f"Status Code: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"Response: {response.text[:500]}")

if response.status_code == 200:
    print("\n✅ Login successful!")
    data = response.json()
    print(f"Token: {data.get('access_token', '')[:50]}...")
    print(f"User: {data.get('user', {}).get('username')}")
else:
    print(f"\n❌ Login failed!")
    print(f"Error: {response.text}")

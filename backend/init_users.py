#!/usr/bin/env python3
"""
Initialize users table with test accounts
Password for all users: "secret"
"""
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from utils.auth import get_password_hash

# Get database URL from environment
DB_URL = os.getenv("DB_URL", "postgresql://postgres:root@localhost:5432/prd")

print(f"Connecting to database: {DB_URL}")
engine = create_engine(DB_URL)

# Generate password hash for "secret"
password_hash = get_password_hash("secret")
print(f"Generated password hash for 'secret': {password_hash[:50]}...")

# Create users table and insert test users
with engine.begin() as conn:
    # Create users table
    print("Creating users table...")
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20),
            role VARCHAR(20) NOT NULL CHECK (role IN ('verifikator', 'administrator')),
            created_at TIMESTAMPTZ DEFAULT now(),
            last_login TIMESTAMPTZ,
            dark_mode BOOLEAN DEFAULT FALSE,
            compact_mode BOOLEAN DEFAULT FALSE,
            generator_keywords TEXT DEFAULT ''
        )
    """))
    
    # Create index on username
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)
    """))
    
    print("Inserting test users...")
    # Insert test users
    conn.execute(text("""
        INSERT INTO users (username, password_hash, full_name, email, phone, role, created_at)
        VALUES 
            ('admin', :password_hash, 'Administrator', 'admin@example.com', '081234567890', 'administrator', now()),
            ('verif1', :password_hash, 'Verifikator Satu', 'verif1@example.com', '081234567891', 'verifikator', now()),
            ('verif2', :password_hash, 'Verifikator Dua', 'verif2@example.com', '081234567892', 'verifikator', now()),
            ('verif3', :password_hash, 'Verifikator Tiga', NULL, NULL, 'verifikator', now())
        ON CONFLICT (username) DO UPDATE SET
            password_hash = EXCLUDED.password_hash,
            full_name = EXCLUDED.full_name
    """), {"password_hash": password_hash})
    
    # Verify users created
    result = conn.execute(text("SELECT username, full_name, role FROM users ORDER BY id"))
    users = result.fetchall()
    
    print("\n✅ Users table initialized successfully!")
    print(f"Total users: {len(users)}")
    print("\nTest accounts (all with password 'secret'):")
    for user in users:
        print(f"  - {user[0]:10s} | {user[1]:25s} | {user[2]}")
    
    print("\n✅ Database initialization complete!")

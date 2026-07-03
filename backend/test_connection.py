#!/usr/bin/env python3
"""
Simple connection test using psycopg3 (sync) to diagnose connection issues.
"""

import os
import sys
from urllib.parse import quote_plus, urlparse
from dotenv import load_dotenv

# Load env
load_dotenv()

# Get connection string
db_url = os.getenv("DATABASE_URL", "")

if not db_url:
    print("❌ DATABASE_URL not set in .env")
    sys.exit(1)

print(f"Testing connection to: {db_url[:50]}...")

# Parse the URL
try:
    parsed = urlparse(db_url)
    print(f"✓ Parsed URL successfully")
    print(f"  Scheme: {parsed.scheme}")
    print(f"  Host: {parsed.hostname}")
    print(f"  Port: {parsed.port}")
    print(f"  Database: {parsed.path.lstrip('/')}")
except Exception as e:
    print(f"❌ Failed to parse URL: {e}")
    sys.exit(1)

# Try with psycopg3 (sync)
try:
    import psycopg
    print("\n🔗 Testing with psycopg3 (sync)...")
    
    conn = psycopg.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        dbname=parsed.path.lstrip('/') or "postgres",
        user=parsed.username,
        password=parsed.password,
        sslmode="require",
        connect_timeout=10,
    )
    
    print("✅ Connected successfully!")
    
    # Test query
    with conn.cursor() as cur:
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"✓ PostgreSQL: {version.split(',')[0]}")
    
    conn.close()
    print("✅ Connection test passed!")
    
except ImportError:
    print("⚠️  psycopg3 not installed, skipping sync test")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

print("\n✅ All diagnostics passed!")

#!/usr/bin/env python3
"""
Database setup script for Perfect Assistant.
Initializes tables and verifies connection.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


async def setup_database():
    """Initialize database and create all tables."""
    from database import init_db, engine, Base
    from sqlalchemy import inspect, text
    
    print("🗄️  Perfect Assistant — Database Setup")
    print("=" * 50)
    
    try:
        # Initialize tables
        print("\n📦 Creating database tables...")
        await init_db()
        print("✅ Tables created successfully")
        
        # Verify tables
        print("\n🔍 Verifying tables...")
        async with engine.begin() as conn:
            if "sqlite" in str(engine.url):
                # SQLite
                result = await conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ))
                tables = [row[0] for row in result]
            else:
                # PostgreSQL
                result = await conn.execute(text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                ))
                tables = [row[0] for row in result]
        
        if tables:
            print(f"✅ Found {len(tables)} tables:")
            for table in sorted(tables):
                print(f"   - {table}")
        else:
            print("❌ No tables found!")
            return False
        
        # Show connection info
        print("\n🔗 Connection Information:")
        db_url = str(engine.url)
        # Hide password
        if "@" in db_url:
            parts = db_url.split("@")
            db_url = parts[0][:20] + "***@" + parts[1]
        print(f"   Database: {db_url}")
        
        # Show migration files
        print("\n📄 Migration Files:")
        migrations_dir = Path(__file__).parent / "migrations"
        if migrations_dir.exists():
            for file in sorted(migrations_dir.glob("*.sql")):
                size = file.stat().st_size
                print(f"   - {file.name} ({size} bytes)")
        
        print("\n" + "=" * 50)
        print("✅ Database setup complete!")
        print("\nNext steps:")
        print("1. Start backend: uvicorn main:app --reload")
        print("2. Check health: curl http://localhost:8000/health")
        print("3. View docs: http://localhost:8000/docs")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run setup
    success = asyncio.run(setup_database())
    sys.exit(0 if success else 1)

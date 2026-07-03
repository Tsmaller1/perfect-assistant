#!/usr/bin/env python3
"""
Setup Supabase database for Perfect Assistant.
Connects to Supabase PostgreSQL and runs migrations.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


async def setup_supabase():
    """Initialize Supabase database with schema."""
    from sqlalchemy import text, inspect
    from database import engine, init_db
    
    print("🗄️  Perfect Assistant — Supabase Setup")
    print("=" * 60)
    
    try:
        # Test connection
        print("\n🔗 Testing Supabase connection...")
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            await conn.execute(text("SELECT current_database()"))
        print("✅ Connected to Supabase PostgreSQL")
        
        # Initialize tables
        print("\n📦 Creating database tables...")
        await init_db()
        print("✅ Tables created successfully")
        
        # Verify tables
        print("\n🔍 Verifying tables...")
        async with engine.begin() as conn:
            result = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            ))
            tables = [row[0] for row in result]
        
        if tables:
            print(f"✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"   ✓ {table}")
        else:
            print("❌ No tables found!")
            return False
        
        # Show Supabase info
        print("\n📊 Supabase Information:")
        print(f"   URL: https://taaakkckfumdqqlvvnie.supabase.co")
        print(f"   Project Reference: taaakkckfumdqqlvvnie")
        print(f"   Database: postgres")
        
        # Get row counts
        print("\n📈 Table Row Counts:")
        async with engine.begin() as conn:
            for table in tables:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"   {table}: {count} rows")
        
        print("\n" + "=" * 60)
        print("✅ Supabase setup complete!")
        print("\nNext steps:")
        print("1. Update backend/.env with DATABASE_URL")
        print("2. Start backend: uvicorn main:app --reload")
        print("3. Check health: curl http://localhost:8000/health")
        print("4. View API docs: http://localhost:8000/docs")
        print("=" * 60)
        
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
    
    # Verify DATABASE_URL is set
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set in .env file")
        print("Please copy .env.example to .env and fill in the values")
        sys.exit(1)
    
    if "supabase" not in db_url.lower():
        print("⚠️  Warning: DATABASE_URL doesn't contain 'supabase'")
        print(f"   Using: {db_url[:50]}...")
    
    # Run setup
    success = asyncio.run(setup_supabase())
    sys.exit(0 if success else 1)

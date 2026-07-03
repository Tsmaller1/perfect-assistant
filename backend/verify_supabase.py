#!/usr/bin/env python3
"""
Quick verify Supabase connection without creating tables.
Useful for testing connection before full setup.
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def verify_connection():
    """Test Supabase connection."""
    from sqlalchemy import text
    from database import engine
    
    print("🔗 Testing Supabase Connection...")
    print("-" * 50)
    
    try:
        async with engine.begin() as conn:
            # Test basic connection
            result = await conn.execute(text("SELECT 1"))
            print("✅ Basic connection: OK")
            
            # Get database info
            result = await conn.execute(text("SELECT current_database(), current_user, version()"))
            db, user, version = result.fetchone()
            print(f"✅ Database: {db}")
            print(f"✅ User: {user}")
            print(f"✅ PostgreSQL: {version.split(' ')[1]}")
            
            # Check if tables exist
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            ))
            table_count = result.scalar()
            print(f"✅ Tables found: {table_count}")
            
            if table_count == 0:
                print("\n⚠️  No tables yet. Run:")
                print("   python setup_supabase.py")
            else:
                # List tables
                result = await conn.execute(text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' ORDER BY table_name"
                ))
                print("\n📊 Tables:")
                for table in result:
                    print(f"   ✓ {table[0]}")
        
        print("\n" + "=" * 50)
        print("✅ Supabase connection verified!")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set in .env")
        sys.exit(1)
    
    success = asyncio.run(verify_connection())
    sys.exit(0 if success else 1)

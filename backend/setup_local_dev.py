#!/usr/bin/env python3
"""
Local Development Setup Script - Phase 5
Sets up PostgreSQL database locally for development without Docker
"""

import subprocess
import sys
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def run_command(cmd, description):
    """Run shell command and report status"""
    print(f"\n📋 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False

def setup_local_postgres():
    """Setup PostgreSQL database locally"""
    print("\n" + "="*70)
    print("🐘 LOCAL POSTGRES SETUP (Phase 5 - Development)")
    print("="*70)
    
    # Database credentials
    DB_HOST = "localhost"
    DB_PORT = 5432
    DB_USER = "postgres"
    DB_PASSWORD = "postgres"
    DB_NAME = "pine_sales_ai"
    
    try:
        # Connect to PostgreSQL default database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}';")
        if not cursor.fetchone():
            print(f"\n📝 Creating database '{DB_NAME}'...")
            cursor.execute(f"CREATE DATABASE {DB_NAME};")
            print(f"✅ Database '{DB_NAME}' created")
        else:
            print(f"✅ Database '{DB_NAME}' already exists")
        
        cursor.close()
        conn.close()
        
        # Connect to new database and run migrations
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        # Run migration files
        migration_dir = "migrations"
        if not os.path.exists(migration_dir):
            print(f"❌ Migration directory '{migration_dir}' not found")
            return False
        
        # Read and execute migrations in order
        migration_files = sorted([f for f in os.listdir(migration_dir) if f.endswith('.sql') and 'postgresql' in f or 'initial' in f])
        
        for migration_file in migration_files:
            if 'sqlite' in migration_file:
                continue  # Skip SQLite-specific migrations
            
            filepath = os.path.join(migration_dir, migration_file)
            print(f"\n📄 Running migration: {migration_file}")
            
            with open(filepath, 'r') as f:
                sql = f.read()
                cursor.execute(sql)
                conn.commit()
                print(f"✅ {migration_file} - Applied")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print("✅ LOCAL POSTGRES SETUP COMPLETE")
        print("="*70)
        print(f"\n📊 Database Connection Details:")
        print(f"  Host: {DB_HOST}:{DB_PORT}")
        print(f"  Database: {DB_NAME}")
        print(f"  User: {DB_USER}")
        print(f"\n💡 Update .env:")
        print(f"  DATABASE_URL=postgresql+asyncpg://{DB_USER}:postgres@localhost:5432/{DB_NAME}")
        print(f"\n🚀 Start backend: python -m uvicorn main:app --reload")
        print("="*70 + "\n")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ PostgreSQL Connection Failed")
        print(f"Error: {e}")
        print(f"\n💡 Make sure PostgreSQL is running:")
        print(f"  macOS: brew services start postgresql")
        print(f"  Linux: sudo systemctl start postgresql")
        print(f"  Windows: Start PostgreSQL from Services")
        return False
    except Exception as e:
        print(f"\n❌ Setup Failed: {e}")
        return False

if __name__ == "__main__":
    success = setup_local_postgres()
    sys.exit(0 if success else 1)

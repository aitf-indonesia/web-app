"""
Script to update crawling_data table schema.
Adds domain and og_metadata columns if they don't exist.
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DB_URL", "postgresql://postgres:root@localhost:5432/prd")
engine = create_engine(DATABASE_URL)

def update_schema():
    """Update crawling_data table schema."""
    try:
        with engine.begin() as conn:
            print("Checking and updating crawling_data table schema...")
            
            # Add domain column if it doesn't exist
            print("  Adding domain column...")
            conn.execute(text("""
                ALTER TABLE crawling_data 
                ADD COLUMN IF NOT EXISTS domain VARCHAR(255)
            """))
            print("  ✓ domain column added/verified")
            
            # Add og_metadata column if it doesn't exist
            print("  Adding og_metadata column...")
            conn.execute(text("""
                ALTER TABLE crawling_data 
                ADD COLUMN IF NOT EXISTS og_metadata JSONB
            """))
            print("  ✓ og_metadata column added/verified")
            
            # Remove keywords column if it exists (old schema)
            print("  Removing keywords column (if exists)...")
            conn.execute(text("""
                ALTER TABLE crawling_data 
                DROP COLUMN IF EXISTS keywords
            """))
            print("  ✓ keywords column removed (if existed)")
            
        print("\n✅ Schema update completed successfully!")
        print("Database is now ready for crawler operations.")
        
    except Exception as e:
        print(f"\n❌ Error updating schema: {str(e)}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("UPDATE CRAWLING_DATA SCHEMA")
    print("=" * 60)
    print("\nThis will update the crawling_data table to:")
    print("  - Add 'domain' column (VARCHAR 255)")
    print("  - Add 'og_metadata' column (JSONB)")
    print("  - Remove 'keywords' column (deprecated)")
    print("=" * 60)
    
    update_schema()

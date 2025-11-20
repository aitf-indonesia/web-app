"""
Script to verify crawling data in database.
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import json

load_dotenv()

DATABASE_URL = os.getenv("DB_URL", "postgresql://postgres:root@localhost:5432/prd")
engine = create_engine(DATABASE_URL)

def verify_data():
    """Check crawling data in database."""
    try:
        with engine.begin() as conn:
            # Count total records
            result = conn.execute(text("SELECT COUNT(*) FROM crawling_data"))
            total = result.scalar()
            print(f"Total records in crawling_data: {total}")
            
            if total > 0:
                # Show latest 5 records
                print("\nLatest 5 records:")
                print("=" * 80)
                result = conn.execute(text("""
                    SELECT id_crawling, url, title, domain, 
                           CASE WHEN og_metadata IS NOT NULL THEN 'Yes' ELSE 'No' END as has_og,
                           image_path, status, date_crawled
                    FROM crawling_data 
                    ORDER BY id_crawling DESC 
                    LIMIT 5
                """))
                
                for row in result:
                    print(f"\nID: {row[0]}")
                    print(f"  URL: {row[1]}")
                    print(f"  Title: {row[2]}")
                    print(f"  Domain: {row[3]}")
                    print(f"  Has OG Metadata: {row[4]}")
                    print(f"  Image Path: {row[5]}")
                    print(f"  Status: {row[6]}")
                    print(f"  Date: {row[7]}")
                
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("=" * 80)
    print("VERIFY CRAWLING DATA")
    print("=" * 80)
    verify_data()

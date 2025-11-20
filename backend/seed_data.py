import os
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
from urllib.parse import urlparse

DB_URL = os.getenv("DB_URL", "postgresql://postgres:root@localhost:5432/prd")
engine = create_engine(DB_URL)

csv_path = Path("public/data/links.csv")
if not csv_path.exists():
    raise SystemExit(f"CSV not found: {csv_path}")

df = pd.read_csv(csv_path)
df = df.rename(columns={'URL': 'url', 'Url': 'url', 'link': 'url', 'Title': 'title', 'Paragraph': 'description'})

print("Columns in dataframe:", df.columns.tolist())
print(f"Total rows: {len(df)}")

df["url"] = df["url"].astype(str).fillna("").str.strip()
df = df[df["url"] != ""].drop_duplicates(subset=["url"])

print(f"After cleaning: {len(df)} rows")

with engine.begin() as conn:
    # First, insert into crawling_data
    for idx, row in df.iterrows():
        url = row.get("url", "")
        title = row.get("title", "")[:255] if pd.notna(row.get("title")) else ""
        description = row.get("description", "") if pd.notna(row.get("description")) else ""
        
        # Extract domain from URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc if parsed_url.netloc else None
        
        # Initialize og_metadata as None (or an empty JSON string if preferred)
        og_metadata = None # This would typically be populated by a crawler
        
        status = 'processed' # Maintain original status
        
        # Insert into crawling_data
        result = conn.execute(text("""
            INSERT INTO crawling_data (url, title, description, domain, og_metadata, status)
            VALUES (:url, :title, :description, :domain, :og_metadata, :status)
            RETURNING id_crawling
        """), {"url": url, "title": title, "description": description, "domain": domain, "og_metadata": og_metadata, "status": status})
        
        id_crawling = result.fetchone()[0]
        
        # Insert into results with the crawling_data id
        conn.execute(text("""
            INSERT INTO results (
                id_crawling, url, keywords, reasoning_text, 
                label_final, final_confidence, status, flagged
            )
            VALUES (
                :id_crawling, :url, 'judi online', 
                'Situs terdeteksi mengandung konten perjudian online berdasarkan analisis URL dan konten.',
                true, 0.85, 'unverified', false
            )
        """), {"id_crawling": id_crawling, "url": url})
        
        if (idx + 1) % 50 == 0:
            print(f"Processed {idx + 1} rows...")

print(f"✅ Import complete — {len(df)} records inserted into database")

#!/usr/bin/env python3
"""
Script untuk MEMERIKSA data duplikat dari semua tabel di database (DRY RUN)
Tidak menghapus data, hanya menampilkan laporan duplikat
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'prd'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# Definisi tabel (sama seperti remove_duplicates.py)
TABLE_DEFINITIONS = {
    'audit_log': {
        'pk': 'id',
        'unique_cols': ['id_result', 'action', 'username', 'details'],
        'exclude_cols': ['timestamp']
    },
    'chat_history': {
        'pk': 'id',
        'unique_cols': ['username', 'id_domain', 'role', 'message'],
        'exclude_cols': ['created_at']
    },
    'domain_notes': {
        'pk': 'id',
        'unique_cols': ['id_domain', 'note_text', 'created_by'],
        'exclude_cols': ['created_at', 'updated_at']
    },
    'feedback': {
        'pk': 'id_feedback',
        'unique_cols': ['messages', 'sender'],
        'exclude_cols': ['waktu_pengiriman']
    },
    'generated_domains': {
        'pk': 'id_domain',
        'unique_cols': ['url', 'title', 'domain', 'image_base64', 'is_dummy'],
        'exclude_cols': ['date_generated']
    },
    'generator_settings': {
        'pk': 'id',
        'unique_cols': ['setting_key', 'setting_value'],
        'exclude_cols': ['updated_at', 'updated_by']
    },
    'history_log': {
        'pk': 'id',
        'unique_cols': ['id_result', 'text'],
        'exclude_cols': ['time']
    },
    'object_detection': {
        'pk': 'id_detection',
        'unique_cols': ['id_domain', 'label', 'confidence_score', 'image_detected_base64', 
                       'bounding_box', 'ocr', 'model_version'],
        'exclude_cols': ['processed_at']
    },
    'reasoning': {
        'pk': 'id_reasoning',
        'unique_cols': ['id_domain', 'label', 'context', 'confidence_score', 'model_version'],
        'exclude_cols': ['processed_at']
    },
    'results': {
        'pk': 'id_results',
        'unique_cols': ['id_domain', 'id_reasoning', 'id_detection', 'url', 'keywords', 
                       'reasoning_text', 'image_final_path', 'label_final', 'final_confidence',
                       'status', 'flagged', 'is_manual'],
        'exclude_cols': ['created_at', 'modified_at', 'updated_at', 'verified_at', 
                        'modified_by', 'created_by', 'verified_by']
    },
    'users': {
        'pk': 'id',
        'unique_cols': ['username', 'email'],
        'exclude_cols': ['password_hash', 'last_login', 'created_at', 'dark_mode', 
                        'compact_mode', 'generator_keywords']
    },
    'announcements': {
        'pk': 'id',
        'unique_cols': ['title', 'content', 'category', 'created_by'],
        'exclude_cols': ['created_at', 'updated_at']
    }
}


def get_connection():
    """Membuat koneksi ke database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        raise


def check_duplicates_in_table(conn, table_name, table_def):
    """
    Memeriksa duplikat dari tabel tertentu tanpa menghapus
    
    Args:
        conn: Database connection
        table_name: Nama tabel
        table_def: Definisi tabel (pk, unique_cols, exclude_cols)
    
    Returns:
        dict: Informasi duplikat
    """
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    pk = table_def['pk']
    unique_cols = table_def['unique_cols']
    
    # Buat daftar kolom untuk PARTITION BY
    partition_cols = ', '.join(unique_cols)
    
    # Query untuk menghitung total baris
    count_query = f"SELECT COUNT(*) as total FROM {table_name}"
    cursor.execute(count_query)
    total_rows = cursor.fetchone()['total']
    
    # Query untuk menemukan duplikat
    find_duplicates_query = f"""
        WITH duplicates AS (
            SELECT 
                {pk},
                ROW_NUMBER() OVER (
                    PARTITION BY {partition_cols}
                    ORDER BY {pk}
                ) as row_num
            FROM {table_name}
        )
        SELECT {pk}
        FROM duplicates
        WHERE row_num > 1
    """
    
    # Query untuk menghitung grup duplikat
    count_duplicate_groups_query = f"""
        WITH duplicate_groups AS (
            SELECT 
                {partition_cols},
                COUNT(*) as count
            FROM {table_name}
            GROUP BY {partition_cols}
            HAVING COUNT(*) > 1
        )
        SELECT COUNT(*) as groups FROM duplicate_groups
    """
    
    try:
        # Cari duplikat
        cursor.execute(find_duplicates_query)
        duplicate_ids = [row[pk] for row in cursor.fetchall()]
        
        # Hitung grup duplikat
        cursor.execute(count_duplicate_groups_query)
        duplicate_groups = cursor.fetchone()['groups']
        
        result = {
            'total_rows': total_rows,
            'duplicate_count': len(duplicate_ids),
            'duplicate_groups': duplicate_groups,
            'duplicate_ids': duplicate_ids[:10]  # Hanya simpan 10 pertama untuk preview
        }
        
        return result
        
    except Exception as e:
        print(f"  ❌ Error pada tabel '{table_name}': {e}")
        raise
    finally:
        cursor.close()


def main():
    """Main function"""
    print("=" * 80)
    print("LAPORAN PEMERIKSAAN DATA DUPLIKAT (DRY RUN)")
    print("=" * 80)
    print(f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {DB_CONFIG['database']} @ {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print("=" * 80)
    print()
    
    conn = None
    total_duplicates = 0
    tables_with_duplicates = []
    
    try:
        # Koneksi ke database
        print("📡 Menghubungkan ke database...")
        conn = get_connection()
        print("✓ Koneksi berhasil!")
        print()
        
        # Proses setiap tabel
        print(f"🔍 Memeriksa {len(TABLE_DEFINITIONS)} tabel...")
        print()
        
        for table_name, table_def in TABLE_DEFINITIONS.items():
            print(f"📋 Tabel: {table_name}")
            try:
                result = check_duplicates_in_table(conn, table_name, table_def)
                
                print(f"  Total baris: {result['total_rows']}")
                print(f"  Baris duplikat: {result['duplicate_count']}")
                print(f"  Grup duplikat: {result['duplicate_groups']}")
                
                if result['duplicate_count'] > 0:
                    total_duplicates += result['duplicate_count']
                    tables_with_duplicates.append({
                        'name': table_name,
                        'duplicates': result['duplicate_count'],
                        'groups': result['duplicate_groups']
                    })
                    print(f"  ⚠️  Contoh ID duplikat: {result['duplicate_ids']}")
                else:
                    print(f"  ✓ Tidak ada duplikat")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
            print()
        
        # Summary
        print("=" * 80)
        print("RINGKASAN")
        print("=" * 80)
        print(f"Total tabel diperiksa: {len(TABLE_DEFINITIONS)}")
        print(f"Tabel dengan duplikat: {len(tables_with_duplicates)}")
        print(f"Total baris duplikat: {total_duplicates}")
        print()
        
        if tables_with_duplicates:
            print("Detail tabel dengan duplikat:")
            for table in tables_with_duplicates:
                print(f"  - {table['name']}: {table['duplicates']} baris ({table['groups']} grup)")
            print()
            print("💡 Untuk menghapus duplikat, jalankan: python remove_duplicates.py")
        else:
            print("✅ Tidak ada duplikat ditemukan di database!")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        return 1
    
    finally:
        if conn:
            conn.close()
            print("🔌 Koneksi database ditutup.")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

#!/usr/bin/env python3
"""
Script untuk menghapus data duplikat dari semua tabel di database
Duplikat diidentifikasi berdasarkan semua kolom kecuali primary key dan timestamp
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

# Definisi tabel dan kolom untuk identifikasi duplikat
# Format: 'table_name': {
#     'pk': 'primary_key_column',
#     'unique_cols': ['kolom1', 'kolom2', ...],  # Kolom yang digunakan untuk identifikasi duplikat
#     'exclude_cols': ['timestamp_col1', ...]     # Kolom yang diabaikan (timestamp, dll)
# }

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
        'unique_cols': ['username', 'email'],  # Username dan email harus unik
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


def remove_duplicates_from_table(conn, table_name, table_def):
    """
    Menghapus duplikat dari tabel tertentu
    
    Args:
        conn: Database connection
        table_name: Nama tabel
        table_def: Definisi tabel (pk, unique_cols, exclude_cols)
    
    Returns:
        int: Jumlah baris yang dihapus
    """
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    pk = table_def['pk']
    unique_cols = table_def['unique_cols']
    
    # Buat query untuk menemukan duplikat
    # Strategi: Gunakan ROW_NUMBER() untuk memberi nomor pada setiap duplikat,
    # kemudian hapus semua kecuali yang pertama (row_num > 1)
    
    # Buat daftar kolom untuk PARTITION BY
    partition_cols = ', '.join(unique_cols)
    
    # Query untuk menemukan ID duplikat (semua kecuali yang pertama)
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
    
    try:
        # Cari duplikat
        cursor.execute(find_duplicates_query)
        duplicate_ids = [row[pk] for row in cursor.fetchall()]
        
        if not duplicate_ids:
            print(f"  ✓ Tidak ada duplikat ditemukan di tabel '{table_name}'")
            return 0
        
        # Hapus duplikat
        if isinstance(duplicate_ids[0], str):
            # Untuk string IDs (seperti id_detection)
            ids_str = "', '".join(str(id) for id in duplicate_ids)
            delete_query = f"DELETE FROM {table_name} WHERE {pk} IN ('{ids_str}')"
        else:
            # Untuk numeric IDs
            ids_str = ', '.join(str(id) for id in duplicate_ids)
            delete_query = f"DELETE FROM {table_name} WHERE {pk} IN ({ids_str})"
        
        cursor.execute(delete_query)
        deleted_count = cursor.rowcount
        
        print(f"  ✓ Berhasil menghapus {deleted_count} baris duplikat dari tabel '{table_name}'")
        return deleted_count
        
    except Exception as e:
        print(f"  ❌ Error pada tabel '{table_name}': {e}")
        raise
    finally:
        cursor.close()


def main():
    """Main function"""
    print("=" * 80)
    print("SCRIPT PENGHAPUSAN DATA DUPLIKAT")
    print("=" * 80)
    print(f"Waktu mulai: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {DB_CONFIG['database']} @ {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print("=" * 80)
    print()
    
    conn = None
    total_deleted = 0
    
    try:
        # Koneksi ke database
        print("📡 Menghubungkan ke database...")
        conn = get_connection()
        print("✓ Koneksi berhasil!")
        print()
        
        # Proses setiap tabel
        print(f"🔍 Memproses {len(TABLE_DEFINITIONS)} tabel...")
        print()
        
        for table_name, table_def in TABLE_DEFINITIONS.items():
            print(f"📋 Tabel: {table_name}")
            try:
                deleted = remove_duplicates_from_table(conn, table_name, table_def)
                total_deleted += deleted
                conn.commit()
            except Exception as e:
                print(f"  ⚠️  Rollback transaksi untuk tabel '{table_name}'")
                conn.rollback()
            print()
        
        # Summary
        print("=" * 80)
        print("RINGKASAN")
        print("=" * 80)
        print(f"Total baris duplikat yang dihapus: {total_deleted}")
        print(f"Waktu selesai: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        if total_deleted > 0:
            print()
            print("✅ Proses penghapusan duplikat selesai!")
        else:
            print()
            print("ℹ️  Tidak ada duplikat yang ditemukan di database.")
        
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        if conn:
            conn.rollback()
        return 1
    
    finally:
        if conn:
            conn.close()
            print("🔌 Koneksi database ditutup.")
    
    return 0


if __name__ == "__main__":
    import sys
    
    # Konfirmasi dari user
    print()
    print("⚠️  PERINGATAN: Script ini akan menghapus data duplikat dari SEMUA tabel!")
    print("⚠️  Pastikan Anda sudah membuat backup database sebelum melanjutkan.")
    print()
    
    response = input("Apakah Anda yakin ingin melanjutkan? (ketik 'YA' untuk melanjutkan): ")
    
    if response.strip().upper() != 'YA':
        print("❌ Dibatalkan oleh user.")
        sys.exit(0)
    
    print()
    sys.exit(main())

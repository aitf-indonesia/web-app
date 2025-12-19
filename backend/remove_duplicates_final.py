#!/usr/bin/env python3
"""
Script untuk MEMERIKSA dan MENGHAPUS data duplikat EXACT
Versi FINAL - Bekerja tanpa PRIMARY KEY constraint
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime
import sys

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

# Mapping tabel ke kolom ID-nya (karena tidak ada PK constraint)
TABLE_ID_COLUMNS = {
    'audit_log': 'id',
    'chat_history': 'id',
    'domain_notes': 'id',
    'feedback': 'id_feedback',
    'generated_domains': 'id_domain',
    'generator_settings': 'id',
    'history_log': 'id',
    'object_detection': 'id_detection',
    'reasoning': 'id_reasoning',
    'results': 'id_results',
    'users': 'id',
    'announcements': 'id'
}


def get_connection():
    """Membuat koneksi ke database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        raise


def get_table_columns(conn, table_name):
    """Mendapatkan semua kolom dari tabel"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """
    cursor.execute(query, (table_name,))
    columns = cursor.fetchall()
    cursor.close()
    return columns


def check_exact_duplicates(conn, table_name, id_column):
    """Memeriksa duplikat EXACT dari tabel"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Dapatkan semua kolom
    columns = get_table_columns(conn, table_name)
    all_cols = [col['column_name'] for col in columns]
    
    # Kolom untuk grouping (semua kolom kecuali ID)
    group_cols = [col for col in all_cols if col != id_column]
    
    if not group_cols:
        return {'total_rows': 0, 'duplicate_count': 0, 'unique_count': 0}
    
    group_cols_str = ', '.join(group_cols)
    
    try:
        # Hitung total baris
        cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
        total_rows = cursor.fetchone()['total']
        
        if total_rows == 0:
            return {'total_rows': 0, 'duplicate_count': 0, 'unique_count': 0}
        
        # Hitung baris unik (menggunakan DISTINCT ON)
        unique_query = f"""
            SELECT COUNT(*) as unique_count FROM (
                SELECT DISTINCT ON ({group_cols_str}) {id_column}
                FROM {table_name}
                ORDER BY {group_cols_str}, {id_column}
            ) as unique_rows
        """
        cursor.execute(unique_query)
        unique_count = cursor.fetchone()['unique_count']
        
        duplicate_count = total_rows - unique_count
        
        return {
            'total_rows': total_rows,
            'unique_count': unique_count,
            'duplicate_count': duplicate_count
        }
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {'total_rows': 0, 'duplicate_count': 0, 'unique_count': 0}
    finally:
        cursor.close()


def remove_exact_duplicates(conn, table_name, id_column):
    """Menghapus duplikat EXACT dari tabel"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Dapatkan semua kolom
    columns = get_table_columns(conn, table_name)
    all_cols = [col['column_name'] for col in columns]
    
    # Kolom untuk grouping (semua kolom kecuali ID)
    group_cols = [col for col in all_cols if col != id_column]
    
    if not group_cols:
        print(f"  ⚠️  Tabel '{table_name}' hanya memiliki ID column, dilewati")
        return 0
    
    group_cols_str = ', '.join(group_cols)
    
    # Query untuk menemukan ID yang HARUS DIPERTAHANKAN
    keep_ids_query = f"""
        SELECT DISTINCT ON ({group_cols_str}) {id_column}
        FROM {table_name}
        ORDER BY {group_cols_str}, {id_column}
    """
    
    try:
        # Dapatkan ID yang harus dipertahankan
        cursor.execute(keep_ids_query)
        keep_ids = [row[id_column] for row in cursor.fetchall()]
        
        if not keep_ids:
            print(f"  ✓ Tabel '{table_name}' kosong")
            return 0
        
        # Hitung total baris
        cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
        total_rows = cursor.fetchone()['total']
        
        # Jika jumlah ID yang dipertahankan sama dengan total baris, tidak ada duplikat
        if len(keep_ids) == total_rows:
            print(f"  ✓ Tidak ada duplikat di tabel '{table_name}'")
            return 0
        
        # Hapus semua baris KECUALI yang ada di keep_ids
        if isinstance(keep_ids[0], str):
            # Untuk string IDs - gunakan parameterized query untuk keamanan
            placeholders = ','.join(['%s'] * len(keep_ids))
            delete_query = f"DELETE FROM {table_name} WHERE {id_column} NOT IN ({placeholders})"
            cursor.execute(delete_query, keep_ids)
        else:
            # Untuk numeric IDs
            placeholders = ','.join(['%s'] * len(keep_ids))
            delete_query = f"DELETE FROM {table_name} WHERE {id_column} NOT IN ({placeholders})"
            cursor.execute(delete_query, keep_ids)
        
        deleted_count = cursor.rowcount
        
        if deleted_count > 0:
            print(f"  ✓ Menghapus {deleted_count} baris duplikat (tersisa {len(keep_ids)} baris unik)")
        
        return deleted_count
        
    except Exception as e:
        print(f"  ❌ Error pada tabel '{table_name}': {e}")
        raise
    finally:
        cursor.close()


def main_check():
    """Check mode - hanya memeriksa duplikat"""
    print("=" * 80)
    print("LAPORAN PEMERIKSAAN DATA DUPLIKAT EXACT")
    print("=" * 80)
    print(f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {DB_CONFIG['database']} @ {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print()
    print("ℹ️  Duplikat exact = baris dengan SEMUA kolom sama persis (termasuk NULL)")
    print("=" * 80)
    print()
    
    conn = None
    total_duplicates = 0
    tables_with_duplicates = []
    
    try:
        print("📡 Menghubungkan ke database...")
        conn = get_connection()
        print("✓ Koneksi berhasil!")
        print()
        
        print(f"🔍 Memeriksa {len(TABLE_ID_COLUMNS)} tabel...")
        print()
        
        for table_name, id_column in TABLE_ID_COLUMNS.items():
            print(f"📋 Tabel: {table_name}")
            result = check_exact_duplicates(conn, table_name, id_column)
            
            print(f"  Total baris: {result['total_rows']}")
            print(f"  Baris unik: {result['unique_count']}")
            print(f"  Baris duplikat: {result['duplicate_count']}")
            
            if result['duplicate_count'] > 0:
                total_duplicates += result['duplicate_count']
                tables_with_duplicates.append({
                    'name': table_name,
                    'total': result['total_rows'],
                    'unique': result['unique_count'],
                    'duplicates': result['duplicate_count']
                })
                print(f"  ⚠️  Ada {result['duplicate_count']} baris duplikat")
            else:
                print(f"  ✓ Tidak ada duplikat")
            print()
        
        # Summary
        print("=" * 80)
        print("RINGKASAN")
        print("=" * 80)
        print(f"Total tabel diperiksa: {len(TABLE_ID_COLUMNS)}")
        print(f"Tabel dengan duplikat: {len(tables_with_duplicates)}")
        print(f"Total baris duplikat: {total_duplicates}")
        print()
        
        if tables_with_duplicates:
            print("Detail tabel dengan duplikat:")
            for table in tables_with_duplicates:
                print(f"  - {table['name']}: {table['duplicates']} duplikat dari {table['total']} baris total")
            print()
            print("💡 Untuk menghapus duplikat, jalankan:")
            print("   docker exec -i prd_backend python3 remove_duplicates_final.py --remove")
        else:
            print("✅ Tidak ada duplikat exact ditemukan di database!")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        return 1
    
    finally:
        if conn:
            conn.close()
            print("🔌 Koneksi database ditutup.")
    
    return 0


def main_remove():
    """Remove mode - menghapus duplikat"""
    print("=" * 80)
    print("SCRIPT PENGHAPUSAN DATA DUPLIKAT EXACT")
    print("=" * 80)
    print(f"Waktu mulai: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {DB_CONFIG['database']} @ {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print()
    print("ℹ️  Script ini hanya menghapus baris yang SEMUA kolomnya sama persis")
    print("=" * 80)
    print()
    
    conn = None
    total_deleted = 0
    
    try:
        print("📡 Menghubungkan ke database...")
        conn = get_connection()
        print("✓ Koneksi berhasil!")
        print()
        
        print(f"🔍 Memproses {len(TABLE_ID_COLUMNS)} tabel...")
        print()
        
        for table_name, id_column in TABLE_ID_COLUMNS.items():
            print(f"📋 Tabel: {table_name}")
            try:
                deleted = remove_exact_duplicates(conn, table_name, id_column)
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
            print("ℹ️  Tidak ada duplikat exact yang ditemukan di database.")
        
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
    if len(sys.argv) > 1 and sys.argv[1] == '--remove':
        # Mode remove
        print()
        print("⚠️  PERINGATAN: Script ini akan menghapus data duplikat EXACT dari SEMUA tabel!")
        print("⚠️  Duplikat exact = baris dengan SEMUA kolom sama persis (termasuk NULL)")
        print("⚠️  Pastikan Anda sudah membuat backup database sebelum melanjutkan.")
        print()
        
        response = input("Apakah Anda yakin ingin melanjutkan? (ketik 'YA' untuk melanjutkan): ")
        
        if response.strip().upper() != 'YA':
            print("❌ Dibatalkan oleh user.")
            sys.exit(0)
        
        print()
        sys.exit(main_remove())
    else:
        # Mode check (default)
        sys.exit(main_check())

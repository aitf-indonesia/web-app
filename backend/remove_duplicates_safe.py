#!/usr/bin/env python3
"""
Script AMAN untuk menghapus data duplikat dari semua tabel di database
Hanya menghapus duplikat EXACT (semua kolom sama persis)
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


def get_primary_key(conn, table_name):
    """Mendapatkan primary key dari tabel"""
    cursor = conn.cursor()
    query = """
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = %s::regclass AND i.indisprimary
    """
    cursor.execute(query, (f'public.{table_name}',))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None


def remove_exact_duplicates(conn, table_name):
    """
    Menghapus duplikat EXACT dari tabel
    Duplikat exact = semua kolom (termasuk NULL) sama persis
    Hanya menyimpan 1 baris, menghapus sisanya
    """
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Dapatkan primary key
    pk = get_primary_key(conn, table_name)
    if not pk:
        print(f"  ⚠️  Tabel '{table_name}' tidak memiliki primary key, dilewati")
        return 0
    
    # Dapatkan semua kolom
    columns = get_table_columns(conn, table_name)
    all_cols = [col['column_name'] for col in columns]
    
    # Kolom untuk grouping (semua kolom kecuali PK)
    group_cols = [col for col in all_cols if col != pk]
    
    if not group_cols:
        print(f"  ⚠️  Tabel '{table_name}' hanya memiliki primary key, dilewati")
        return 0
    
    # Buat query untuk menemukan duplikat EXACT
    # Menggunakan DISTINCT ON untuk PostgreSQL
    # Strategi: Buat CTE dengan semua data, lalu hapus yang tidak ada di hasil DISTINCT ON
    
    group_cols_str = ', '.join(group_cols)
    all_cols_str = ', '.join(all_cols)
    
    # Query untuk menemukan ID yang HARUS DIPERTAHANKAN (yang pertama dari setiap grup duplikat)
    keep_ids_query = f"""
        SELECT DISTINCT ON ({group_cols_str}) {pk}
        FROM {table_name}
        ORDER BY {group_cols_str}, {pk}
    """
    
    try:
        # Dapatkan ID yang harus dipertahankan
        cursor.execute(keep_ids_query)
        keep_ids = [row[pk] for row in cursor.fetchall()]
        
        if not keep_ids:
            print(f"  ✓ Tabel '{table_name}' kosong")
            return 0
        
        # Hitung total baris
        cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
        total_rows = cursor.fetchone()['total']
        
        # Jika jumlah ID yang dipertahankan sama dengan total baris, tidak ada duplikat
        if len(keep_ids) == total_rows:
            print(f"  ✓ Tidak ada duplikat exact di tabel '{table_name}'")
            return 0
        
        # Hapus semua baris KECUALI yang ada di keep_ids
        if isinstance(keep_ids[0], str):
            # Untuk string IDs
            ids_str = "', '".join(str(id) for id in keep_ids)
            delete_query = f"DELETE FROM {table_name} WHERE {pk} NOT IN ('{ids_str}')"
        else:
            # Untuk numeric IDs
            ids_str = ', '.join(str(id) for id in keep_ids)
            delete_query = f"DELETE FROM {table_name} WHERE {pk} NOT IN ({ids_str})"
        
        cursor.execute(delete_query)
        deleted_count = cursor.rowcount
        
        if deleted_count > 0:
            print(f"  ✓ Menghapus {deleted_count} baris duplikat dari '{table_name}' (tersisa {len(keep_ids)} baris unik)")
        else:
            print(f"  ✓ Tidak ada duplikat di tabel '{table_name}'")
        
        return deleted_count
        
    except Exception as e:
        print(f"  ❌ Error pada tabel '{table_name}': {e}")
        raise
    finally:
        cursor.close()


def get_all_tables(conn):
    """Mendapatkan semua tabel di schema public"""
    cursor = conn.cursor()
    query = """
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY tablename
    """
    cursor.execute(query)
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables


def main():
    """Main function"""
    print("=" * 80)
    print("SCRIPT PENGHAPUSAN DATA DUPLIKAT EXACT (AMAN)")
    print("=" * 80)
    print(f"Waktu mulai: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {DB_CONFIG['database']} @ {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print()
    print("ℹ️  Script ini hanya menghapus baris yang SEMUA kolomnya sama persis")
    print("ℹ️  (termasuk nilai NULL)")
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
        
        # Dapatkan semua tabel
        tables = get_all_tables(conn)
        print(f"🔍 Memproses {len(tables)} tabel...")
        print()
        
        for table_name in tables:
            print(f"📋 Tabel: {table_name}")
            try:
                deleted = remove_exact_duplicates(conn, table_name)
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
    import sys
    
    # Konfirmasi dari user
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
    sys.exit(main())

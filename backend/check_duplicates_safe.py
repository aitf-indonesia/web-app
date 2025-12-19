#!/usr/bin/env python3
"""
Script untuk MEMERIKSA data duplikat EXACT (semua kolom sama)
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


def check_exact_duplicates(conn, table_name):
    """Memeriksa duplikat EXACT dari tabel"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Dapatkan primary key
    pk = get_primary_key(conn, table_name)
    if not pk:
        return {'total_rows': 0, 'duplicate_count': 0, 'unique_count': 0}
    
    # Dapatkan semua kolom
    columns = get_table_columns(conn, table_name)
    all_cols = [col['column_name'] for col in columns]
    
    # Kolom untuk grouping (semua kolom kecuali PK)
    group_cols = [col for col in all_cols if col != pk]
    
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
                SELECT DISTINCT ON ({group_cols_str}) {pk}
                FROM {table_name}
                ORDER BY {group_cols_str}, {pk}
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
        # Koneksi ke database
        print("📡 Menghubungkan ke database...")
        conn = get_connection()
        print("✓ Koneksi berhasil!")
        print()
        
        # Dapatkan semua tabel
        tables = get_all_tables(conn)
        print(f"🔍 Memeriksa {len(tables)} tabel...")
        print()
        
        for table_name in tables:
            print(f"📋 Tabel: {table_name}")
            result = check_exact_duplicates(conn, table_name)
            
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
        print(f"Total tabel diperiksa: {len(tables)}")
        print(f"Tabel dengan duplikat: {len(tables_with_duplicates)}")
        print(f"Total baris duplikat: {total_duplicates}")
        print()
        
        if tables_with_duplicates:
            print("Detail tabel dengan duplikat:")
            for table in tables_with_duplicates:
                print(f"  - {table['name']}: {table['duplicates']} duplikat dari {table['total']} baris total")
            print()
            print("💡 Untuk menghapus duplikat, jalankan:")
            print("   docker exec -i prd_backend python3 remove_duplicates_safe.py")
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


if __name__ == "__main__":
    import sys
    sys.exit(main())

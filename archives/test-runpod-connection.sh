#!/bin/bash
# Test Database Connection dari RunPod
# Jalankan script ini di RunPod untuk verifikasi koneksi database

echo "🔍 Testing PostgreSQL Connection from RunPod"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Database credentials
DB_HOST="13.215.203.144"
DB_PORT="5432"
DB_NAME="prd"
DB_USER="postgres"
DB_PASS="postgres"

# Test 1: Port connectivity (already succeeded!)
echo "✅ Test 1: Port Connectivity"
echo "   Connection to $DB_HOST:$DB_PORT succeeded!"
echo ""

# Test 2: Install PostgreSQL client if needed
echo "📦 Test 2: Checking PostgreSQL Client..."
if ! command -v psql &> /dev/null; then
    echo "   Installing PostgreSQL client..."
    apt-get update -qq && apt-get install -y postgresql-client -qq
    echo "   ✅ PostgreSQL client installed"
else
    echo "   ✅ PostgreSQL client already installed"
fi
echo ""

# Test 3: Database connection
echo "🔌 Test 3: Testing Database Connection..."
CONNECTION_STRING="postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME"

if psql "$CONNECTION_STRING" -c "SELECT 1;" &> /dev/null; then
    echo "   ✅ Database connection SUCCESSFUL!"
    echo ""
    
    # Get PostgreSQL version
    echo "📊 Database Information:"
    psql "$CONNECTION_STRING" -t -c "SELECT version();" | head -1
    echo ""
    
    # Test query
    echo "🧪 Test Query:"
    psql "$CONNECTION_STRING" -c "SELECT current_database(), current_user, inet_server_addr(), inet_server_port();"
    echo ""
    
    # List tables
    echo "📋 Available Tables:"
    psql "$CONNECTION_STRING" -c "\dt"
    echo ""
    
else
    echo "   ❌ Database connection FAILED"
    echo "   Trying to get error details..."
    psql "$CONNECTION_STRING" -c "SELECT 1;" 2>&1
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ALL TESTS PASSED!"
echo ""
echo "🎯 Connection String for Your Application:"
echo "   $CONNECTION_STRING"
echo ""
echo "📝 Python Example:"
echo "   import psycopg2"
echo "   conn = psycopg2.connect("
echo "       host='$DB_HOST',"
echo "       port=$DB_PORT,"
echo "       database='$DB_NAME',"
echo "       user='$DB_USER',"
echo "       password='$DB_PASS'"
echo "   )"
echo ""
echo "🎉 Database is ready to use from RunPod!"

#!/usr/bin/env python3
"""
Quick test script to verify suggestions functionality
"""
import sqlite3
from app import get_db, init_db

# Initialize DB
print("1. Initializing database...")
try:
    init_db()
    print("   ✓ Database initialized")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Check suggestions table exists
print("\n2. Checking suggestions table...")
try:
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='suggestions'")
    if cur.fetchone():
        print("   ✓ Suggestions table exists")
    else:
        print("   ✗ Suggestions table not found")
        exit(1)
    con.close()
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Check table schema
print("\n3. Checking suggestions table schema...")
try:
    con = get_db()
    cur = con.cursor()
    cur.execute("PRAGMA table_info(suggestions)")
    columns = {row[1]: row[2] for row in cur.fetchall()}
    con.close()
    
    required = ['id', 'user_id', 'fullname', 'email', 'sdg_category', 'title', 'description', 'status', 'created_at']
    for col in required:
        if col in columns:
            print(f"   ✓ Column '{col}' exists ({columns[col]})")
        else:
            print(f"   ✗ Column '{col}' missing")
            exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Insert test suggestion
print("\n4. Testing suggestion insert...")
try:
    con = get_db()
    cur = con.cursor()
    cur.execute('''
        INSERT INTO suggestions (user_id, fullname, email, sdg_category, title, description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (1, 'Test User', 'test@example.com', 'SDG 1: No Poverty', 'Test Suggestion', 'This is a test suggestion'))
    con.commit()
    suggestion_id = cur.lastrowid
    con.close()
    print(f"   ✓ Suggestion inserted (ID: {suggestion_id})")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Verify suggestion retrieval
print("\n5. Testing suggestion retrieval...")
try:
    con = get_db()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM suggestions ORDER BY created_at DESC LIMIT 1")
    sugg = cur.fetchone()
    con.close()
    
    if sugg:
        print(f"   ✓ Retrieved suggestion: '{sugg['title']}' by {sugg['fullname']}")
        print(f"     - Status: {sugg['status']}")
        print(f"     - Category: {sugg['sdg_category']}")
    else:
        print("   ✗ No suggestions found")
        exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Test status update
print("\n6. Testing suggestion status update...")
try:
    con = get_db()
    cur = con.cursor()
    cur.execute("UPDATE suggestions SET status = ? WHERE id = ?", ('approved', suggestion_id))
    con.commit()
    
    cur.execute("SELECT status FROM suggestions WHERE id = ?", (suggestion_id,))
    new_status = cur.fetchone()[0]
    con.close()
    
    if new_status == 'approved':
        print(f"   ✓ Status updated to '{new_status}'")
    else:
        print(f"   ✗ Status update failed (got '{new_status}')")
        exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Check counts by status
print("\n7. Checking suggestion status counts...")
try:
    con = get_db()
    cur = con.cursor()
    
    cur.execute("SELECT COUNT(*) FROM suggestions WHERE status = 'pending'")
    pending = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM suggestions WHERE status = 'approved'")
    approved = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM suggestions WHERE status = 'rejected'")
    rejected = cur.fetchone()[0]
    
    con.close()
    
    print(f"   ✓ Pending: {pending}")
    print(f"   ✓ Approved: {approved}")
    print(f"   ✓ Rejected: {rejected}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

print("\n✅ All tests passed! Suggestions feature is working correctly.")
print("\nNOTE: Test data was inserted. You can clean it up with:")
print("  DELETE FROM suggestions WHERE fullname = 'Test User';")

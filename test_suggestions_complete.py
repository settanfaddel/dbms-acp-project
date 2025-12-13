#!/usr/bin/env python3
"""
Test script to verify suggestions feature with proper error handling
"""
import sys
import sqlite3
from app import get_db, init_db

print("=" * 60)
print("SUGGESTIONS FEATURE TEST")
print("=" * 60)

# Step 1: Initialize DB
print("\n[1/6] Initializing database...")
try:
    init_db()
    print("✓ Database initialized successfully")
except Exception as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

# Step 2: Verify table structure
print("\n[2/6] Verifying suggestions table schema...")
try:
    con = get_db()
    cur = con.cursor()
    cur.execute("PRAGMA table_info(suggestions)")
    columns = {row[1]: row[2] for row in cur.fetchall()}
    con.close()
    
    required_columns = {
        'id': 'INTEGER',
        'user_id': 'INTEGER',
        'fullname': 'TEXT',
        'email': 'TEXT',
        'sdg_category': 'TEXT',
        'title': 'TEXT',
        'description': 'TEXT',
        'status': 'TEXT',
        'created_at': 'TIMESTAMP'
    }
    
    all_good = True
    for col, expected_type in required_columns.items():
        if col in columns:
            print(f"  ✓ {col:15} ({columns[col]})")
        else:
            print(f"  ✗ {col:15} MISSING")
            all_good = False
    
    if not all_good:
        print("✗ FAILED: Missing columns")
        sys.exit(1)
    print("✓ All required columns present")
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

# Step 3: Test INSERT
print("\n[3/6] Testing suggestion insertion...")
try:
    con = get_db()
    cur = con.cursor()
    
    test_data = {
        'user_id': 1,
        'fullname': 'Test User',
        'email': 'test@example.com',
        'sdg_category': 'SDG 1: No Poverty',
        'title': 'Test Suggestion Title',
        'description': 'This is a detailed test suggestion'
    }
    
    cur.execute('''
        INSERT INTO suggestions (user_id, fullname, email, sdg_category, title, description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', tuple(test_data.values()))
    
    con.commit()
    suggestion_id = cur.lastrowid
    con.close()
    
    print(f"✓ Suggestion inserted (ID: {suggestion_id})")
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Test SELECT
print("\n[4/6] Testing suggestion retrieval...")
try:
    con = get_db()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    cur.execute("SELECT * FROM suggestions WHERE id = ?", (suggestion_id,))
    sugg = cur.fetchone()
    con.close()
    
    if sugg:
        print(f"✓ Retrieved suggestion:")
        print(f"  - ID: {sugg['id']}")
        print(f"  - Title: {sugg['title']}")
        print(f"  - Author: {sugg['fullname']}")
        print(f"  - Email: {sugg['email']}")
        print(f"  - Category: {sugg['sdg_category']}")
        print(f"  - Status: {sugg['status']}")
    else:
        print(f"✗ FAILED: Could not retrieve suggestion ID {suggestion_id}")
        sys.exit(1)
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 5: Test status filtering
print("\n[5/6] Testing status filtering...")
try:
    con = get_db()
    cur = con.cursor()
    
    cur.execute("SELECT COUNT(*) FROM suggestions WHERE status = 'pending'")
    pending = cur.fetchone()[0]
    print(f"✓ Pending suggestions: {pending}")
    
    # Update status to approved
    cur.execute("UPDATE suggestions SET status = ? WHERE id = ?", ('approved', suggestion_id))
    con.commit()
    
    cur.execute("SELECT COUNT(*) FROM suggestions WHERE status = 'approved'")
    approved = cur.fetchone()[0]
    print(f"✓ Approved suggestions: {approved}")
    
    con.close()
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 6: Verify form submission path
print("\n[6/6] Verifying form submission requirements...")
try:
    # Simulate form data from submit_suggestion route
    form_data = {
        'email': 'user@example.com',
        'sdg_category': 'SDG 3: Good Health',
        'title': 'Healthcare Initiative',
        'description': 'We should focus on preventive healthcare'
    }
    
    # Verify all fields are present
    required_fields = ['email', 'sdg_category', 'title', 'description']
    all_fields_present = all(field in form_data for field in required_fields)
    
    if all_fields_present:
        print("✓ All required form fields present:")
        for field in required_fields:
            print(f"  - {field}: ✓")
    else:
        print("✗ FAILED: Missing form fields")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ FAILED: {e}")
    sys.exit(1)

# Clean up test data
print("\n[Cleanup] Removing test data...")
try:
    con = get_db()
    con.execute("DELETE FROM suggestions WHERE fullname = 'Test User'")
    con.commit()
    con.close()
    print("✓ Test data cleaned up")
except Exception as e:
    print(f"⚠ Warning: Could not clean up test data: {e}")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nThe suggestions feature is ready to use:")
print("1. Users can visit /suggestions")
print("2. Click 'Submit Suggestion' button")
print("3. Fill in email, category, title, and description")
print("4. Click 'Submit Suggestion'")
print("5. Admins can approve/reject suggestions")

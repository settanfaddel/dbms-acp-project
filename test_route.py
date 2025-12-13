#!/usr/bin/env python3
"""
Quick test to verify suggestions route is accessible
"""
import sys
from app import app

# Test that the route exists
print("=" * 60)
print("TESTING SUGGESTIONS ROUTE")
print("=" * 60)

print("\n[1/2] Checking if /suggestions route is registered...")

# Get all registered routes
routes = [rule.rule for rule in app.url_map.iter_rules()]
suggestions_routes = [r for r in routes if 'suggestion' in r.lower()]

if suggestions_routes:
    print("✓ Suggestions routes found:")
    for route in suggestions_routes:
        print(f"  - {route}")
else:
    print("✗ No suggestions routes found!")
    sys.exit(1)

print("\n[2/2] Checking if /suggestions GET route exists...")

suggestions_route = None
for rule in app.url_map.iter_rules():
    if rule.rule == '/suggestions' and 'GET' in rule.methods:
        suggestions_route = rule
        break

if suggestions_route:
    print(f"✓ /suggestions route found")
    print(f"  Methods: {suggestions_route.methods}")
    print(f"  Endpoint: {suggestions_route.endpoint}")
else:
    print("✗ /suggestions GET route not found!")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ROUTE CHECK PASSED!")
print("=" * 60)
print("\nWhen you click 'Suggestions' in the navbar:")
print("1. Browser will navigate to /suggestions")
print("2. You must be logged in (checks session)")
print("3. Page will load suggestions.html")
print("4. Modal will be ready to submit suggestions")
print("\nTo test manually:")
print("1. Start the app: python app.py")
print("2. Log in as any user")
print("3. Click 'Suggestions' link")
print("4. You should see the suggestions page")

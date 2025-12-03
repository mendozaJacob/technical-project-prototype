#!/usr/bin/env python3
"""
Debug script to check Flask routes
"""

import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app
from app import app

def list_routes():
    """List all registered routes in the Flask app"""
    print("🔍 Registered Flask Routes:")
    print("=" * 50)
    
    rules = list(app.url_map.iter_rules())
    rules.sort(key=lambda rule: rule.rule)
    
    teacher_routes = []
    other_routes = []
    
    for rule in rules:
        route_info = f"{rule.rule:30} -> {rule.endpoint}"
        if 'teacher' in rule.endpoint:
            teacher_routes.append(route_info)
        else:
            other_routes.append(route_info)
    
    print("📚 Teacher Routes:")
    for route in teacher_routes:
        print(f"  {route}")
    
    print(f"\n📊 Total Routes: {len(rules)}")
    print(f"📋 Teacher Routes: {len(teacher_routes)}")
    
    # Check specifically for our routes
    target_routes = ['teacher_add_question', 'teacher_edit_question']
    print(f"\n🎯 Checking target routes:")
    for target in target_routes:
        found = any(target in rule.endpoint for rule in rules)
        status = "✅ FOUND" if found else "❌ MISSING"
        print(f"  {target}: {status}")

if __name__ == "__main__":
    list_routes()
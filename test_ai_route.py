#!/usr/bin/env python3
"""
Test script to check if the ai-arrange-questions route is properly defined
"""

import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_route_syntax():
    """Test if the route can be imported without syntax errors"""
    print("🔧 Testing route syntax...")
    
    try:
        # Import the Flask app
        from app import app
        
        # Check if the route exists
        rules = list(app.url_map.iter_rules())
        ai_arrange_routes = [rule for rule in rules if 'ai-arrange-questions' in rule.rule]
        
        if ai_arrange_routes:
            print("✅ AI arrange questions route found:")
            for route in ai_arrange_routes:
                print(f"   {route.rule} -> {route.endpoint}")
        else:
            print("❌ AI arrange questions route NOT found")
            
        # List all teacher routes containing 'ai'
        ai_routes = [rule for rule in rules if 'teacher' in rule.rule and 'ai' in rule.rule.lower()]
        print(f"\n📋 All AI-related teacher routes ({len(ai_routes)}):")
        for route in ai_routes:
            print(f"   {route.rule} -> {route.endpoint}")
            
    except Exception as e:
        print(f"❌ Error importing or checking routes: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_route_syntax()
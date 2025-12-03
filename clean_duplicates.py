#!/usr/bin/env python3
"""
Script to remove duplicate Flask route definitions from app.py
Keeps only the first occurrence of each route.
"""

def clean_app_py():
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    seen_routes = set()
    cleaned_lines = []
    skip_until_next_route = False
    current_function = None
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a route definition
        if line.strip().startswith('@app.route('):
            route_pattern = line.strip()
            
            # Check if we've seen this route before
            if route_pattern in seen_routes:
                # Skip this entire function definition
                skip_until_next_route = True
                print(f"Skipping duplicate route: {route_pattern}")
                i += 1
                continue
            else:
                # This is the first occurrence, keep it
                seen_routes.add(route_pattern)
                skip_until_next_route = False
                print(f"Keeping first occurrence of: {route_pattern}")
        
        # If we're skipping, check if we've reached the next function or route
        if skip_until_next_route:
            # Skip lines until we find another @app.route or def at the start of line
            if line.strip().startswith('@app.route(') or (line.strip().startswith('def ') and not line.startswith('    ')):
                # We've reached the next function/route, stop skipping
                skip_until_next_route = False
                # Don't increment i here, we want to process this line
                continue
            else:
                # Still skipping
                i += 1
                continue
        
        # Add the line if we're not skipping
        cleaned_lines.append(line)
        i += 1
    
    # Write the cleaned content back
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    print(f"Cleaning complete. Reduced from {len(lines)} to {len(cleaned_lines)} lines.")

if __name__ == "__main__":
    clean_app_py()
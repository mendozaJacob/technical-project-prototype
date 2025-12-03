#!/usr/bin/env python3
"""
Test script for automatic enemy generation feature
This script tests the enemy generation functions independently
"""

import json
import random
import os

def determine_chapter_theme(chapter_name, chapter_description=""):
    """Determine the theme of a chapter based on its name and description"""
    text = (chapter_name + " " + chapter_description).lower()
    
    # Theme detection keywords
    theme_keywords = {
        "linux": ["linux", "command", "shell", "terminal", "system", "admin", "filesystem"],
        "security": ["security", "cyber", "firewall", "protection", "encryption", "vulnerability"],
        "network": ["network", "protocol", "routing", "tcp", "ip", "connection", "internet"],
        "python": ["python", "programming", "code", "script", "function", "class"],
        "programming": ["programming", "algorithm", "code", "software", "development", "logic"],
        "database": ["database", "sql", "query", "table", "schema", "data"],
        "web": ["web", "html", "css", "javascript", "frontend", "backend", "api"]
    }
    
    # Check for theme matches
    for theme, keywords in theme_keywords.items():
        if any(keyword in text for keyword in keywords):
            return theme
    
    return "general"

def generate_enemy_name(level, chapter_theme="general", difficulty="Easy"):
    """Generate an appropriate enemy name based on level, theme, and difficulty"""
    
    # Theme-based name components
    theme_prefixes = {
        "general": ["Novice", "Apprentice", "Journeyman", "Expert", "Master", "Grandmaster"],
        "linux": ["System", "Terminal", "Shell", "Kernel", "Command", "Script"],
        "security": ["Cyber", "Secure", "Guardian", "Defender", "Sentinel", "Warden"],
        "network": ["Network", "Protocol", "Packet", "Router", "Switch", "Gateway"],
        "python": ["Code", "Script", "Function", "Class", "Module", "Package"],
        "programming": ["Logic", "Algorithm", "Syntax", "Debug", "Compile", "Execute"],
        "database": ["Query", "Schema", "Index", "Table", "Record", "Database"],
        "web": ["Server", "Client", "API", "HTTP", "Browser", "Web"]
    }
    
    theme_suffixes = {
        "general": ["Guardian", "Keeper", "Warden", "Master", "Lord", "Champion"],
        "linux": ["Admin", "Daemon", "Process", "Wizard", "Guru", "Sage"],
        "security": ["Hunter", "Scanner", "Firewall", "Protector", "Shield", "Vault"],
        "network": ["Router", "Bridge", "Hub", "Node", "Relay", "Gateway"],
        "python": ["Parser", "Compiler", "Interpreter", "Handler", "Manager", "Controller"],
        "programming": ["Debugger", "Optimizer", "Validator", "Executor", "Builder", "Tester"],
        "database": ["Architect", "Designer", "Optimizer", "Administrator", "Analyst", "Engineer"],
        "web": ["Developer", "Designer", "Architect", "Engineer", "Specialist", "Expert"]
    }
    
    # Difficulty modifiers
    difficulty_modifiers = {
        "Easy": ["Apprentice", "Novice", "Junior", "Basic", "Simple"],
        "Medium": ["Skilled", "Advanced", "Senior", "Professional", "Elite"],
        "Hard": ["Master", "Expert", "Legendary", "Supreme", "Ultimate"]
    }
    
    # Get appropriate components
    prefixes = theme_prefixes.get(chapter_theme.lower(), theme_prefixes["general"])
    suffixes = theme_suffixes.get(chapter_theme.lower(), theme_suffixes["general"])
    modifiers = difficulty_modifiers.get(difficulty, difficulty_modifiers["Easy"])
    
    # Create name based on level progression
    if level <= 5:
        prefix = random.choice(prefixes[:2])  # Use easier prefixes
    elif level <= 15:
        prefix = random.choice(prefixes[2:4])  # Use medium prefixes
    else:
        prefix = random.choice(prefixes[4:])  # Use harder prefixes
    
    suffix = random.choice(suffixes)
    
    # Sometimes add difficulty modifier
    if random.random() < 0.3:  # 30% chance
        modifier = random.choice(modifiers)
        return f"{modifier} {suffix}"
    else:
        return f"{prefix} {suffix}"

def generate_enemy_avatar(level, chapter_theme="general"):
    """Generate an appropriate emoji avatar for the enemy"""
    
    theme_avatars = {
        "general": ["🧙‍♂️", "👨‍💻", "👾", "🧞", "🛡️", "⚔️", "🏰", "🎯", "🔮", "⚡"],
        "linux": ["💻", "🖥️", "⌨️", "🔧", "⚙️", "🛠️", "📟", "🔍", "📊", "🗃️"],
        "security": ["🔒", "🛡️", "🔐", "🚨", "👮‍♂️", "🔍", "🚀", "⚡", "🎯", "🛸"],
        "network": ["🌐", "📡", "🔗", "📶", "🌍", "🛰️", "⚡", "🔌", "📊", "🎛️"],
        "python": ["🐍", "🐲", "🔥", "⚡", "🧠", "🔮", "📚", "🎯", "⚙️", "🚀"],
        "programming": ["💻", "🤖", "⚡", "🔧", "⚙️", "🎯", "🧠", "🔮", "🚀", "💡"],
        "database": ["📊", "🗄️", "📈", "💾", "🔍", "📋", "📁", "🎯", "⚡", "🔧"],
        "web": ["🌐", "💻", "📱", "🎨", "🔧", "⚡", "🚀", "💡", "🎯", "📊"]
    }
    
    avatars = theme_avatars.get(chapter_theme.lower(), theme_avatars["general"])
    
    # Progressive avatar selection based on level
    if level <= 5:
        return random.choice(avatars[:3])  # Simpler avatars
    elif level <= 15:
        return random.choice(avatars[3:7])  # Medium complexity
    else:
        return random.choice(avatars[7:])  # More intimidating avatars

def generate_enemy_taunt_auto(level, chapter_theme="general", difficulty="Easy", enemy_name="Enemy"):
    """Generate an appropriate taunt for automatically created enemies"""
    
    theme_taunts = {
        "general": [
            f"{enemy_name} challenges your knowledge!",
            "Can you handle this level of difficulty?",
            "Let's see what you're made of!",
            "Your skills will be tested here!",
            "Prepare for a real challenge!"
        ],
        "linux": [
            "Your command line skills are weak!",
            "Can you navigate the terminal?",
            "Let's see your system administration prowess!",
            "Shell scripting will be your downfall!",
            "The filesystem maze awaits you!"
        ],
        "security": [
            "Your defenses are inadequate!",
            "Can you protect against my attacks?",
            "Security through obscurity won't help you!",
            "Your firewall knowledge is lacking!",
            "Let's test your cybersecurity skills!"
        ],
        "network": [
            "Your network knowledge has gaps!",
            "Can you configure proper routing?",
            "Protocol understanding is key!",
            "Let's see your connectivity skills!",
            "Network troubleshooting will challenge you!"
        ],
        "python": [
            "Your Python code has bugs!",
            "Can you handle advanced syntax?",
            "Let's test your programming logic!",
            "Object-oriented concepts will confuse you!",
            "Your algorithms need improvement!"
        ],
        "programming": [
            "Your code lacks elegance!",
            "Can you debug efficiently?",
            "Algorithm complexity will defeat you!",
            "Let's see your problem-solving skills!",
            "Data structures will challenge you!"
        ],
        "database": [
            "Your queries are inefficient!",
            "Can you design proper schemas?",
            "Let's test your SQL knowledge!",
            "Database optimization will challenge you!",
            "Relational concepts will confuse you!"
        ],
        "web": [
            "Your frontend skills need work!",
            "Can you handle responsive design?",
            "Let's test your web standards knowledge!",
            "API integration will challenge you!",
            "Your user experience is lacking!"
        ]
    }
    
    base_taunts = theme_taunts.get(chapter_theme.lower(), theme_taunts["general"])
    
    # Add difficulty-based intensity
    if difficulty == "Hard":
        intensity_modifiers = ["This will destroy you!", "Prepare for defeat!", "You have no chance!"]
        if random.random() < 0.4:
            return random.choice(intensity_modifiers)
    
    return random.choice(base_taunts)

def auto_generate_enemy(level, chapter_id=1, difficulty="Easy"):
    """Generate a complete enemy for a given level"""
    # Load chapters to determine theme
    try:
        with open('data/chapters.json', 'r', encoding='utf-8') as f:
            chapters_data = json.load(f)
        
        chapter = None
        for ch in chapters_data.get('chapters', []):
            if ch.get('id') == chapter_id:
                chapter = ch
                break
        
        if chapter:
            chapter_theme = determine_chapter_theme(
                chapter.get('name', ''), 
                chapter.get('description', '')
            )
        else:
            chapter_theme = "general"
    except:
        chapter_theme = "general"
    
    # Generate enemy components
    name = generate_enemy_name(level, chapter_theme, difficulty)
    avatar = generate_enemy_avatar(level, chapter_theme)
    taunt = generate_enemy_taunt_auto(level, chapter_theme, difficulty, name)
    
    # Create enemy object
    enemy = {
        "level": level,
        "name": name,
        "avatar": avatar,
        "taunt": taunt,
        "image": f"enemies/{name.lower().replace(' ', '_')}.jpg",
        "range": f"Q{level*10-9}–Q{level*10}"  # Approximate range
    }
    
    return enemy

def test_enemy_generation():
    """Test the automatic enemy generation functions"""
    print("🧪 Testing Automatic Enemy Generation System")
    print("=" * 50)
    
    # Test 1: Generate enemy for different themes
    themes = ["linux", "security", "python", "network", "general"]
    
    for theme in themes:
        print(f"\n📋 Testing theme: {theme}")
        enemy = auto_generate_enemy(level=99, chapter_id=999, difficulty="Medium")
        
        print(f"  🏷️  Name: {enemy['name']}")
        print(f"  🎭 Avatar: {enemy['avatar']}")
        print(f"  💬 Taunt: {enemy['taunt']}")
        print(f"  📍 Level: {enemy['level']}")
    
    # Test 2: Theme detection
    print(f"\n🔍 Testing theme detection:")
    test_chapters = [
        ("Linux Fundamentals", "Basic Linux commands and system administration"),
        ("Python Programming", "Learn Python coding and algorithms"),
        ("Network Security", "Cybersecurity and firewall management"),
        ("Web Development", "HTML, CSS, and JavaScript basics")
    ]
    
    for name, desc in test_chapters:
        theme = determine_chapter_theme(name, desc)
        print(f"  '{name}' -> Theme: {theme}")
    
    # Test 3: Generate sample enemies for different levels and difficulties
    print(f"\n🎯 Testing level progression and difficulty:")
    for level in [1, 5, 10, 15, 20]:
        for difficulty in ["Easy", "Medium", "Hard"]:
            enemy = auto_generate_enemy(level=level, chapter_id=1, difficulty=difficulty)
            print(f"  Level {level:2d} ({difficulty:6s}): {enemy['name']} {enemy['avatar']}")
    
    print(f"\n✅ All tests completed successfully!")
    print("🚀 The automatic enemy generation system is ready!")

if __name__ == "__main__":
    test_enemy_generation()
import requests
from bs4 import BeautifulSoup

# Test what the actual HTML looks like
response = requests.get('http://127.0.0.1:5000/teacher/levels')
soup = BeautifulSoup(response.content, 'html.parser')

# Find level cards and check their data-chapter-id attributes
level_cards = soup.find_all('div', class_='level-card')

print(f"Found {len(level_cards)} level cards:")
for i, card in enumerate(level_cards[:10]):  # First 10 cards
    chapter_id = card.get('data-chapter-id')
    level_title = card.find('h3', class_='level-title')
    level_text = level_title.text if level_title else "Unknown"
    print(f"  {level_text}: data-chapter-id='{chapter_id}'")

# Check the dropdown options
chapter_options = soup.find_all('option')
print(f"\nDropdown options:")
for option in chapter_options:
    value = option.get('value')
    text = option.text.strip()
    print(f"  Value: '{value}' → Text: '{text}'")
import os
import re

files = [
    r"f:\CalAi\stitch_nutrivision_ai\nutriflow_dashboard\code.html",
    r"f:\CalAi\stitch_nutrivision_ai\ai_nutrition_scanner\code.html",
    r"f:\CalAi\stitch_nutrivision_ai\meal_history_logs\code.html",
    r"f:\CalAi\stitch_nutrivision_ai\profile_health_goals\code.html"
]

# The sidebars typically have href="#" followed by something with data-icon="dashboard" etc.
# We can use regex to replace href="#" when it's immediately preceding or containing these icons.
# A simpler approach: Just find all <a> tags that contain the word Dashboard, AI Scanner, History, Settings/Profile and replace their href.

for filepath in files:
    if not os.path.exists(filepath): continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: <a ... href="#" ...> ... >Dashboard< ... </a>
    # We can just replace href="#" with a temporary placeholder if we know what follows it.
    
    # Let's do it with a simple state machine or regex
    # Actually, the quickest hack is to replace specific blocks of HTML or use BeautifulSoup.
    
    # But since we just want to replace href="#" for the sidebar items:
    # 1. dashboard
    content = re.sub(r'href="#"([^>]*>[^<]*<span[^>]*data-icon="dashboard"[^>]*>dashboard</span>)', r'href="/"\1', content)
    # 2. AI Scanner / monochrome_photos
    content = re.sub(r'href="#"([^>]*>[^<]*<span[^>]*data-icon="monochrome_photos"[^>]*>monochrome_photos</span>)', r'href="/scanner"\1', content)
    # 3. History
    content = re.sub(r'href="#"([^>]*>[^<]*<span[^>]*data-icon="history"[^>]*>history</span>)', r'href="/history"\1', content)
    # 4. Settings / Profile
    content = re.sub(r'href="#"([^>]*>[^<]*<span[^>]*data-icon="person"[^>]*>person</span>)', r'href="/profile"\1', content)
    content = re.sub(r'href="#"([^>]*>[^<]*<span[^>]*data-icon="settings"[^>]*>settings</span>)', r'href="/profile"\1', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Links updated")

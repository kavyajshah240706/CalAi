import os
import re

def fix_avatars(directory):
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith('.html'):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                original = content
                
                # Make any <img ... alt="User profile avatar" ...> clickable
                # Find <img ... alt="User profile avatar" ...> that does NOT have onclick
                # We can just replace '<img alt="User profile avatar"' with '<img onclick="window.location.href=\'/profile\'" style="cursor:pointer" alt="User profile avatar"'
                
                # Check if not already added
                if 'onclick="window.location.href=\'/profile\'"' not in content:
                    content = content.replace(
                        '<img alt="User profile avatar"',
                        '<img onclick="window.location.href=\'/profile\'" style="cursor:pointer" alt="User profile avatar"'
                    )
                
                if content != original:
                    with open(path, 'w', encoding='utf-8') as file:
                        file.write(content)
                    print(f"Fixed avatar in {path}")

fix_avatars('f:/CalAi/src/frontend')

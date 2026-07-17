import os
import re

LOGOUT_HTML = """
            <button onclick="handleLogout()" class="w-full mt-2 flex items-center space-x-3 px-4 py-3 rounded-lg text-red-500 hover:bg-red-50 transition-all duration-300">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
                <span class="font-label-lg text-label-lg">Sign Out</span>
            </button>
            <script>
                async function handleLogout() {
                    try {
                        const res = await fetch('/api/logout', { method: 'POST' });
                        if(res.ok) window.location.href = '/login';
                    } catch(e) { console.error('Logout failed', e); }
                }
            </script>
"""

def add_logout(directory):
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith('.html'):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                original = content
                
                if 'href="/profile"' in content and 'handleLogout()' not in content:
                    content = re.sub(
                        r'(<a[^>]*href="/profile"[^>]*>.*?</a>)',
                        r'\1' + LOGOUT_HTML,
                        content,
                        flags=re.DOTALL
                    )
                
                if content != original:
                    with open(path, 'w', encoding='utf-8') as file:
                        file.write(content)
                    print(f"Added logout to {path}")

add_logout('f:/CalAi/src/frontend')

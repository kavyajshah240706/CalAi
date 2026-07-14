import os

folders = ['ai_nutrition_scanner', 'meal_history_logs', 'nutriflow_chat', 'nutriflow_dashboard', 'profile_health_goals']
chat_nav = '''<li>
<a class="flex items-center gap-3 p-3 rounded-lg text-on-surface-variant dark:text-surface-variant hover:text-primary hover:bg-surface-container-low dark:hover:bg-surface-container transition-colors duration-200" href="/chat">
<span class="material-symbols-outlined" data-icon="forum">forum</span>
<span class="font-body-md text-body-md">AI Chat</span>
</a>
</li>
'''

for f in folders:
    path = f'src/frontend/{f}/code.html'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        if 'href="/chat"' not in content:
            mobile_target = '<a class="flex flex-col items-center text-on-surface-variant" href="/history">'
            mobile_chat = '''<a class="flex flex-col items-center text-on-surface-variant" href="/chat">
<span class="material-symbols-outlined" data-icon="forum">forum</span>
<span class="font-label-sm text-label-sm mt-1">Chat</span>
</a>
'''
            content = content.replace(mobile_target, mobile_chat + mobile_target)
            
            parts = content.split('</ul>')
            if len(parts) > 1:
                content = parts[0] + chat_nav + '</ul>' + '</ul>'.join(parts[1:])
            
            with open(path, 'w', encoding='utf-8') as file:
                file.write(content)

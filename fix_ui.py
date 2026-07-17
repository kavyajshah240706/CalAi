import os
import re

def fix_ui(directory):
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith('.html'):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                original = content
                
                # 1. Fix broken images in dashboard
                content = content.replace(
                    '`\n                        <img alt="${meal.food_name}" class="w-16 h-16 rounded-md object-cover mr-4 shadow-sm" src="${meal.image_url || \'https://via.placeholder.com/150\'}"/>',
                    '`\n                        ${meal.image_url && meal.image_url !== "None" ? `<img alt="${meal.food_name}" class="w-16 h-16 rounded-md object-cover mr-4 shadow-sm" src="${meal.image_url}"/>` : `<div class="w-16 h-16 rounded-md mr-4 bg-surface-container-high flex items-center justify-center text-primary"><span class="material-symbols-outlined" style="font-size: 32px">restaurant</span></div>`}'
                )
                
                # 2. Fix broken images in history logs
                content = content.replace(
                    '<img alt="${meal.food_name}" class="w-full h-full object-cover" src="${meal.image_url || \'https://via.placeholder.com/300?text=No+Image\'}" />',
                    '${meal.image_url && meal.image_url !== "None" ? `<img alt="${meal.food_name}" class="w-full h-full object-cover" src="${meal.image_url}" />` : `<div class="w-full h-full bg-surface-container-high flex items-center justify-center text-primary"><span class="material-symbols-outlined" style="font-size: 48px">restaurant</span></div>`}'
                )

                # 3. Fix Top Right Header buttons
                
                # btnAiAnalyze
                content = content.replace(
                    '<button id="btnAiAnalyze"',
                    '<button id="btnAiAnalyze" onclick="window.location.href=\'/scanner\'"'
                )
                
                # Notifications
                # We can match the exact structure
                content = content.replace(
                    '<button class="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-full hover:bg-surface-container-low">\n<span class="material-symbols-outlined" data-icon="notifications">notifications</span>',
                    '<button onclick="alert(\'You are all caught up! No new notifications.\')" class="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-full hover:bg-surface-container-low">\n<span class="material-symbols-outlined" data-icon="notifications">notifications</span>'
                )
                
                # Settings
                content = content.replace(
                    '<button class="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-full hover:bg-surface-container-low">\n<span class="material-symbols-outlined" data-icon="settings">settings</span>',
                    '<button onclick="window.location.href=\'/profile\'" class="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-full hover:bg-surface-container-low">\n<span class="material-symbols-outlined" data-icon="settings">settings</span>'
                )
                
                # Profile Avatar
                content = content.replace(
                    '<img alt="User profile avatar" class="w-8 h-8 rounded-full object-cover border-2 border-surface-container shadow-soft"',
                    '<img onclick="window.location.href=\'/profile\'" style="cursor:pointer" alt="User profile avatar" class="w-8 h-8 rounded-full object-cover border-2 border-surface-container shadow-soft"'
                )
                
                if content != original:
                    with open(path, 'w', encoding='utf-8') as file:
                        file.write(content)
                    print(f"Fixed UI elements in {path}")

fix_ui('f:/CalAi/src/frontend')

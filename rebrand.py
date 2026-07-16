import os

def replace_in_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.html', '.py', '.md')):
                filepath = os.path.join(root, file)
                if filepath == os.path.abspath(__file__):
                    continue
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'CalAi' in content or 'nutriflow' in content:
                    content = content.replace('CalAi', 'CalAi')
                    # Don't replace nutriflow_dashboard folder names since it might break paths, only visible strings
                    content = content.replace('Welcome to calai', 'Welcome to calai')
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Updated {filepath}")

replace_in_files('f:/CalAi')

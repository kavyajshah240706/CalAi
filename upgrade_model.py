import os
def upgrade_models(dir):
    for root, d, files in os.walk(dir):
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as file: c = file.read()
                
                original = c
                c = c.replace('"gemini-1.5-flash"', '"gemini-3.5-flash"')
                c = c.replace('location="us-central1"', 'location="global"')
                
                if original != c:
                    with open(path, 'w', encoding='utf-8') as file: file.write(c)
                    print(f"Upgraded {path}")

upgrade_models('f:/CalAi/src')

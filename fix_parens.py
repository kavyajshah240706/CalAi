import os
def fix(dir):
    for root, d, files in os.walk(dir):
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                with open(path, 'r', encoding='utf-8') as file: c = file.read()
                c = c.replace('location="us-central1"))', 'location="us-central1")')
                with open(path, 'w', encoding='utf-8') as file: file.write(c)
fix('f:/CalAi/src')

import os
import re

def migrate_to_vertex(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and file != 'fix_vertex.py':
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # 1. Replace gemini-3.5-flash with gemini-1.5-flash
                content = content.replace('"gemini-3.5-flash"', '"gemini-1.5-flash"')
                
                # 2. Replace genai.Client instantiations to use Vertex AI
                # Match genai.Client(...) across multiple lines
                pattern = r'genai\.Client\([^)]*\)'
                replacement = 'genai.Client(vertexai=True, project="gemini-project-2-500616", location="us-central1")'
                
                content = re.sub(pattern, replacement, content)
                
                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Updated {filepath}")

migrate_to_vertex('f:/CalAi/src')

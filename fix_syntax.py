import os
import re

def fix_syntax(directory):
    pattern1 = r'client = genai\.Client\(vertexai=True, project="gemini-project-2-500616", location="us-central1"\),\s*http_options=types\.HttpOptions\(api_version="v1"\)\s*\)'
    replacement1 = 'client = genai.Client(vertexai=True, project="gemini-project-2-500616", location="us-central1")'
    
    # Check for other variations
    pattern2 = r'self\.client = genai\.Client\(vertexai=True, project="gemini-project-2-500616", location="us-central1"\),\s*http_options=types\.HttpOptions\(api_version="v1"\)\s*\)'
    replacement2 = 'self.client = genai.Client(vertexai=True, project="gemini-project-2-500616", location="us-central1")'

    # Any leftover generic ones where it didn't have http_options
    pattern3 = r'client = genai\.Client\(vertexai=True, project="gemini-project-2-500616", location="us-central1"\),\s*\)'
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and file not in ['fix_vertex.py', 'fix_syntax.py']:
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                content = re.sub(pattern1, replacement1, content)
                content = re.sub(pattern2, replacement2, content)
                content = re.sub(pattern3, replacement1, content)
                
                # Also just in case there are random dangling `)` 
                content = content.replace('client = genai.Client(vertexai=True, project="gemini-project-2-500616", location="us-central1")\n            )', 'client = genai.Client(vertexai=True, project="gemini-project-2-500616", location="us-central1")')
                
                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Fixed syntax in {filepath}")

fix_syntax('f:/CalAi/src')

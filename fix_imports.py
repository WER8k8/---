import os, re
path = 'backend/app'
for root, dirs, files in os.walk(path):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            content = content.replace('`nfrom', '\nfrom')
            content = re.sub(r'from app\.models\.content import (.*?),\s*\nfrom app\.models\.seo_metadata', r'from app.models.content import \1\nfrom app.models.seo_metadata', content)
            content = content.replace('from app.models.content import \n', '')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

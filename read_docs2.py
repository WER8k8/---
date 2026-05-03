from docx import Document
import os
import json

os.chdir(r'c:\Users\97907\Desktop\UJ\wang  zhan')

docs = [f for f in os.listdir('prompt_lib') if f.endswith('.docx')]
output = {}

for doc_name in docs:
    print(f'Reading: {doc_name}')
    try:
        doc = Document(os.path.join('prompt_lib', doc_name))
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        output[doc_name] = '\n'.join(full_text)
    except Exception as e:
        output[doc_name] = f'Error: {e}'

# Save to JSON file for easier reading
with open('prompt_lib_output.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'Done. Saved to prompt_lib_output.json')
print(f'Total docs read: {len(docs)}')
for name in docs:
    length = len(output.get(name, ''))
    print(f'  {name}: {length} chars')

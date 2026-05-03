from docx import Document
import os

os.chdir(r'c:\Users\97907\Desktop\UJ\wang  zhan')

docs = [f for f in os.listdir('prompt_lib') if f.endswith('.docx')]
for doc_name in docs:
    print(f'=== {doc_name} ===')
    try:
        doc = Document(os.path.join('prompt_lib', doc_name))
        for para in doc.paragraphs:
            if para.text.strip():
                print(para.text)
        print()
    except Exception as e:
        print(f'Error: {e}')
    print()

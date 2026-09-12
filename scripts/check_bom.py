import os

path = r"c:\Users\Administrator.WIN-36O2UQRI3U1\Desktop\上线网站开发完成\上线网站\backend\config\dev\.env"

with open(path, 'rb') as f:
    header = f.read(4)
    
print(f"File header (hex): {header.hex()}")
print(f"Has BOM: {header.startswith(b'\xef\xbb\xbf')}")

with open(path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'N8N_WEBHOOK_SECRET' in line:
            print(f"\nLine {i+1}: {repr(line)}")
            break
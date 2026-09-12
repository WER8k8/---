path = r"c:\Users\Administrator.WIN-36O2UQRI3U1\Desktop\上线网站开发完成\上线网站\backend\config\dev\.env"

with open(path, 'rb') as f:
    content = f.read()
    
lines = content.split(b'\n')
for i, line in enumerate(lines):
    if b'N8N' in line:
        print(f"Line {i+1}:")
        print(f"  Binary: {line.hex()}")
        print(f"  Text: {line.decode('utf-8', errors='replace')}")
        print()
        
for i, line in enumerate(lines):
    if b'MEM0_API_URL' in line:
        print(f"Line {i+1} (MEM0):")
        print(f"  Binary: {line.hex()}")
        print(f"  Text: {line.decode('utf-8', errors='replace')}")
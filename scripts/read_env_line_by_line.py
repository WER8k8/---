path = r"c:\Users\Administrator.WIN-36O2UQRI3U1\Desktop\上线网站开发完成\上线网站\backend\config\dev\.env"

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
for i, line in enumerate(lines):
    if 210 <= i+1 <= 230:
        stripped = line.strip()
        print(f"Line {i+1}: len={len(line)}, stripped_len={len(stripped)}")
        print(f"  Raw: {repr(line)}")
        if stripped:
            print(f"  Stripped: {repr(stripped)}")
            if '=' in stripped and not stripped.startswith('#'):
                parts = stripped.split('=', 1)
                print(f"  KEY: {repr(parts[0].strip())}")
                print(f"  VAL: {repr(parts[1].strip())}")
        print()
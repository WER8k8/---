"""批量修复错误的 apiGet 导入和调用"""

import os
import re

views_dir = r"C:\Users\97907\Desktop\上线网站\frontend\admin\src\views"

# 要匹配的错误模式
# 1. import { apiGet } from '@/utils/api'
# 2. onMounted(async () => { try { await apiGet('/xxx') } catch { /* 空状态 */ } })

pattern = r'''import\s+\{\s*apiGet\s*\}\s+from\s+['"]@/utils/api['"]\s*

onMounted\(async\s+\(\)\s*=>\s*\{\s*
\s*try\s*\{\s*await\s+apiGet\(['"][^'"]*['"]\)\s*\}\s*catch\s*\{\s*/\*\s*空状态\s*\*/\s*\}\s*
\}\)'''

fixed_count = 0

for root, dirs, files in os.walk(views_dir):
    for file in files:
        if file.endswith('.vue'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否包含错误模式
            if 'apiGet' in content and "from '@/utils/api'" in content:
                # 使用更简单的字符串替换
                original = content
                
                # 替换模式：移除 apiGet 导入和错误的 onMounted 调用
                # 保留正常的 onMounted 和导入
                lines = content.split('\n')
                new_lines = []
                skip_next = 0
                
                for i, line in enumerate(lines):
                    if skip_next > 0:
                        skip_next -= 1
                        continue
                    
                    # 检查是否是 apiGet 导入行
                    if "import { apiGet } from '@/utils/api'" in line:
                        # 跳过这行和接下来的空行
                        continue
                    
                    # 检查是否是错误的 onMounted 调用
                    if 'onMounted(async () => {' in line and i + 1 < len(lines):
                        # 检查下一行是否包含 apiGet 调用
                        next_lines = '\n'.join(lines[i:i+6])
                        if 'apiGet' in next_lines and '空状态' in next_lines:
                            # 跳过这整个块
                            # 找到匹配的闭合括号
                            brace_count = 0
                            started = False
                            for j in range(i, min(i+10, len(lines))):
                                if '{' in lines[j]:
                                    brace_count += lines[j].count('{')
                                    started = True
                                if '}' in lines[j]:
                                    brace_count -= lines[j].count('}')
                                if started and brace_count <= 0:
                                    skip_next = j - i
                                    break
                            continue
                    
                    new_lines.append(line)
                
                new_content = '\n'.join(new_lines)
                
                if new_content != original:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"✅ 修复: {filepath}")
                    fixed_count += 1

print(f"\n共修复 {fixed_count} 个文件")

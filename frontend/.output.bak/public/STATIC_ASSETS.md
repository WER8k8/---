# 优丁建材 AI-SaaS - 静态资源

## 已创建的资源 (2026-05-12)

1. **favicon.ico** - 浏览器标签页图标 (32x32)
2. **logo.png** - 网站Logo (200x60)
3. **og-default.jpg** - 社交分享默认图 (1200x630)
4. **product-default.jpg** - 产品占位图 (400x400)

## 创建方法

由于直接生成图片可能需要较长执行时间，建议手动创建或使用在线工具：

### 方案1: 使用在线工具

访问 https://www.favicon.cc/ 或 https://realfavicongenerator.net/

### 方案2: 使用Python脚本

```python
from PIL import Image, ImageDraw
import os

public_dir = 'c:/Users/97907/Desktop/UJ/website/frontend/public'

# 创建基础图片
img = Image.new('RGB', (32, 32), color='#1E40AF')
draw = ImageDraw.Draw(img)
img.save(os.path.join(public_dir, 'favicon.ico'), format='ICO')
```

### 方案3: 从模板下载

可以从 Unsplash 等网站下载占位图：

- og-default.jpg: 社交分享图 (1200x630)
- product-default.jpg: 产品图 (400x400)

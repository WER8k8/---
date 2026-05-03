"""
生产环境安全配置脚本
生成安全的JWT密钥、数据库密码等敏感配置
"""

import secrets
import string
import os
from pathlib import Path


def generate_jwt_secret():
    """生成安全的JWT密钥"""
    return secrets.token_hex(32)


def generate_database_password(length=32):
    """生成安全的数据库密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in "!@#$%^&*" for c in password)):
            return password


def generate_env_file():
    """生成生产环境.env文件"""
    jwt_secret = generate_jwt_secret()
    db_password = generate_database_password()
    
    env_content = f"""# ===========================================
# 生产环境配置文件
# 生成时间: {__import__('datetime').datetime.now().isoformat()}
# ===========================================
# ⚠️ 安全警告：请勿将此文件提交到版本控制系统！
# ===========================================

# 应用配置
APP_NAME=轻集料混凝土SEO智能运营系统
DEBUG=False
API_V1_PREFIX=/api/v1

# 安全配置 - 必须修改
JWT_SECRET_KEY={jwt_secret}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# 数据库配置 - 生产环境使用PostgreSQL
DB_TYPE=postgresql
DATABASE_URL=postgresql://youding_admin:{db_password}@localhost:5432/youding_prod

# Redis配置
REDIS_URL=redis://localhost:6379/0

# CORS配置 - 修改为实际域名
CORS_ORIGINS=["https://youding.com", "https://www.youding.com"]
ALLOWED_HOSTS=["youding.com", "www.youding.com"]

# AI服务配置
AI_NVIDIA_API_KEY=your-nvidia-api-key-here
AI_OPENAI_API_KEY=your-openai-api-key-here

# 文件上传配置
MAX_UPLOAD_SIZE_MB=20
ALLOWED_EXTENSIONS=["jpg", "jpeg", "png", "gif", "webp", "pdf", "doc", "docx", "xls", "xlsx", "dwg", "dxf"]

# 限流配置
RATE_LIMIT_MAX_REQUESTS=60
RATE_LIMIT_WINDOW_SECONDS=60
"""
    
    env_path = Path(__file__).parent / ".env.production"
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✅ 生产环境配置文件已生成: {env_path}")
    print(f"\n🔑 JWT_SECRET_KEY: {jwt_secret}")
    print(f"🔒 数据库密码: {db_password}")
    print(f"\n⚠️  安全提示:")
    print(f"  1. 请将 .env.production 文件移动到安全位置")
    print(f"  2. 不要将此文件提交到Git仓库")
    print(f"  3. 在服务器上设置环境变量或使用.env文件")
    print(f"  4. 定期更换JWT密钥和数据库密码")
    
    return jwt_secret, db_password


def check_gitignore():
    """检查.gitignore是否包含.env文件"""
    gitignore_path = Path(__file__).parent.parent / ".gitignore"
    
    if not gitignore_path.exists():
        print("\n⚠️  未找到.gitignore文件，创建中...")
        gitignore_content = """# 环境配置文件
.env
.env.local
.env.production
.env.staging

# 数据库文件
*.db
*.sqlite3

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# 日志文件
*.log
logs/

# 上传文件
uploads/
"""
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print(f"✅ 已创建 .gitignore: {gitignore_path}")
    else:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '.env' not in content:
            print("\n⚠️  .gitignore中缺少.env配置，正在添加...")
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                f.write("\n# 环境配置文件\n.env\n.env.local\n.env.production\n.env.staging\n")
            print("✅ 已更新 .gitignore")
        else:
            print("✅ .gitignore已包含.env配置")


if __name__ == "__main__":
    print("="*60)
    print("🔐 生产环境安全配置工具")
    print("="*60)
    
    check_gitignore()
    print()
    generate_env_file()
    
    print("\n" + "="*60)
    print("✅ 配置完成！")
    print("="*60)

"""
HTTPS证书配置和SSL中间件
支持Let's Encrypt自动证书管理
"""

import ssl
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware


class SSLConfig:
    """SSL配置类"""
    
    # 证书目录
    CERT_DIR = Path(__file__).parent.parent.parent / "certs"
    CERT_DIR.mkdir(exist_ok=True)
    
    # 证书文件路径
    CERT_FILE = CERT_DIR / "fullchain.pem"
    KEY_FILE = CERT_DIR / "privkey.pem"
    
    @classmethod
    def is_ssl_configured(cls) -> bool:
        """检查SSL证书是否已配置"""
        return cls.CERT_FILE.exists() and cls.KEY_FILE.exists()
    
    @classmethod
    def create_ssl_context(cls) -> ssl.SSLContext:
        """创建SSL上下文"""
        if not cls.is_ssl_configured():
            raise FileNotFoundError(
                f"SSL证书未找到！\n"
                f"请将证书文件放置到: {cls.CERT_DIR}\n"
                f"需要文件: fullchain.pem, privkey.pem"
            )
        
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(
            certfile=str(cls.CERT_FILE),
            keyfile=str(cls.KEY_FILE)
        )
        
        # 安全配置
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.set_ciphers(
            'ECDHE-ECDSA-AES128-GCM-SHA256:'
            'ECDHE-RSA-AES128-GCM-SHA256:'
            'ECDHE-ECDSA-AES256-GCM-SHA384:'
            'ECDHE-RSA-AES256-GCM-SHA384'
        )
        context.options |= ssl.OP_NO_COMPRESSION
        
        return context
    
    @classmethod
    def setup_https_redirect(cls, app: FastAPI):
        """配置HTTPS重定向中间件"""
        
        class HTTPSRedirectMiddleware:
            def __init__(self, app):
                self.app = app
            
            async def __call__(self, scope, receive, send):
                if scope["type"] == "http":
                    # 检查是否是健康检查或ACME验证请求
                    path = scope.get("path", "")
                    if path.startswith("/.well-known/acme-challenge/"):
                        await self.app(scope, receive, send)
                        return
                    
                    # HTTP重定向到HTTPS
                    headers = dict(scope.get("headers", []))
                    host = headers.get(b"host", b"localhost").decode()
                    
                    body = b"HTTPS required"
                    await send({
                        "type": "http.response.start",
                        "status": 301,
                        "headers": [
                            (b"location", f"https://{host}{path}".encode()),
                            (b"content-length", str(len(body)).encode()),
                        ],
                    })
                    await send({
                        "type": "http.response.body",
                        "body": body,
                    })
                    return
                
                await self.app(scope, receive, send)
        
        app.add_middleware(HTTPSRedirectMiddleware)
    
    @classmethod
    def setup_security_headers(cls, app: FastAPI):
        """配置安全响应头"""
        
        class SecurityHeadersMiddleware:
            def __init__(self, app):
                self.app = app
            
            async def __call__(self, scope, receive, send):
                if scope["type"] != "http":
                    await self.app(scope, receive, send)
                    return
                
                async def send_with_headers(message):
                    if message["type"] == "http.response.start":
                        headers = list(message.get("headers", []))
                        
                        # 添加安全头
                        security_headers = [
                            (b"strict-transport-security", b"max-age=31536000; includeSubDomains; preload"),
                            (b"x-content-type-options", b"nosniff"),
                            (b"x-frame-options", b"DENY"),
                            (b"x-xss-protection", b"1; mode=block"),
                            (b"referrer-policy", b"strict-origin-when-cross-origin"),
                            (b"content-security-policy", b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"),
                            (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
                        ]
                        
                        headers.extend(security_headers)
                        message["headers"] = headers
                    
                    await send(message)
                
                await self.app(scope, receive, send_with_headers)
        
        app.add_middleware(SecurityHeadersMiddleware)
    
    @classmethod
    def generate_self_signed_cert(cls):
        """生成自签名证书（仅用于开发测试）"""
        import subprocess
        
        cert_path = str(cls.CERT_FILE)
        key_path = str(cls.KEY_FILE)
        
        if cls.is_ssl_configured():
            print("✅ SSL证书已存在")
            return
        
        print("🔐 生成自签名SSL证书（仅用于开发测试）...")
        
        try:
            subprocess.run([
                "openssl", "req", "-x509", "-newkey", "rsa:4096",
                "-keyout", key_path,
                "-out", cert_path,
                "-days", "365",
                "-nodes",
                "-subj", "/C=CN/ST=Beijing/L=Beijing/O=YouDing/OU=IT/CN=localhost"
            ], check=True)
            
            print(f"✅ 自签名证书已生成: {cert_path}")
            print("⚠️  警告: 自签名证书仅用于开发测试，生产环境请使用Let's Encrypt")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 证书生成失败: {e}")
        except FileNotFoundError:
            print("❌ OpenSSL未安装，请先安装OpenSSL")


def setup_ssl(app: FastAPI, enable_https: bool = True):
    """配置SSL"""
    
    # 配置安全头
    SSLConfig.setup_security_headers(app)
    
    if enable_https:
        # 配置HTTPS重定向
        SSLConfig.setup_https_redirect(app)
        
        # 检查证书
        if SSLConfig.is_ssl_configured():
            print("✅ SSL证书已加载")
        else:
            print("⚠️  SSL证书未配置，HTTP模式运行")
    
    return app

"""应用启动脚本 - 支持多环境配置"""

import logging
import os
import sys
import argparse

import uvicorn
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def load_environment_config(env: str):
    """
    动态加载指定环境的配置文件

    Args:
        env: 环境名称 (dev, test, prod)

    Returns:
        bool: 配置加载是否成功
    """
    config_dir = os.path.join(os.path.dirname(__file__), 'config', env)
    env_file = os.path.join(config_dir, '.env')

    if os.path.exists(env_file):
        load_dotenv(env_file)
        logger.info("已加载 %s 环境配置: %s", env, env_file)
        return True
    else:
        logger.warning("未找到 %s 环境配置文件: %s", env, env_file)
        logger.warning("请确保文件存在或从 .env.example 复制")
        example_file = os.path.join(config_dir, '.env.example')
        if os.path.exists(example_file):
            load_dotenv(example_file)
            logger.info("已加载示例配置作为备用: %s", example_file)
            return True
        return False

def main():
    parser = argparse.ArgumentParser(description='启动优丁平台后端服务')
    parser.add_argument(
        '--env',
        type=str,
        default='dev',
        choices=['dev', 'test', 'prod'],
        help='运行环境: dev(开发), test(测试), prod(生产)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='服务端口号（默认从环境变量PORT读取）'
    )
    parser.add_argument(
        '--host',
        type=str,
        default=None,
        help='绑定地址（默认从环境变量HOST读取，若无则为0.0.0.0）'
    )

    args = parser.parse_args()

    # 加载环境配置
    if not load_environment_config(args.env):
        logger.error("无法加载环境配置，退出")
        sys.exit(1)

    # 设置环境变量标识
    os.environ['ENVIRONMENT'] = args.env

    # 导入应用（必须在配置加载之后）
    from app.main import app

    # 获取端口和地址
    port = args.port if args.port else int(os.environ.get("PORT", 8000))
    host = args.host if args.host else os.environ.get("HOST", "0.0.0.0")

    logger.info("\n启动优丁平台后端服务")
    logger.info("   环境: %s", args.env)
    logger.info("   地址: http://%s:%s", host, port)
    logger.info("   API前缀: %s", os.environ.get('API_PREFIX', '/api/v1'))
    logger.info("   调试模式: %s", os.environ.get('DEBUG', 'false').lower() == 'true')
    logger.info("")

    # 启动服务
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=(args.env == 'dev'),
        workers=1 if args.env == 'dev' else 4
    )

if __name__ == "__main__":
    # Windows multiprocessing fix
    try:
        from multiprocessing import freeze_support
        freeze_support()
    except ImportError:
        pass

    main()
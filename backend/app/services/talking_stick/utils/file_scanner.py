# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
Talking-Stick 文件扫描工具
负责遍历目录和识别风险文件
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

from ..models.scan_result import RiskFile


@dataclass
class FileInfo:
    """文件信息"""
    path: str
    size: int
    file_type: str
    last_modified: datetime
    is_risk: bool = False
    risk_level: str = "low"
    risk_reason: str = ""


class FileScanner:
    """文件扫描器"""
    def __init__(self, exclude_dirs: List[str] = None, exclude_extensions: List[str] = None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param exclude_dirs: 参数 exclude_dirs
        :param exclude_extensions: 参数 exclude_extensions
        :return: 返回处理结果。
        """
        self.exclude_dirs = exclude_dirs or [
            "node_modules", ".git", "__pycache__", ".venv", "dist", "build"
        ]
        self.exclude_extensions = exclude_extensions or [
            ".pyc", ".pyo", ".so", ".dll", ".exe"
        ]
    
    def scan_directory(self, target_path: str, recursive: bool = True) -> List[FileInfo]:
        """扫描目录"""
        target = Path(target_path)
        if not target.exists():
            raise FileNotFoundError(f"目标路径不存在: {target_path}")
        
        files = []
        if target.is_file():
            # 扫描单个文件
            file_info = self._get_file_info(target)
            if file_info:
                files.append(file_info)
        elif target.is_dir():
            # 扫描目录
            if recursive:
                for root, dirs, filenames in os.walk(target):
                    # 过滤排除的目录
                    dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
                    for filename in filenames:
                        filepath = Path(root) / filename
                        file_info = self._get_file_info(filepath)
                        if file_info:
                            files.append(file_info)
            else:
                # 只扫描当前目录
                for filepath in target.iterdir():
                    if filepath.is_file():
                        file_info = self._get_file_info(filepath)
                        if file_info:
                            files.append(file_info)
        
        return files
    
    def _get_file_info(self, filepath: Path) -> Optional[FileInfo]:
        """获取文件信息"""
        try:
            # 检查文件扩展名是否排除
            if filepath.suffix.lower() in self.exclude_extensions:
                return None
            
            # 获取文件信息
            stat = filepath.stat()
            # 识别文件类型
            file_type = self._identify_file_type(filepath)
            # 评估风险级别
            risk_level, risk_reason = self._assess_risk(filepath, file_type)
            return FileInfo(
                path=str(filepath),
                size=stat.st_size,
                file_type=file_type,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                is_risk=risk_level != "low",
                risk_level=risk_level,
                risk_reason=risk_reason
            )
        except (OSError, PermissionError):
            # 无法访问的文件
            return None
    
    def _identify_file_type(self, filepath: Path) -> str:
        """识别文件类型"""
        suffix = filepath.suffix.lower()
        # Python文件
        if suffix == ".py":
            return "python"
        
        # JavaScript/TypeScript文件
        if suffix in [".js", ".jsx", ".ts", ".tsx"]:
            return "javascript"
        
        # 配置文件
        if suffix in [".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"]:
            return "config"
        
        # 文档文件
        if suffix in [".md", ".txt", ".rst"]:
            return "documentation"
        
        # HTML/CSS文件
        if suffix in [".html", ".htm", ".css"]:
            return "web"
        
        # 其他
        return "other"
    
    def _assess_risk(self, filepath: Path, file_type: str) -> tuple:
        """评估文件风险级别"""
        filename = filepath.name.lower()
        path_str = str(filepath).lower()
        # 高风险文件
        high_risk_patterns = [
            "auth", "login", "admin", "user", "session",
            "password", "token", "secret", "key", "credential"
        ]
        for pattern in high_risk_patterns:
            if pattern in filename or pattern in path_str:
                return "high", f"包含敏感关键词: {pattern}"
        
        # 中风险文件
        if file_type == "python" and ("api" in path_str or "route" in path_str):
            return "medium", "API路由文件"
        
        if file_type == "config":
            return "medium", "配置文件"
        
        # 低风险文件
        return "low", ""
    
    def get_risk_files(self, files: List[FileInfo]) -> List[RiskFile]:
        """获取风险文件列表"""
        risk_files = []
        for file_info in files:
            if file_info.is_risk:
                risk_file = RiskFile(
                    path=file_info.path,
                    risk_level=file_info.risk_level,
                    reason=file_info.risk_reason,
                    file_type=file_info.file_type,
                    size=file_info.size,
                    last_modified=file_info.last_modified
                )
                risk_files.append(risk_file)
        
        return risk_files

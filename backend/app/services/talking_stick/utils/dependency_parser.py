# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
Talking-Stick 依赖解析工具
负责解析和分析项目依赖
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

from ..models.scan_result import DependencyInfo


@dataclass
class DependencyFile:
    """依赖文件信息"""
    path: str
    file_type: str  # requirements.txt, package.json, etc.
    dependencies: List[DependencyInfo]


class DependencyParser:
    """依赖解析器"""
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self.parsers = {
            "requirements.txt": self._parse_requirements_txt,
            "package.json": self._parse_package_json,
            "Pipfile": self._parse_pipfile,
            "pyproject.toml": self._parse_pyproject_toml,
        }
    
    def parse_project(self, project_path: str) -> Dict[str, List[DependencyInfo]]:
        """解析项目依赖"""
        project = Path(project_path)
        if not project.exists():
            raise FileNotFoundError(f"项目路径不存在: {project_path}")
        
        dependencies = {}
        # 扫描常见的依赖文件
        dependency_files = [
            "requirements.txt",
            "package.json",
            "Pipfile",
            "pyproject.toml",
        ]
        for dep_file in dependency_files:
            dep_path = project / dep_file
            if dep_path.exists():
                lang, deps = self._parse_dependency_file(dep_path)
                if deps:
                    dependencies[lang] = deps
        
        return dependencies
    
    def _parse_dependency_file(self, filepath: Path) -> tuple:
        """解析依赖文件"""
        filename = filepath.name
        if filename in self.parsers:
            return self.parsers[filename](filepath)
        
        return "unknown", []
    
    def _parse_requirements_txt(self, filepath: Path) -> tuple:
        """解析 requirements.txt"""
        dependencies = []
        try:
            content = filepath.read_text(encoding='utf-8')
            for line in content.splitlines():
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                
                # 解析包名和版本
                if '==' in line:
                    name, version = line.split('==', 1)
                    dependencies.append(DependencyInfo(
                        name=name.strip(),
                        version=version.strip(),
                        known_vulnerabilities=0
                    ))
                elif '>=' in line:
                    name, version = line.split('>=', 1)
                    dependencies.append(DependencyInfo(
                        name=name.strip(),
                        version=f">={version.strip()}",
                        known_vulnerabilities=0
                    ))
                else:
                    # 没有版本约束
                    dependencies.append(DependencyInfo(
                        name=line,
                        version="latest",
                        known_vulnerabilities=0
                    ))
        except Exception as e:
            logger.error("解析 requirements.txt 失败: %s", e)
        
        return "python", dependencies
    
    def _parse_package_json(self, filepath: Path) -> tuple:
        """解析 package.json"""
        dependencies = []
        try:
            content = filepath.read_text(encoding='utf-8')
            data = json.loads(content)
            # 解析 dependencies
            for name, version in data.get('dependencies', {}).items():
                dependencies.append(DependencyInfo(
                    name=name,
                    version=version,
                    known_vulnerabilities=0
                ))
            
            # 解析 devDependencies
            for name, version in data.get('devDependencies', {}).items():
                dependencies.append(DependencyInfo(
                    name=name,
                    version=version,
                    known_vulnerabilities=0
                ))
        except Exception as e:
            logger.error("解析 package.json 失败: %s", e)
        
        return "node", dependencies
    
    def _parse_pipfile(self, filepath: Path) -> tuple:
        """解析 Pipfile"""
        # TODO [P2] 实现 Pipfile 解析（待Phase 2扩展依赖支持）
        return "python", []

    def _parse_pyproject_toml(self, filepath: Path) -> tuple:
        """解析 pyproject.toml"""
        # TODO [P2] 实现 pyproject.toml 解析（待Phase 2扩展依赖支持）
        return "python", []

    def check_known_vulnerabilities(self, dependencies: Dict[str, List[DependencyInfo]]) -> Dict[str, List[DependencyInfo]]:
        """检查已知漏洞"""
        # TODO [P2] 集成漏洞数据库查询（待Phase 2接入漏洞库API）
        return dependencies
    
    def get_dependency_summary(self, dependencies: Dict[str, List[DependencyInfo]]) -> Dict[str, Any]:
        """获取依赖摘要"""
        summary = {
            "total_packages": 0,
            "by_language": {},
            "with_vulnerabilities": 0
        }
        for lang, deps in dependencies.items():
            summary["total_packages"] += len(deps)
            summary["by_language"][lang] = len(deps)
            for dep in deps:
                if dep.known_vulnerabilities > 0:
                    summary["with_vulnerabilities"] += 1
        
        return summary

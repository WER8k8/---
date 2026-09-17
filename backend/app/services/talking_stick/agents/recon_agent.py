# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
Talking-Stick 侦察Agent
负责遍历目录、收集源码、依赖清单，初步标记风险文件
"""

from typing import Any, Dict, List
from pathlib import Path

from .base_agent import BaseAgent
from ..config import ConfigManager
from ..utils.file_scanner import FileScanner
from ..utils.dependency_parser import DependencyParser
from ..utils.rule_engine import RuleEngine


class ReconAgent(BaseAgent):
    """侦察Agent"""
    def __init__(self, config_manager: ConfigManager):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param config_manager: 参数 config_manager
        :return: 返回处理结果。
        """
        super().__init__("recon", config_manager)
        # 初始化工具
        self.file_scanner = None
        self.dependency_parser = None
        self.rule_engine = None
        self._init_tools()
    
    def _init_tools(self) -> None:
        """初始化工具"""
        # 获取扫描配置
        scan_config = self.config_manager.get('scan', {})
        # 初始化文件扫描器
        self.file_scanner = FileScanner(
            exclude_dirs=scan_config.get('exclude_dirs', []),
            exclude_extensions=scan_config.get('exclude_extensions', [])
        )
        # 初始化依赖解析器
        self.dependency_parser = DependencyParser()
        # 初始化规则引擎
        self.rule_engine = RuleEngine()
    
    async def execute(self, target_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行侦察任务"""
        self.log(f"开始侦察 - 目标: {target_path}")
        # 获取文件锁
        lock_id = await self.acquire_file_lock(target_path)
        try:
            # 扫描文件
            files = await self._scan_files(target_path)
            # 解析依赖
            dependencies = await self._parse_dependencies(target_path)
            # 标记风险文件
            risk_files = await self._identify_risk_files(files)
            # 生成侦察结果
            result = self._generate_result(target_path, files, dependencies, risk_files)
            self.log(f"侦察完成 - 文件数: {len(files)}, 风险文件: {len(risk_files)}")
            return result
            
        finally:
            # 释放文件锁
            await self.release_file_lock(lock_id)
    
    async def _scan_files(self, target_path: str) -> List[Dict[str, Any]]:
        """扫描文件"""
        self.log("扫描文件系统...")
        # 使用文件扫描器遍历目录
        files_info = self.file_scanner.scan_directory(target_path)
        # 转换为字典格式
        files = []
        for file_info in files_info:
            path = Path(file_info.path)
            files.append({
                "path": str(file_info.path),
                "relative_path": str(path.relative_to(target_path)) if target_path in file_info.path else path.name,
                "size": file_info.size,
                "type": file_info.file_type,
                "extension": path.suffix.lower(),
                "last_modified": file_info.last_modified.isoformat() if file_info.last_modified else None
            })
        
        return files
    
    async def _parse_dependencies(self, target_path: str) -> List[Dict[str, Any]]:
        """解析依赖"""
        self.log("解析依赖文件...")
        target = Path(target_path)
        dependencies = []
        # 检查Python依赖
        requirements_file = target / "requirements.txt"
        if requirements_file.exists():
            python_deps = self.dependency_parser.parse_requirements_file(str(requirements_file))
            dependencies.extend(python_deps)
        
        # 检查Node.js依赖
        package_json = target / "package.json"
        if package_json.exists():
            node_deps = self.dependency_parser.parse_package_json(str(package_json))
            dependencies.extend(node_deps)
        
        return dependencies
    
    async def _identify_risk_files(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """识别风险文件"""
        self.log("识别风险文件...")
        risk_files = []
        for file_info in files:
            file_path = file_info["path"]
            risk_score = 0
            risk_reasons = []
            # 基于文件类型的风险评估
            file_type = file_info["type"]
            if file_type in ["python", "javascript", "typescript"]:
                risk_score += 20
                risk_reasons.append("源代码文件")
            
            # 基于文件扩展名的风险评估
            extension = file_info["extension"]
            high_risk_extensions = [".py", ".js", ".ts", ".jsx", ".tsx", ".php", ".java", ".go"]
            if extension in high_risk_extensions:
                risk_score += 30
                risk_reasons.append("高风险文件类型")
            
            # 基于文件名的风险评估
            file_name = Path(file_path).name.lower()
            high_risk_patterns = [
                "config", "secret", "key", "password", "auth", "login", "admin",
                "database", "db", "env", ".env", "settings", "credential"
            ]
            for pattern in high_risk_patterns:
                if pattern in file_name:
                    risk_score += 40
                    risk_reasons.append(f"敏感文件名: {pattern}")
                    break
            
            # 基于文件路径的风险评估
            file_path_lower = file_path.lower()
            high_risk_paths = [
                "/api/", "/auth/", "/admin/", "/config/", "/settings/",
                "/database/", "/db/", "/models/", "/controllers/", "/routes/"
            ]
            for path_pattern in high_risk_paths:
                if path_pattern in file_path_lower:
                    risk_score += 25
                    risk_reasons.append(f"敏感路径: {path_pattern}")
                    break
            
            # 如果风险分数超过阈值，标记为风险文件
            if risk_score >= 30:
                risk_files.append({
                    "path": file_path,
                    "relative_path": file_info["relative_path"],
                    "risk_score": risk_score,
                    "risk_reasons": risk_reasons,
                    "size": file_info["size"],
                    "type": file_type
                })
        
        # 按风险分数排序
        risk_files.sort(key=lambda x: x["risk_score"], reverse=True)
        return risk_files
    
    def _generate_result(self, target_path: str, files: List[Dict[str, Any]], 
                        dependencies: List[Dict[str, Any]], 
                        risk_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成侦察结果"""
        # 统计文件类型
        file_types = {}
        for file_info in files:
            file_type = file_info["type"]
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        # 统计依赖类型
        dependency_types = {}
        for dep in dependencies:
            dep_type = dep.get("type", "unknown")
            dependency_types[dep_type] = dependency_types.get(dep_type, 0) + 1
        
        # 计算总文件大小
        total_size = sum(file_info["size"] for file_info in files)
        return {
            "agent_type": "recon",
            "target_path": target_path,
            "timestamp": self.generate_id("recon"),
            "summary": {
                "total_files": len(files),
                "total_size": total_size,
                "risk_files": len(risk_files),
                "total_dependencies": len(dependencies),
                "file_types": file_types,
                "dependency_types": dependency_types
            },
            "files": files,
            "dependencies": dependencies,
            "risk_files": risk_files,
            "recommendations": self._generate_recommendations(risk_files, dependencies)
        }
    
    def _generate_recommendations(self, risk_files: List[Dict[str, Any]], 
                                 dependencies: List[Dict[str, Any]]) -> List[str]:
        """生成建议"""
        recommendations = []
        # 基于风险文件的建议
        if len(risk_files) > 0:
            high_risk_files = [f for f in risk_files if f["risk_score"] >= 60]
            if high_risk_files:
                recommendations.append(f"发现 {len(high_risk_files)} 个高风险文件，建议优先审计")
            
            sensitive_files = [f for f in risk_files if any("敏感" in reason for reason in f["risk_reasons"])]
            if sensitive_files:
                recommendations.append(f"发现 {len(sensitive_files)} 个敏感文件，需要特别关注")
        
        # 基于依赖的建议
        if len(dependencies) > 0:
            recommendations.append(f"发现 {len(dependencies)} 个依赖，建议进行依赖安全扫描")
            # 检查是否有已知漏洞的依赖
            vulnerable_deps = [dep for dep in dependencies if dep.get("vulnerabilities")]
            if vulnerable_deps:
                recommendations.append(f"发现 {len(vulnerable_deps)} 个依赖存在已知漏洞")
        
        # 通用建议
        if not recommendations:
            recommendations.append("未发现明显风险，建议进行深度代码审计")
        
        return recommendations
# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
Talking-Stick 扫描结果数据模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class RiskFile:
    """风险文件信息"""
    path: str
    risk_level: str  # high, medium, low
    reason: str
    file_type: str
    size: int
    last_modified: Optional[datetime] = None


@dataclass
class DependencyInfo:
    """依赖信息"""
    name: str
    version: str
    known_vulnerabilities: int = 0


@dataclass
class ScanSummary:
    """扫描摘要"""
    total_files: int = 0
    high_risk: int = 0
    medium_risk: int = 0
    low_risk: int = 0


@dataclass
class ScanResult:
    """扫描结果"""
    scan_id: str
    timestamp: datetime
    target_path: str
    files_scanned: int = 0
    risk_files: List[RiskFile] = field(default_factory=list)
    dependencies: Dict[str, List[DependencyInfo]] = field(default_factory=dict)
    summary: ScanSummary = field(default_factory=ScanSummary)
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "scan_id": self.scan_id,
            "timestamp": self.timestamp.isoformat(),
            "target_path": self.target_path,
            "files_scanned": self.files_scanned,
            "risk_files": [
                {
                    "path": rf.path,
                    "risk_level": rf.risk_level,
                    "reason": rf.reason,
                    "file_type": rf.file_type,
                    "size": rf.size,
                    "last_modified": rf.last_modified.isoformat() if rf.last_modified else None
                }
                for rf in self.risk_files
            ],
            "dependencies": {
                lang: [
                    {
                        "name": dep.name,
                        "version": dep.version,
                        "known_vulnerabilities": dep.known_vulnerabilities
                    }
                    for dep in deps
                ]
                for lang, deps in self.dependencies.items()
            },
            "summary": {
                "total_files": self.summary.total_files,
                "high_risk": self.summary.high_risk,
                "medium_risk": self.summary.medium_risk,
                "low_risk": self.summary.low_risk
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScanResult':
        """从字典创建实例"""
        risk_files = [
            RiskFile(
                path=rf.get('path', ''),
                risk_level=rf.get('risk_level', 'low'),
                reason=rf.get('reason', ''),
                file_type=rf.get('file_type', ''),
                size=rf.get('size', 0),
                last_modified=datetime.fromisoformat(rf['last_modified']) if rf.get('last_modified') else None
            )
            for rf in data.get('risk_files', [])
        ]
        dependencies = {}
        for lang, deps in data.get('dependencies', {}).items():
            dependencies[lang] = [
                DependencyInfo(
                    name=dep.get('name', ''),
                    version=dep.get('version', ''),
                    known_vulnerabilities=dep.get('known_vulnerabilities', 0)
                )
                for dep in deps
            ]
        
        summary_data = data.get('summary', {})
        summary = ScanSummary(
            total_files=summary_data.get('total_files', 0),
            high_risk=summary_data.get('high_risk', 0),
            medium_risk=summary_data.get('medium_risk', 0),
            low_risk=summary_data.get('low_risk', 0)
        )
        return cls(
            scan_id=data.get('scan_id', ''),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.now(),
            target_path=data.get('target_path', ''),
            files_scanned=data.get('files_scanned', 0),
            risk_files=risk_files,
            dependencies=dependencies,
            summary=summary
        )

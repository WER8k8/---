# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
Talking-Stick 配置管理模块
负责加载和管理配置文件
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """模型配置"""
    provider: str
    model: str
    max_tokens: int
    temperature: float


@dataclass
class FileLockConfig:
    """文件锁配置"""
    lock_dir: str
    timeout: int
    granularity: str


@dataclass
class OutputConfig:
    """输出配置"""
    dir: str
    formats: list
    generate_html: bool
    analyze_dependencies: bool


@dataclass
class TalkingStickConfig:
    """Talking-Stick 主配置"""
    version: str
    models: Dict[str, ModelConfig]
    scan: Dict[str, Any]
    detection: Dict[str, Any]
    file_lock: FileLockConfig
    output: OutputConfig
    integration: Dict[str, Any]


class ConfigManager:
    """配置管理器"""
    def __init__(self, config_path: str = ".talking-stick/config.yaml"):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param config_path: 参数 config_path
        :return: 返回处理结果。
        """
        self.config_path = Path(config_path)
        self._config: Optional[TalkingStickConfig] = None
    
    def load(self) -> TalkingStickConfig:
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)
        
        # 解析模型配置
        models = {}
        for agent_type, model_conf in raw_config.get('models', {}).items():
            models[agent_type] = ModelConfig(
                provider=model_conf.get('provider', 'openai'),
                model=model_conf.get('model', 'gpt-4'),
                max_tokens=model_conf.get('max_tokens', 4096),
                temperature=model_conf.get('temperature', 0.0)
            )
        
        # 解析文件锁配置
        file_lock_conf = raw_config.get('file_lock', {})
        file_lock = FileLockConfig(
            lock_dir=file_lock_conf.get('lock_dir', '.talking-stick-locks'),
            timeout=file_lock_conf.get('timeout', 300),
            granularity=file_lock_conf.get('granularity', 'directory')
        )
        # 解析输出配置
        output_conf = raw_config.get('output', {})
        output = OutputConfig(
            dir=output_conf.get('dir', 'docs'),
            formats=output_conf.get('formats', ['markdown', 'json']),
            generate_html=output_conf.get('generate_html', True),
            analyze_dependencies=output_conf.get('analyze_dependencies', True)
        )
        self._config = TalkingStickConfig(
            version=raw_config.get('version', '1.0.0'),
            models=models,
            scan=raw_config.get('scan', {}),
            detection=raw_config.get('detection', {}),
            file_lock=file_lock,
            output=output,
            integration=raw_config.get('integration', {})
        )
        return self._config
    
    def get_model_config(self, agent_type: str) -> ModelConfig:
        """获取指定Agent的模型配置"""
        if not self._config:
            self.load()
        
        if agent_type not in self._config.models:
            raise ValueError(f"未知的Agent类型: {agent_type}")
        
        return self._config.models[agent_type]
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        if not self._config:
            self.load()
        
        return getattr(self._config, key, default)

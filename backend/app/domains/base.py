# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""领域模块基类 — FIX-31: 模块单体架构

每个领域模块继承此基类，提供统一的接口：
- name: 领域名称
- router: 领域 API 路由（自动注册）
- register_models(): 注册领域数据模型
- get_facade(): 获取领域对外接口
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from fastapi import APIRouter


class DomainModule(ABC):
    """领域模块基类。

    子类必须实现：
    - name: 领域名称（英文标识）
    - label: 领域中文标签
    - router: FastAPI 路由实例
    """
    name: str = ""
    label: str = ""
    @property
    @abstractmethod
    def router(self) -> APIRouter:
        """返回领域的 API 路由。"""
        ...

    @property
    def prefix(self) -> str:
        """路由前缀，默认使用领域名。"""
        return f"/{self.name}"

    @property
    def tags(self) -> list[str]:
        """OpenAPI 标签。"""
        return [self.label]

    def register(self, parent_router: APIRouter) -> None:
        """将领域路由注册到父路由。"""
        parent_router.include_router(
            self.router,
            prefix=self.prefix,
            tags=self.tags,
        )

    def get_facade(self) -> dict:
        """返回领域对外接口的元数据。

        Returns:
            {
                "name": str,
                "label": str,
                "routes": int,
                "models": list[str],
                "services": list[str],
            }
        """
        return {
            "name": self.name,
            "label": self.label,
            "routes": len(self.router.routes) if self.router else 0,
            "models": [],
            "services": [],
        }
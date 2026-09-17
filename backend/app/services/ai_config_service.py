# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI模型配置服务层"""

from typing import Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.ai_config import AIModelConfig, AIModelProvider, AIUsageLog
from app.schemas.ai_config import (AIModelConfigCreate, AIModelConfigUpdate,
                                   AIModelProviderCreate,
                                   AIModelProviderUpdate, AIUsageStatsResponse,
                                   CurrentModelResponse)


class AIConfigService:
    """AI配置服务"""
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    # ============ Provider Operations ============
    def get_provider_by_id(
            self,
            provider_id: str) -> Optional[AIModelProvider]:
        """根据ID获取提供商"""
        return self.db.query(AIModelProvider).filter(
            AIModelProvider.id == provider_id).first()

    def get_provider_by_name(self, name: str) -> Optional[AIModelProvider]:
        """根据名称获取提供商"""
        return self.db.query(AIModelProvider).filter(
            AIModelProvider.name == name).first()

    def list_providers(self, is_active: bool = None) -> List[AIModelProvider]:
        """获取提供商列表"""
        query = self.db.query(AIModelProvider)
        if is_active is not None:
            query = query.filter(AIModelProvider.is_active == is_active)
        return query.order_by(AIModelProvider.created_at.desc()).all()

    def create_provider(self, data: AIModelProviderCreate) -> AIModelProvider:
        """创建提供商"""
        # 检查名称是否已存在
        if self.get_provider_by_name(data.name):
            raise ValueError("提供商名称已存在")

        provider = AIModelProvider(
            name=data.name,
            provider_type=data.provider_type,
            api_key=data.api_key,
            base_url=data.base_url,
            default_model=data.default_model,
            is_active=data.is_active if data.is_active is not None else True,
            is_default=data.is_default if data.is_default is not None else False,
            description=data.description,
        )
        # 如果设为默认，取消其他默认
        if provider.is_default:
            self._clear_default_provider()

        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def update_provider(
            self,
            provider_id: str,
            data: AIModelProviderUpdate) -> Optional[AIModelProvider]:
        """更新提供商"""
        provider = self.get_provider_by_id(provider_id)
        if not provider:
            return None

        update_data = data.model_dump(exclude_unset=True)
        # 检查名称是否与其他提供商冲突
        if "name" in update_data and update_data["name"] != provider.name:
            if self.get_provider_by_name(update_data["name"]):
                raise ValueError("提供商名称已存在")

        # 如果设为默认，取消其他默认
        if "is_default" in update_data and update_data["is_default"]:
            self._clear_default_provider()

        for key, value in update_data.items():
            setattr(provider, key, value)

        self.db.commit()
        self.db.refresh(provider)
        return provider

    def delete_provider(self, provider_id: str) -> bool:
        """删除提供商"""
        provider = self.get_provider_by_id(provider_id)
        if not provider:
            return False

        # 删除关联的模型配置
        self.db.query(AIModelConfig).filter(
            AIModelConfig.provider_id == provider_id).delete()

        self.db.delete(provider)
        self.db.commit()
        return True

    def set_default_provider(
            self,
            provider_id: str) -> Optional[AIModelProvider]:
        """设置默认提供商"""
        provider = self.get_provider_by_id(provider_id)
        if not provider:
            return None

        if not provider.is_active:
            raise ValueError("无法将非活跃提供商设为默认")

        self._clear_default_provider()
        provider.is_default = True
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def _clear_default_provider(self):
        """清除所有默认提供商标记"""
        self.db.query(AIModelProvider).filter(AIModelProvider.is_default).update(
            {AIModelProvider.is_default: False})
        self.db.flush()

    # ============ Model Config Operations ============
    def get_model_config_by_id(
            self, config_id: str) -> Optional[AIModelConfig]:
        """根据ID获取模型配置"""
        return self.db.query(AIModelConfig).filter(
            AIModelConfig.id == config_id).first()

    def list_model_configs(
            self,
            provider_id: str = None,
            model_type: str = None,
            is_active: bool = None) -> List[AIModelConfig]:
        """获取模型配置列表"""
        query = self.db.query(AIModelConfig)
        if provider_id:
            query = query.filter(AIModelConfig.provider_id == provider_id)
        if model_type:
            query = query.filter(AIModelConfig.model_type == model_type)
        if is_active is not None:
            query = query.filter(AIModelConfig.is_active == is_active)

        return query.order_by(AIModelConfig.created_at.desc()).all()

    def create_model_config(self, data: AIModelConfigCreate) -> AIModelConfig:
        """创建模型配置"""
        # 检查提供商是否存在且活跃
        provider = self.get_provider_by_id(data.provider_id)
        if not provider or not provider.is_active:
            raise ValueError("提供商不存在或未激活")

        config = AIModelConfig(
            provider_id=data.provider_id,
            model_name=data.model_name,
            model_type=data.model_type,
            temperature=data.temperature if data.temperature else "0.7",
            max_tokens=data.max_tokens if data.max_tokens else "4096",
            context_window=data.context_window,
            is_active=data.is_active if data.is_active is not None else True,
            is_default=data.is_default if data.is_default is not None else False,
            metadata=data.metadata,
        )
        # 如果设为默认，取消同类型的其他默认
        if config.is_default:
            self._clear_default_model(config.provider_id, config.model_type)

        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def update_model_config(
            self,
            config_id: str,
            data: AIModelConfigUpdate) -> Optional[AIModelConfig]:
        """更新模型配置"""
        config = self.get_model_config_by_id(config_id)
        if not config:
            return None

        update_data = data.model_dump(exclude_unset=True)
        # 如果设为默认，取消同类型的其他默认
        if "is_default" in update_data and update_data["is_default"]:
            self._clear_default_model(config.provider_id, config.model_type)

        for key, value in update_data.items():
            setattr(config, key, value)

        self.db.commit()
        self.db.refresh(config)
        return config

    def delete_model_config(self, config_id: str) -> bool:
        """删除模型配置"""
        config = self.get_model_config_by_id(config_id)
        if not config:
            return False

        self.db.delete(config)
        self.db.commit()
        return True

    def _clear_default_model(self, provider_id: str, model_type: str):
        """清除同提供商同类型的所有默认模型标记"""
        self.db.query(AIModelConfig).filter(
            and_(
                AIModelConfig.provider_id == provider_id,
                AIModelConfig.model_type == model_type,
                AIModelConfig.is_default,
            )
        ).update({AIModelConfig.is_default: False})
        self.db.flush()

    # ============ Current Model Operations ============
    def get_current_model(
            self,
            model_type: str = "general") -> Optional[CurrentModelResponse]:
        """获取当前使用的模型配置"""
        # 优先获取默认提供商的默认模型
        default_provider = (
            self.db.query(AIModelProvider)
            .filter(AIModelProvider.is_default, AIModelProvider.is_active)
            .first()
        )
        if not default_provider:
            # 如果没有默认提供商，获取第一个活跃的提供商
            default_provider = self.db.query(AIModelProvider).filter(
                AIModelProvider.is_active).first()

        if not default_provider:
            return None

        # 获取该提供商下指定类型的默认模型
        default_model = (
            self.db.query(AIModelConfig)
            .filter(
                AIModelConfig.provider_id == default_provider.id,
                AIModelConfig.model_type == model_type,
                AIModelConfig.is_default,
                AIModelConfig.is_active,
            )
            .first()
        )
        if not default_model:
            # 如果没有默认模型，获取第一个活跃的模型
            default_model = (
                self.db.query(AIModelConfig)
                .filter(
                    AIModelConfig.provider_id == default_provider.id,
                    AIModelConfig.model_type == model_type,
                    AIModelConfig.is_active,
                )
                .first()
            )

        if not default_model:
            return None

        return CurrentModelResponse(
            provider_id=default_provider.id,
            provider_name=default_provider.name,
            provider_type=default_provider.provider_type,
            model_name=default_model.model_name,
            model_type=default_model.model_type,
            temperature=default_model.temperature,
            max_tokens=default_model.max_tokens,
        )

    def get_provider_model_config(
            self,
            provider_id: str,
            model_type: str = "general") -> Optional[Dict]:
        """获取指定提供商的模型配置"""
        provider = self.get_provider_by_id(provider_id)
        if not provider or not provider.is_active:
            return None

        model_config = (
            self.db.query(AIModelConfig)
            .filter(
                AIModelConfig.provider_id == provider_id,
                AIModelConfig.model_type == model_type,
                AIModelConfig.is_active,
            )
            .first()
        )
        if not model_config:
            model_config = (
                self.db.query(AIModelConfig) .filter(
                    AIModelConfig.provider_id == provider_id,
                    AIModelConfig.is_active) .first())

        if not model_config:
            return None

        return {
            "provider": {
                "id": provider.id,
                "name": provider.name,
                "type": provider.provider_type,
                "api_key": provider.api_key,
                "base_url": provider.base_url,
                "default_model": provider.default_model,
            },
            "model": {
                "name": model_config.model_name,
                "type": model_config.model_type,
                "temperature": float(model_config.temperature),
                "max_tokens": int(model_config.max_tokens),
            },
        }

    # ============ Usage Log Operations ============
    def log_usage(
        self,
        provider_id: str,
        model_name: str,
        task_type: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        cost: float = 0.0,
        duration_ms: int = 0,
        success: bool = True,
        error_message: str = None,
    ):
        """记录AI使用日志"""
        log = AIUsageLog(
            provider_id=provider_id,
            model_name=model_name,
            task_type=task_type,
            prompt_tokens=str(prompt_tokens),
            completion_tokens=str(completion_tokens),
            total_tokens=str(total_tokens),
            cost=str(cost),
            duration_ms=str(duration_ms),
            success=success,
            error_message=error_message,
        )
        self.db.add(log)
        self.db.commit()

    def get_usage_stats(
            self,
            provider_id: str = None,
            days: int = 30) -> AIUsageStatsResponse:
        """获取使用统计"""
        query = self.db.query(
            func.count(AIUsageLog.id).label("total_requests"),
            func.sum(func.cast(AIUsageLog.total_tokens, int)).label("total_tokens"),
            func.sum(func.cast(AIUsageLog.cost, float)).label("total_cost"),
            func.avg(func.cast(AIUsageLog.duration_ms, int)).label("avg_duration_ms"),
            func.avg(func.cast(AIUsageLog.success, int)).label("success_rate"),
        )
        if provider_id:
            query = query.filter(AIUsageLog.provider_id == provider_id)

        result = query.first()
        return AIUsageStatsResponse(
            total_requests=result.total_requests or 0,
            total_tokens=result.total_tokens or 0,
            total_cost=result.total_cost or 0.0,
            success_rate=(result.success_rate or 0) * 100,
            avg_duration_ms=result.avg_duration_ms or 0.0,
        )

    def get_usage_logs(
            self,
            provider_id: str = None,
            task_type: str = None,
            page: int = 1,
            page_size: int = 50) -> List[AIUsageLog]:
        """获取使用日志列表"""
        query = self.db.query(AIUsageLog)
        if provider_id:
            query = query.filter(AIUsageLog.provider_id == provider_id)
        if task_type:
            query = query.filter(AIUsageLog.task_type == task_type)

        return query.order_by(
            AIUsageLog.created_at.desc()).offset(
            (page - 1) * page_size).limit(page_size).all()

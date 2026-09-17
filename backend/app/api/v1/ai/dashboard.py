# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""AI增强的数据可视化Dashboard API"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success_response
from app.core.logging_config import LogConfig
from app.core.security import get_current_user, optional_auth
from app.services.ai_engine import AIEngine

logger = LogConfig.get_logger("ai_dashboard")

router = APIRouter(prefix="/ai/dashboard", tags=["AI数据可视化"])


class DashboardInsightRequest(BaseModel):
    """Dashboard洞察请求"""
    dashboard_data: Dict[str, Any]
    insight_type: str = "summary"  # summary, anomalies, predictions, recommendations


class AnomalyDetectionRequest(BaseModel):
    """异常检测请求"""
    metric_name: str
    time_series: List[Dict[str, Any]]  # [{"date": "2024-01-01", "value": 100}, ...]
    sensitivity: str = "medium"  # low, medium, high


class TrendPredictionRequest(BaseModel):
    """趋势预测请求"""
    metric_name: str
    time_series: List[Dict[str, Any]]
    prediction_days: int = 30


@router.post("/insights")
async def generate_dashboard_insights(
    request: DashboardInsightRequest,
    db: Session = Depends(get_db),
    current_user=Depends(optional_auth),
):
    """生成Dashboard的AI洞察
    
    为Dashboard数据生成AI洞察，包括：
    - 数据摘要
    - 异常检测
    - 趋势预测
    - 优化建议
    """
    ai_engine = AIEngine()
    if not ai_engine.is_available():
        raise HTTPException(status_code=503, detail="AI服务不可用")
    
    # 构建AI提示词
    prompt = f"""请作为数据分析专家，分析以下Dashboard数据并生成洞察。

Dashboard数据：
```json
{request.dashboard_data}
```

请生成以下类型的洞察（{request.insight_type}）：

1. **数据摘要**（summary）：总结关键指标和变化趋势
2. **异常检测**（anomalies）：识别异常数据点和可能原因
3. **趋势预测**（predictions）：基于历史数据预测未来趋势
4. **优化建议**（recommendations）：提出改进建议和行动计划

请以JSON格式返回结果：
```json
{{
  "insights": [
    {{
      "type": "summary|anomaly|prediction|recommendation",
      "title": "洞察标题",
      "description": "详细描述",
      "severity": "info|warning|critical",
      "metric": "相关指标名称",
      "suggested_action": "建议行动"
    }}
  ],
  "summary": "整体摘要文字"
}}
```"""

    try:
        response = await ai_engine.generate(
            prompt=prompt,
            model="general",
            task_complexity="complex"
        )
        # 解析AI响应
        import json
        import re
        content = response.get("content", "")
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            insights_data = json.loads(json_match.group(0))
            return success_response(data={
                "status": "success",
                "insights": insights_data.get("insights", []),
                "summary": insights_data.get("summary", ""),
                "ai_model": response.get("model", "unknown"),
                "token_usage": response.get("token_usage", 0),
            })
        else:
            logger.warning(f"AI响应中未找到JSON: {content[:200]}")
            return success_response(data={
                "status": "partial",
                "insights": [],
                "summary": content,
                "ai_model": response.get("model", "unknown"),
                "token_usage": response.get("token_usage", 0),
            })
            
    except json.JSONDecodeError as e:
        logger.error(f"解析AI响应JSON失败: {e}")
        raise HTTPException(status_code=500, detail="AI响应解析失败")
    except Exception as e:
        logger.error(f"生成Dashboard洞察失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成洞察失败: {str(e)}")


@router.post("/anomaly-detection")
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(optional_auth),
):
    """检测时间序列数据中的异常
    
    使用AI检测时间序列数据中的异常点，返回异常列表和解释。
    """
    ai_engine = AIEngine()
    if not ai_engine.is_available():
        raise HTTPException(status_code=503, detail="AI服务不可用")
    
    # 构建AI提示词
    prompt = f"""请作为数据分析专家，检测以下时间序列数据中的异常点。

指标名称：{request.metric_name}
敏感度：{request.sensitivity}

时间序列数据：
```json
{request.time_series}
```

请检测以下类型的异常：
1. **点异常**（Point Anomalies）：单个数据点显著偏离
2. **上下文异常**（Contextual Anomalies）：在特定上下文中异常
3. **趋势异常**（Trend Anomalies）：趋势方向或斜率异常变化

请以JSON格式返回结果：
```json
{{
  "anomalies": [
    {{
      "date": "异常日期",
      "value": 异常值,
      "type": "point|contextual|trend",
      "severity": "low|medium|high|critical",
      "description": "异常描述",
      "possible_cause": "可能原因"
    }}
  ],
  "summary": "异常检测摘要"
}}
```"""

    try:
        response = await ai_engine.generate(
            prompt=prompt,
            model="general",
            task_complexity="complex"
        )
        # 解析AI响应
        import json
        import re
        content = response.get("content", "")
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            anomalies_data = json.loads(json_match.group(0))
            return success_response(data={
                "status": "success",
                "metric_name": request.metric_name,
                "anomalies": anomalies_data.get("anomalies", []),
                "summary": anomalies_data.get("summary", ""),
                "ai_model": response.get("model", "unknown"),
                "token_usage": response.get("token_usage", 0),
            })
        else:
            logger.warning(f"AI响应中未找到JSON: {content[:200]}")
            return success_response(data={
                "status": "partial",
                "metric_name": request.metric_name,
                "anomalies": [],
                "summary": content,
                "ai_model": response.get("model", "unknown"),
                "token_usage": response.get("token_usage", 0),
            })
            
    except json.JSONDecodeError as e:
        logger.error(f"解析AI响应JSON失败: {e}")
        raise HTTPException(status_code=500, detail="AI响应解析失败")
    except Exception as e:
        logger.error(f"异常检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"异常检测失败: {str(e)}")


@router.post("/trend-prediction")
async def predict_trend(
    request: TrendPredictionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(optional_auth),
):
    """预测时间序列数据的未来趋势
    
    使用AI分析历史数据并预测未来趋势。
    """
    ai_engine = AIEngine()
    if not ai_engine.is_available():
        raise HTTPException(status_code=503, detail="AI服务不可用")
    
    # 构建AI提示词
    prompt = f"""请作为数据分析专家，分析以下时间序列数据并预测未来趋势。

指标名称：{request.metric_name}
预测天数：{request.prediction_days}天

历史数据：
```json
{request.time_series}
```

请完成以下任务：
1. 分析历史趋势（上升、下降、平稳、季节性等）
2. 预测未来{request.prediction_days}天的趋势
3. 识别关键转折点和事件
4. 提供置信区间

请以JSON格式返回结果：
```json
{{
  "historical_analysis": {{
    "trend": "increasing|decreasing|stable|seasonal",
    "growth_rate": "增长率（百分比）",
    "seasonality": "季节性描述",
    "key_events": ["关键事件1", "关键事件2"]
  }},
  "predictions": [
    {{
      "date": "预测日期",
      "predicted_value": "预测值",
      "confidence_interval": {{
        "lower": "下限",
        "upper": "上限"
      }},
      "trend": "increasing|decreasing|stable"
    }}
  ],
  "summary": "趋势预测摘要"
}}
```"""

    try:
        response = await ai_engine.generate(
            prompt=prompt,
            model="general",
            task_complexity="complex"
        )
        # 解析AI响应
        import json
        import re
        content = response.get("content", "")
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            predictions_data = json.loads(json_match.group(0))
            return success_response(data={
                "status": "success",
                "metric_name": request.metric_name,
                "historical_analysis": predictions_data.get("historical_analysis", {}),
                "predictions": predictions_data.get("predictions", []),
                "summary": predictions_data.get("summary", ""),
                "ai_model": response.get("model", "unknown"),
                "token_usage": response.get("token_usage", 0),
            })
        else:
            logger.warning(f"AI响应中未找到JSON: {content[:200]}")
            return success_response(data={
                "status": "partial",
                "metric_name": request.metric_name,
                "predictions": [],
                "summary": content,
                "ai_model": response.get("model", "unknown"),
                "token_usage": response.get("token_usage", 0),
            })
            
    except json.JSONDecodeError as e:
        logger.error(f"解析AI响应JSON失败: {e}")
        raise HTTPException(status_code=500, detail="AI响应解析失败")
    except Exception as e:
        logger.error(f"趋势预测失败: {e}")
        raise HTTPException(status_code=500, detail=f"趋势预测失败: {str(e)}")


def _build_seo_insights_prompt(dashboard_data, time_range):
    """拼装 SEO 洞察分析提示词。"""
    prompt = f"""请作为SEO专家，分析以下SEO Dashboard数据并提供洞察和建议。

SEO Dashboard数据：
```json
{dashboard_data}
```

时间范围：{time_range}

请提供以下分析：
1. **整体SEO健康度评估**
2. **关键问题识别**（排名下降、流量减少等）
3. **优化建议**（优先级排序）
4. **下一步行动计划**

请以JSON格式返回：
```json
{{
  "health_score": 85,
  "key_issues": ["问题1", "问题2"],
  "recommendations": [
    {{
      "priority": "high|medium|low",
      "action": "行动描述",
      "expected_impact": "预期影响"
    }}
  ],
  "action_plan": ["行动1", "行动2"],
  "summary": "总体评估摘要"
}}
```"""
    return prompt


@router.get("/seo-dashboard-insights")
async def get_seo_dashboard_insights(
    time_range: str = Query("week", alias="range"),
    db: Session = Depends(get_db),
    current_user=Depends(optional_auth),
):
    """获取SEO Dashboard的AI洞察

    自动获取SEO Dashboard数据，生成AI洞察。
    """
    # 导入SEO dashboard函数
    from app.api.v1.seo.dashboard import get_seo_dashboard
    # 获取SEO dashboard数据
    dashboard_response = get_seo_dashboard(time_range, db)
    dashboard_data = dashboard_response.get("data", {})
    # 生成AI洞察
    ai_engine = AIEngine()
    if not ai_engine.is_available():
        # AI不可用时返回基础数据
        return success_response(data={
            "status": "ai_unavailable",
            "dashboard_data": dashboard_data,
            "insights": [],
            "summary": "AI服务不可用，无法生成洞察"
        })

    # 构建AI提示词
    prompt = _build_seo_insights_prompt(dashboard_data, time_range)
    try:
        response = await ai_engine.generate(
            prompt=prompt,
            model="general",
            task_complexity="complex"
        )
        # 解析AI响应
        import json
        import re
        content = response.get("content", "")
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            insights_data = json.loads(json_match.group(0))
            return success_response(data={
                "status": "success",
                "dashboard_data": dashboard_data,
                "health_score": insights_data.get("health_score", 0),
                "key_issues": insights_data.get("key_issues", []),
                "recommendations": insights_data.get("recommendations", []),
                "action_plan": insights_data.get("action_plan", []),
                "summary": insights_data.get("summary", ""),
                "ai_model": response.get("model", "unknown"),
                "token_usage": response.get("token_usage", 0),
            })
        else:
            logger.warning(f"AI响应中未找到JSON: {content[:200]}")
            return success_response(data={
                "status": "partial",
                "dashboard_data": dashboard_data,
                "insights": [],
                "summary": content,
                "ai_model": response.get("model", "unknown"),
                "token_usage": response.get("token_usage", 0),
            })

    except Exception as e:
        logger.error(f"生成SEO洞察失败: {e}")
        return success_response(data={
            "status": "error",
            "dashboard_data": dashboard_data,
            "insights": [],
            "summary": f"生成洞察失败: {str(e)}"
        })

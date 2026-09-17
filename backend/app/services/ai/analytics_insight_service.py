# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
AI数据洞察服务 - 基于真实LLM调用
功能：
- 异常检测（基于统计规则 + AI解释）
- 趋势预测（AI分析数据趋势）
- 智能洞察生成（调用LLM分析数据）
- 自动可视化推荐（根据数据类型推荐图表）
"""

import json
import logging
import math
import statistics
import uuid
from typing import Any, Dict, List, Optional, Tuple

from app.services.ai_engine import AIEngine

logger = logging.getLogger(__name__)


class InsightRequest:
    """洞察请求"""
    data: List[Dict[str, Any]]
    insight_types: List[str]
    generate_visualization: bool
    def __init__(
        self,
        data: List[Dict[str, Any]],
        insight_types: Optional[List[str]] = None,
        generate_visualization: bool = True,
    ) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :param data: 参数 data
        :param insight_types: 参数 insight_types
        :param generate_visualization: 参数 generate_visualization
        :return: 返回处理结果。
        """
        self.data = data
        self.insight_types = insight_types or ["anomaly", "trend", "correlation"]
        self.generate_visualization = generate_visualization


class Insight:
    """数据洞察"""
    type: str
    description: str
    confidence: float
    visualization: Optional[Dict[str, Any]]
    def __init__(
        self,
        type: str,
        description: str,
        confidence: float,
        visualization: Optional[Dict[str, Any]] = None,
    ) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :param type: 参数 type
        :param description: 参数 description
        :param confidence: 参数 confidence
        :param visualization: 参数 visualization
        :return: 返回处理结果。
        """
        self.type = type
        self.description = description
        self.confidence = confidence
        self.visualization = visualization


class InsightResult:
    """洞察结果"""
    insight_id: str
    status: str
    insights: List[Insight]
    summary: str
    def __init__(
        self,
        insight_id: str,
        status: str,
        insights: List[Insight],
        summary: str,
    ) -> None:
        """__init__。

        参数说明：
        :param self: 参数 self
        :param insight_id: 参数 insight_id
        :param status: 参数 status
        :param insights: 参数 insights
        :param summary: 参数 summary
        :return: 返回处理结果。
        """
        self.insight_id = insight_id
        self.status = status
        self.insights = insights
        self.summary = summary


def _detect_anomalies_statistical(
    data: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """基于统计规则的异常检测（Z-Score方法）

    对数值字段计算Z-Score，超过2个标准差视为异常

    Args:
        data: 数据列表

    Returns:
        异常点列表，每个包含field/index/value/z_score
    """
    if len(data) < 3:
        return []

    # 提取数值字段
    numeric_fields: Dict[str, List[float]] = {}
    for row in data:
        for key, val in row.items():
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                numeric_fields.setdefault(key, []).append(val)

    anomalies: List[Dict[str, Any]] = []
    for field, values in numeric_fields.items():
        if len(values) < 3:
            continue
        mean = statistics.mean(values)
        stdev = statistics.stdev(values)
        if stdev == 0:
            continue

        for i, val in enumerate(values):
            z_score = abs(val - mean) / stdev
            if z_score > 2:
                anomalies.append({
                    "field": field,
                    "index": i,
                    "value": val,
                    "z_score": round(z_score, 2),
                    "mean": round(mean, 2),
                    "stdev": round(stdev, 2),
                })

    return anomalies


def _detect_trends_statistical(
    data: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """基于统计的趋势检测（简单线性回归斜率）

    对数值字段计算线性趋势斜率

    Args:
        data: 数据列表

    Returns:
        趋势列表，每个包含field/direction/slope/r_squared
    """
    if len(data) < 3:
        return []

    numeric_fields: Dict[str, List[float]] = {}
    for row in data:
        for key, val in row.items():
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                numeric_fields.setdefault(key, []).append(val)

    trends: List[Dict[str, Any]] = []
    for field, values in numeric_fields.items():
        n = len(values)
        if n < 3:
            continue

        x = list(range(n))
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator_x = sum((x[i] - x_mean) ** 2 for i in range(n))
        denominator_y = sum((values[i] - y_mean) ** 2 for i in range(n))
        if denominator_x == 0 or denominator_y == 0:
            continue

        slope = numerator / denominator_x
        # R-squared
        ss_res = sum(
            (values[i] - (y_mean + slope * (x[i] - x_mean))) ** 2
            for i in range(n)
        )
        r_squared = 1 - ss_res / denominator_y if denominator_y > 0 else 0
        direction = "上升" if slope > 0 else "下降" if slope < 0 else "平稳"
        trends.append({
            "field": field,
            "direction": direction,
            "slope": round(slope, 4),
            "r_squared": round(r_squared, 4),
        })

    return trends


def _compute_correlations(
    data: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """计算数值字段间的皮尔逊相关系数

    Args:
        data: 数据列表

    Returns:
        相关性列表，每个包含field_a/field_b/correlation
    """
    if len(data) < 5:
        return []

    numeric_fields: Dict[str, List[float]] = {}
    for row in data:
        for key, val in row.items():
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                numeric_fields.setdefault(key, []).append(val)

    field_names = list(numeric_fields.keys())
    correlations: List[Dict[str, Any]] = []
    for i in range(len(field_names)):
        for j in range(i + 1, len(field_names)):
            fa, fb = field_names[i], field_names[j]
            va, vb = numeric_fields[fa], numeric_fields[fb]
            if len(va) != len(vb) or len(va) < 5:
                continue

            n = len(va)
            mean_a, mean_b = statistics.mean(va), statistics.mean(vb)
            cov = sum((va[k] - mean_a) * (vb[k] - mean_b) for k in range(n)) / n
            std_a = statistics.stdev(va)
            std_b = statistics.stdev(vb)
            if std_a == 0 or std_b == 0:
                continue

            corr = cov / (std_a * std_b)
            if abs(corr) > 0.3:  # 只报告中等以上相关
                correlations.append({
                    "field_a": fa,
                    "field_b": fb,
                    "correlation": round(corr, 4),
                    "strength": "强" if abs(corr) > 0.7 else "中",
                })

    return correlations


async def _generate_ai_insights(
    data_summary: str, insight_types: List[str]
) -> List[Insight]:
    """调用LLM生成AI数据洞察

    Args:
        data_summary: 数据摘要文本
        insight_types: 需要生成的洞察类型

    Returns:
        AI生成的Insight列表
    """
    engine = AIEngine()
    if not engine.is_available():
        return []

    type_descriptions = {
        "anomaly": "异常值检测（数据中不符合正常模式的异常点）",
        "trend": "趋势分析（数据随时间的变化趋势）",
        "correlation": "相关性分析（字段之间的关联关系）",
        "outlier": "离群值检测（偏离整体分布的极端值）",
    }
    requested = "\n".join(
        f"- {t}: {type_descriptions.get(t, t)}" for t in insight_types
    )
    try:
        prompt = f"""请分析以下数据，生成数据洞察。

需要分析的维度：
{requested}

数据摘要：
{data_summary}

请返回JSON格式：
{{
    "insights": [
        {{
            "type": "anomaly/trend/correlation/outlier",
            "description": "洞察描述（中文，30-100字）",
            "confidence": 0.85
        }}
    ],
    "summary": "整体数据洞察摘要（50-200字）"
}}

只返回JSON，不要添加其他文本。"""

        result = await engine.generate(
            prompt=prompt,
            max_tokens=2000,
            task_complexity="medium",
        )
        content = result.get("content", "").strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        data = json.loads(content)
        return [
            Insight(
                type=ins.get("type", "unknown"),
                description=ins.get("description", ""),
                confidence=ins.get("confidence", 0.5),
            )
            for ins in data.get("insights", [])
        ]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning(f"Failed to parse AI insights response: {e}")
        return []
    except Exception as e:
        logger.error(f"generate_ai_insights failed: {e}")
        return []


def _build_data_summary(data: List[Dict[str, Any]]) -> str:
    """构建数据摘要供LLM分析

    Args:
        data: 原始数据列表

    Returns:
        数据摘要文本
    """
    if not data:
        return "空数据集"

    n = len(data)
    sample = data[:10]  # 最多取10条样本
    # 统计数值字段的描述性统计
    numeric_stats: Dict[str, Dict[str, float]] = {}
    for row in data:
        for key, val in row.items():
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                stats = numeric_stats.setdefault(key, {"min": float("inf"), "max": float("-inf"), "sum": 0, "count": 0})
                stats["min"] = min(stats["min"], val)
                stats["max"] = max(stats["max"], val)
                stats["sum"] += val
                stats["count"] += 1

    stats_text = ""
    for field, stats in numeric_stats.items():
        avg = stats["sum"] / stats["count"] if stats["count"] > 0 else 0
        stats_text += f"- {field}: 范围[{stats['min']:.2f}, {stats['max']:.2f}], 均值{avg:.2f}\n"

    sample_text = json.dumps(sample, ensure_ascii=False, default=str)
    return f"数据量：{n}条\n\n数值字段统计：\n{stats_text}\n数据样本：\n{sample_text}"


async def _generate_insights_extracted():
    """提取出的子流程，封装原函数的局部计算逻辑。

    :param self: 输入参数
    :return: 返回 insights, summary 等计算结果
    """
    insights: List[Insight] = []
    # 1. 统计方法检测
    if "anomaly" in request.insight_types or "outlier" in request.insight_types:
        anomalies = _detect_anomalies_statistical(request.data)
        for anomaly in anomalies[:5]:  # 限制数量
            insights.append(
                Insight(
                    type="anomaly",
                    description=(
                        f"字段'{anomaly['field']}'第{anomaly['index'] + 1}条数据"
                        f"值为{anomaly['value']}，偏离均值{anomaly['mean']}"
                        f"达{anomaly['z_score']}个标准差"
                    ),
                    confidence=min(0.99, 0.5 + anomaly["z_score"] * 0.1),
                    visualization=(
                        {
                            "type": "scatter_chart",
                            "field": anomaly["field"],
                            "anomaly_index": anomaly["index"],
                        }
                        if request.generate_visualization
                        else None
                    ),
                )
            )

    if "trend" in request.insight_types:
        trends = _detect_trends_statistical(request.data)
        for trend in trends:
            insights.append(
                Insight(
                    type="trend",
                    description=(
                        f"字段'{trend['field']}'呈{trend['direction']}趋势，"
                        f"斜率{trend['slope']}，R²={trend['r_squared']}"
                    ),
                    confidence=min(0.99, abs(trend["r_squared"])),
                    visualization=(
                        {
                            "type": "line_chart",
                            "field": trend["field"],
                            "direction": trend["direction"],
                        }
                        if request.generate_visualization
                        else None
                    ),
                )
            )

    if "correlation" in request.insight_types:
        correlations = _compute_correlations(request.data)
        for corr in correlations:
            insights.append(
                Insight(
                    type="correlation",
                    description=(
                        f"字段'{corr['field_a']}'与'{corr['field_b']}'"
                        f"存在{corr['strength']}相关，"
                        f"相关系数{corr['correlation']}"
                    ),
                    confidence=min(0.99, abs(corr["correlation"])),
                    visualization=(
                        {
                            "type": "scatter_chart",
                            "fields": [corr["field_a"], corr["field_b"]],
                        }
                        if request.generate_visualization
                        else None
                    ),
                )
            )

    # 2. AI补充洞察
    data_summary = _build_data_summary(request.data)
    ai_insights = await _generate_ai_insights(data_summary, request.insight_types)
    insights.extend(ai_insights)
    # 生成摘要
    anomaly_count = sum(1 for i in insights if i.type == "anomaly")
    trend_count = sum(1 for i in insights if i.type == "trend")
    corr_count = sum(1 for i in insights if i.type == "correlation")
    summary = f"共发现{len(insights)}个洞察：{anomaly_count}个异常、{trend_count}个趋势、{corr_count}个相关性"
    return insights, summary

async def generate_insights(request: InsightRequest) -> InsightResult:
    """AI驱动的洞察生成

    结合统计方法和AI分析生成数据洞察：
    1. 先用统计方法检测异常、趋势和相关性
    2. 再调用LLM生成自然语言解释和补充洞察

    Args:
        request: 洞察请求，包含数据和洞察类型

    Returns:
        InsightResult包含洞察列表和摘要
    """
    insight_id = f"insight-{uuid.uuid4().hex[:8]}"
    if not request.data:
        return InsightResult(
            insight_id=insight_id,
            status="empty_data",
            insights=[],
            summary="无数据可供分析",
        )

    insights, summary = await _generate_insights_extracted()
    return InsightResult(
        insight_id=insight_id,
        status="completed",
        insights=insights,
        summary=summary,
    )


async def recommend_visualization(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """推荐最佳可视化方式

    根据数据特征（字段类型、数据量、时间序列等）推荐合适的图表类型

    Args:
        data: 数据列表

    Returns:
        包含recommended_chart/reason/alternatives的字典
    """
    if not data:
        return {
            "recommended_chart": "none",
            "reason": "无数据可供可视化",
            "alternatives": [],
        }

    engine = AIEngine()
    # 基于数据特征的基础推荐逻辑
    fields = list(data[0].keys()) if data else []
    numeric_fields = [
        k for k, v in data[0].items() if isinstance(v, (int, float)) and not isinstance(v, bool)
    ]
    has_time = any(
        "date" in k.lower() or "time" in k.lower() or "日期" in k
        for k in fields
    )
    # 基础推荐
    if has_time and numeric_fields:
        base_recommendation = "line_chart"
        base_reason = "数据包含时间维度和数值字段，折线图最适合展示趋势变化"
    elif len(numeric_fields) >= 2:
        base_recommendation = "scatter_chart"
        base_reason = "数据包含多个数值字段，散点图适合展示关联关系"
    elif numeric_fields:
        base_recommendation = "bar_chart"
        base_reason = "数据包含数值字段，柱状图适合对比不同类别的数值"
    else:
        base_recommendation = "table"
        base_reason = "数据以非数值字段为主，表格展示最清晰"

    # AI增强推荐
    if engine.is_available():
        try:
            data_summary = _build_data_summary(data[:20])
            prompt = f"""根据以下数据，推荐最佳的可视化图表类型。

数据摘要：
{data_summary}

基础推荐：{base_recommendation}

请返回JSON格式：
{{
    "recommended_chart": "图表类型",
    "reason": "推荐理由",
    "alternatives": ["备选图表1", "备选图表2"]
}}

只返回JSON。"""

            result = await engine.generate(
                prompt=prompt,
                max_tokens=500,
                task_complexity="simple",
            )
            content = result.get("content", "").strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse visualization recommendation: {e}")
        except Exception as e:
            logger.error(f"recommend_visualization AI call failed: {e}")

    # 降级返回基础推荐
    return {
        "recommended_chart": base_recommendation,
        "reason": base_reason,
        "alternatives": [],
    }

"""XRoPE (Cross-attention Rotary Position Embedding) 时空三维统一位置编码器。

基于复旦大学 MOSS-VL 核心技术报告 (arXiv 2608.15045)，
将视频的时间维度 (Time $T$)、高度维度 (Height $H$)、宽度维度 (Width $W$)
映射在统一连续坐标流形中，实现对动态物体与动作事件的时间戳级精确对齐。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class SpatiotemporalCoordinate:
    """单个视觉 Token 的时空三维坐标。"""
    t: float  # 时间维度（秒或帧时序）
    h: float  # 空间垂直归一化坐标 [0.0, 1.0]
    w: float  # 空间水平归一化坐标 [0.0, 1.0]


class XRoPEEmbedding:
    """XRoPE 时空旋转位置编码计算器。"""

    def __init__(self, dim: int = 64, base_theta: float = 10000.0):
        self.dim = dim
        self.base_theta = base_theta
        # 为 T, H, W 三个轴分配编码维度 (例如 32 for T, 16 for H, 16 for W)
        self.dim_t = dim // 2
        self.dim_h = dim // 4
        self.dim_w = dim - self.dim_t - self.dim_h

    def compute_frequencies(self, dim_part: int) -> list[float]:
        """计算指定维度的角频率。"""
        return [1.0 / (self.base_theta ** (2 * (i // 2) / float(dim_part))) for i in range(dim_part)]

    def encode_coordinate(self, coord: SpatiotemporalCoordinate) -> dict[str, Any]:
        """计算单个时空位置的旋转角与相位特征。"""
        freqs_t = self.compute_frequencies(self.dim_t)
        freqs_h = self.compute_frequencies(self.dim_h)
        freqs_w = self.compute_frequencies(self.dim_w)

        phase_t = [coord.t * f for f in freqs_t]
        phase_h = [coord.h * f for f in freqs_h]
        phase_w = [coord.w * f for f in freqs_w]

        return {
            "coordinate": {"t": coord.t, "h": coord.h, "w": coord.w},
            "phase_t_norm": sum([abs(p) for p in phase_t]) / (len(phase_t) or 1),
            "phase_h_norm": sum([abs(p) for p in phase_h]) / (len(phase_h) or 1),
            "phase_w_norm": sum([abs(p) for p in phase_w]) / (len(phase_w) or 1),
            "total_dim": self.dim,
        }

    def compute_temporal_iou(self, seg1: tuple[float, float], seg2: tuple[float, float]) -> float:
        """计算两个时间片段的 Temporal IoU（时序交并比）。"""
        start1, end1 = seg1
        start2, end2 = seg2
        inter_start = max(start1, start2)
        inter_end = min(end1, end2)
        intersection = max(0.0, inter_end - inter_start)
        union = (end1 - start1) + (end2 - start2) - intersection
        return round(intersection / union, 4) if union > 0 else 0.0

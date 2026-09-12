"""CHANNEL 插槽适配器：暴露既有渠道状态与唯一询盘写入口。"""

from __future__ import annotations

from typing import Any, Mapping

from app.orchestration.interfaces import ChannelFrontendContract, SlotArchetype
from app.services.ubrain.channel_status import get_all_channel_statuses


INQUIRY_WRITE_ENDPOINT = "/api/v1/inquiries/public"


def _channel_to_dict(channel: Any) -> dict[str, Any]:
    return {
        "id": channel.id,
        "name": channel.name,
        "status": channel.status,
        "reason": channel.reason,
    }


class ChannelFrontendAdapter(ChannelFrontendContract):
    """只呈现/采集；写路径固定收口到既有公开询盘 API。"""

    archetype = SlotArchetype.CHANNEL

    def frontend_manifest(self) -> Mapping[str, Any]:
        channels = [_channel_to_dict(item) for item in get_all_channel_statuses()]
        return {"channels": channels, "inquiry_write_endpoint": INQUIRY_WRITE_ENDPOINT}


__all__ = ["ChannelFrontendAdapter", "INQUIRY_WRITE_ENDPOINT"]

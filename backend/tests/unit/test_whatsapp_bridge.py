"""WhatsApp 翻译桥接测试"""
import pytest
from unittest.mock import patch, AsyncMock
from app.services.whatsapp_bridge import WhatsAppBridge


class TestWhatsAppBridge:
    def test_no_base_url_returns_error(self):
        with patch.dict("os.environ", {"WHATSAPP_BRIDGE_URL": ""}):
            bridge = WhatsAppBridge()
        assert bridge.base_url == ""

    @pytest.mark.asyncio
    async def test_send_without_config_returns_error(self):
        with patch.dict("os.environ", {"WHATSAPP_BRIDGE_URL": ""}):
            bridge = WhatsAppBridge()
            result = await bridge.send_message("+8613800000000", "hello")
        assert result["sent"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_send_with_config(self):
        with patch.dict("os.environ", {"WHATSAPP_BRIDGE_URL": "http://bridge:3000"}):
            bridge = WhatsAppBridge()
            mock_resp = AsyncMock(status_code=200)
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__ = AsyncMock(return_value=AsyncMock(post=AsyncMock(return_value=mock_resp)))
                mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
                result = await bridge.send_message("+8613800000000", "hello")
        assert result["sent"] is True
        assert result["phone"] == "+8613800000000"
        assert result["translated"] is False

    @pytest.mark.asyncio
    async def test_send_with_translation_flag(self):
        with patch.dict("os.environ", {"WHATSAPP_BRIDGE_URL": "http://bridge:3000"}):
            bridge = WhatsAppBridge()
            mock_resp = AsyncMock(status_code=200)
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__ = AsyncMock(return_value=AsyncMock(post=AsyncMock(return_value=mock_resp)))
                mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
                result = await bridge.send_message("+8613800000000", "hello", translate_to="es")
        assert result["translated"] is True

    @pytest.mark.asyncio
    async def test_translate_returns_text_unchanged(self):
        bridge = WhatsAppBridge()
        result = await bridge._translate("hello world", "zh")
        assert result == "hello world"

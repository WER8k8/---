"""§3 多平台发帖合规预检单元测试。"""

from __future__ import annotations

from app.services.platform_compliance_checker import (
    PLATFORM_LIMITS,
    list_platform_limits,
    validate_post_content,
)


class TestTwitter:
    def test_over_280_fails(self):
        r = validate_post_content({"text": "x" * 300}, "twitter")
        assert r.valid is False
        assert any("字数超限" in v for v in r.violations)

    def test_within_limit_ok(self):
        r = validate_post_content({"text": "short post #a #b"}, "twitter")
        assert r.valid is True


class TestXiaohongshu:
    def test_external_link_blocked(self):
        r = validate_post_content({"text": "好产品 https://example.com 买它"}, "xiaohongshu")
        assert r.valid is False
        assert any("外链" in v for v in r.violations)

    def test_image_over_9(self):
        r = validate_post_content({"text": "好看", "image_count": 12}, "xiaohongshu")
        assert r.valid is False
        assert any("图片数超限" in v for v in r.violations)


class TestHashtags:
    def test_too_many_hashtags(self):
        text = " ".join(f"#tag{i}" for i in range(40))
        r = validate_post_content({"text": text}, "instagram_caption")
        assert r.valid is False
        assert any("话题标签" in v for v in r.violations)


class TestUnknownPlatform:
    def test_unknown_lenient(self):
        r = validate_post_content({"text": "x" * 99999}, "no_such_platform")
        assert r.valid is True  # 未配置规格按宽松处理
        assert any("未配置" in s for s in r.suggestions)


class TestMeta:
    def test_list_platform_limits(self):
        rows = list_platform_limits()
        assert any(r["platform"] == "weibo" for r in rows)
        assert all("max_chars" in r for r in rows)

    def test_youtube_title_100(self):
        r = validate_post_content({"title": "T" * 120, "text": ""}, "youtube_title")
        assert r.valid is False

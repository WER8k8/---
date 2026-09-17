"""ContentAdapter 单元测试。"""
import pytest
from app.services.content_adapter import ContentAdapter, PLATFORM_SPECS


@pytest.fixture
def adapter():
    return ContentAdapter()


def test_adapt_twitter_truncation(adapter):
    """Twitter 280 字限制截断。"""
    content = "A" * 500 + " #marketing #sales #leads"
    result = adapter.adapt(content, "twitter")

    assert result["adapted"] is True
    assert result["truncated"] is True
    assert len(result["text"]) == 280
    assert result["text"].endswith("...")
    assert result["platform"] == "twitter"
    assert result["image_ratio"] == "16:9"


def test_adapt_no_truncation(adapter):
    """短内容不截断。"""
    content = "Short post #test"
    result = adapter.adapt(content, "twitter")

    assert result["adapted"] is True
    assert result["truncated"] is False
    assert result["text"] == content


def test_adapt_hashtag_extraction(adapter):
    """提取指定数量的标签。"""
    content = "Check this out #marketing #sales #leads #growth #b2b #extra"
    result = adapter.adapt(content, "linkedin")

    assert len(result["hashtags"]) == 5
    assert result["hashtags"] == ["#marketing", "#sales", "#leads", "#growth", "#b2b"]


def test_adapt_unknown_platform(adapter):
    """未知平台返回 adapted=False。"""
    content = "Some content"
    result = adapter.adapt(content, "unknown_platform")

    assert result["adapted"] is False
    assert "未知平台" in result["error"]
    assert result["text"] == content


def test_adapt_instagram_high_hashtag_limit(adapter):
    """Instagram 允许最多 30 个标签。"""
    tags = " ".join(f"#tag{i}" for i in range(35))
    content = f"Post content {tags}"
    result = adapter.adapt(content, "instagram")

    assert len(result["hashtags"]) == 30
    assert result["image_ratio"] == "1:1"


def test_adapt_batch_all_platforms(adapter):
    """批量适配到所有平台。"""
    content = "Test content #test"
    results = adapter.adapt_batch(content)

    assert len(results) == len(PLATFORM_SPECS)
    assert all(r["adapted"] for r in results)


def test_adapt_batch_specific_platforms(adapter):
    """批量适配到指定平台。"""
    content = "Test content"
    results = adapter.adapt_batch(content, platforms=["twitter", "linkedin"])

    assert len(results) == 2
    platforms = {r["platform"] for r in results}
    assert platforms == {"twitter", "linkedin"}


def test_platform_specs_complete():
    """所有平台规格包含必需字段。"""
    required_fields = {"text_limit", "image_ratio", "hashtags"}
    for platform, spec in PLATFORM_SPECS.items():
        assert required_fields.issubset(spec.keys()), f"{platform} 缺少字段"

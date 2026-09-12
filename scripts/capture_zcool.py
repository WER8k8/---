"""截取4个站酷设计参考页面的完整截图"""
import os
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"c:\Users\Administrator.WIN-36O2UQRI3U1\Desktop\上线网站开发完成\上线网站\docs\design-refs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PAGES = [
    ("page1_saas_b2b_flow", "https://www.zcool.com.cn/work/ZNzI0NjUxODg=.html"),
    ("page2_yisa_crm", "https://www.zcool.com.cn/work/ZNzE0NzgyMDQ=.html"),
    ("page3_saas_workbench", "https://www.zcool.com.cn/article/ZMTYzNzkxNg==.html"),
    ("page4_fanpu_backend", "https://www.zcool.com.cn/work/ZNjQyNDYyOTI=.html"),
]

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def capture_page(browser, name, url, idx):
    """截取单个页面的完整内容"""
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        device_scale_factor=1,
    )
    page = context.new_page()

    print(f"\n[{idx}/4] 正在打开: {url}")
    try:
        page.goto(url, wait_until="networkidle", timeout=60000)
    except Exception as e:
        print(f"  警告: 页面加载超时，继续截图... ({e})")

    # 等待内容加载
    time.sleep(3)

    # 关闭可能的弹窗
    try:
        page.evaluate("""() => {
            // 关闭站酷的登录弹窗
            document.querySelectorAll('.close-btn, .modal-close, [class*="close"]').forEach(el => {
                if(el.offsetParent !== null) el.click();
            });
            // 移除悬浮遮罩
            document.querySelectorAll('.fixed-overlay, .modal-backdrop').forEach(el => el.remove());
        }""")
    except:
        pass

    # 获取页面总高度
    total_height = page.evaluate("() => document.body.scrollHeight")
    print(f"  页面总高度: {total_height}px")

    # 分段截取（站酷页面很长，需要分段截图）
    viewport_height = 900
    screenshots = []
    scroll_positions = list(range(0, total_height, viewport_height))

    for i, scroll_y in enumerate(scroll_positions):
        page.evaluate(f"() => window.scrollTo(0, {scroll_y})")
        time.sleep(0.5)
        segment_path = os.path.join(OUTPUT_DIR, f"{name}_segment_{i:03d}.png")
        page.screenshot(path=segment_path)
        screenshots.append(segment_path)

    print(f"  截取了 {len(screenshots)} 段")

    # 同时截取整页截图
    full_path = os.path.join(OUTPUT_DIR, f"{name}_full.png")
    page.screenshot(path=full_path, full_page=True)
    print(f"  整页截图: {full_path}")

    # 提取所有图片URL
    images = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('img')).map(img => ({
            src: img.src,
            alt: img.alt || '',
            width: img.naturalWidth,
            height: img.naturalHeight
        })).filter(i => i.width > 100 && i.height > 100);
    }""")
    print(f"  发现 {len(images)} 张大图")

    # 保存图片URL列表
    import json
    img_list_path = os.path.join(OUTPUT_DIR, f"{name}_images.json")
    with open(img_list_path, "w", encoding="utf-8") as f:
        json.dump(images, f, ensure_ascii=False, indent=2)

    # 提取所有文字内容
    text_content = page.evaluate("""() => {
        // 获取主要内容区域的文字
        const main = document.querySelector('.work-content, .article-content, .content-main, main, .main-content') || document.body;
        return main.innerText;
    }""")
    text_path = os.path.join(OUTPUT_DIR, f"{name}_text.txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text_content)
    print(f"  文字内容: {text_path} ({len(text_content)} 字)")

    context.close()
    return screenshots, images

def main():
    print("=" * 60)
    print("站酷设计参考页面完整截图工具")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=True,
            args=["--no-sandbox", "--disable-gpu"]
        )

        all_results = {}
        for idx, (name, url) in enumerate(PAGES, 1):
            screenshots, images = capture_page(browser, name, url, idx)
            all_results[name] = {
                "url": url,
                "segments": len(screenshots),
                "images_count": len(images),
            }

        browser.close()

    print("\n" + "=" * 60)
    print("截图完成！汇总：")
    print("=" * 60)
    for name, info in all_results.items():
        print(f"  {name}: {info['segments']}段截图, {info['images_count']}张大图")
    print(f"\n所有文件保存在: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()

"""
Task 2 — Crawl bài báo về nghệ sĩ liên quan tới ma tuý.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài báo từ các trang tin tức Việt Nam.
    2. Sử dụng Crawl4AI (ưu tiên) hoặc requests+regex (fallback).
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata (url, title, date_crawled, content).

Cài đặt:
    pip install crawl4ai
    playwright install chromium
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

# Danh sách URL bài báo về nghệ sĩ Việt Nam liên quan tới ma tuý (do người dùng cung cấp)
ARTICLE_URLS = [
    "https://nld.com.vn/ca-si-miu-le-bi-khoi-to-tam-giam-ve-toi-to-chuc-su-dung-trai-phep-chat-ma-tuy-196260516215034895.htm",
    "https://vietnamnet.vn/de-nghi-truy-to-ca-si-chi-dan-cung-anh-trai-vi-to-chuc-su-dung-ma-tuy-2434484.html",
    "https://dantri.com.vn/phap-luat/nguoi-mau-an-tay-ru-ban-va-tro-ly-cung-su-dung-ma-tuy-20260406152426197.htm",
    "https://vietnamnet.vn/ngoai-nguyen-cong-tri-nhung-nghe-si-nao-tung-bi-bat-vi-ma-tuy-2424971.html",
    "https://tuoitre.vn/rapper-binh-gold-duong-tinh-ma-tuy-khi-lai-xe-co-dau-hieu-gay-roi-trat-tu-cong-cong-20250724080230866.htm",
]


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Thu muc: {DATA_DIR}")


def crawl_article_requests(url: str) -> dict:
    """
    Crawl bằng requests với nhiều header hơn để tránh bị block.
    """
    import requests

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    })

    resp = session.get(url, timeout=20, allow_redirects=True)
    resp.encoding = "utf-8"
    html = resp.text

    # Kiểm tra nếu bị redirect về trang chủ hoặc trang 404
    is_404 = any(kw in html[:3000] for kw in [
        "404", "không tìm thấy", "Không tìm thấy", "Page not found",
        "trang không tồn tại", "Trang không tồn tại"
    ])

    # Trích title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else "Unknown"
    # Làm sạch HTML entities
    title = re.sub(r"&amp;", "&", title)
    title = re.sub(r"&lt;", "<", title)
    title = re.sub(r"&gt;", ">", title)
    title = re.sub(r"&#\d+;", "", title)
    title = title.split("|")[0].split(" - ")[0].strip()

    # Trích nội dung - ưu tiên các thẻ article/main/p
    # Xóa script, style, nav, header, footer
    body = re.sub(r"<(script|style|nav|header|footer|aside)[^>]*>.*?</\1>",
                  " ", html, flags=re.DOTALL | re.IGNORECASE)
    # Lấy đoạn văn trong thẻ <p>
    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", body, re.DOTALL | re.IGNORECASE)
    paragraphs_clean = []
    for p in paragraphs:
        # Xóa HTML tags bên trong
        text = re.sub(r"<[^>]+>", "", p)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > 50:  # Chỉ giữ đoạn có ý nghĩa
            paragraphs_clean.append(text)

    content = "\n\n".join(paragraphs_clean[:30])  # Lấy tối đa 30 đoạn

    if not content or len(content) < 100:
        # Fallback: lấy toàn bộ text
        text = re.sub(r"<[^>]+>", " ", body)
        text = re.sub(r"\s+", " ", text).strip()
        content = text[:5000]

    content_markdown = f"# {title}\n\n**Nguon:** {url}\n\n---\n\n{content}"

    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": content_markdown,
        "crawl_method": "requests",
        "is_404": is_404,
    }


async def crawl_article_crawl4ai(url: str) -> dict:
    """
    Crawl bằng Crawl4AI (dùng Playwright browser headless).
    Cần chạy: playwright install chromium
    """
    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(url=url)

        title = "Unknown"
        if hasattr(result, "metadata") and result.metadata:
            title = result.metadata.get("title", "Unknown")
        if (title == "Unknown" or not title) and result.markdown:
            first_line = result.markdown.strip().splitlines()[0]
            title = first_line.lstrip("#").strip()[:150]

        return {
            "url": url,
            "title": title,
            "date_crawled": datetime.now().isoformat(),
            "content_markdown": result.markdown or "",
            "crawl_method": "crawl4ai",
            "is_404": False,
        }


async def crawl_article(url: str) -> dict:
    """
    Crawl một bài báo — thử Crawl4AI trước, fallback sang requests.
    """
    try:
        return await crawl_article_crawl4ai(url)
    except Exception as e1:
        print(f"    [Crawl4AI failed: {type(e1).__name__}] -> fallback requests...")
        return crawl_article_requests(url)


async def crawl_all():
    """Crawl toàn bộ bài báo trong ARTICLE_URLS."""
    setup_directory()

    success = 0
    failed = 0
    skipped_404 = 0

    print(f"\nBat dau crawl {len(ARTICLE_URLS)} bai bao...\n")

    saved_index = 1
    for i, url in enumerate(ARTICLE_URLS, 1):
        print(f"[{i}/{len(ARTICLE_URLS)}] {url}")
        try:
            article = await crawl_article(url)

            if article.get("is_404"):
                print(f"  [SKIP] URL bi 404/redirect - bo qua")
                skipped_404 += 1
                continue

            filename = f"article_{saved_index:02d}.json"
            filepath = DATA_DIR / filename
            filepath.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            method = article.get("crawl_method", "?")
            content_len = len(article.get("content_markdown", ""))
            print(f"  [OK] {filename} | [{method}] | {content_len} chars | {article['title'][:60]}")
            success += 1
            saved_index += 1

            await asyncio.sleep(1.5)

        except Exception as e:
            print(f"  [FAIL] Loi: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Ket qua: {success} thanh cong | {failed} loi | {skipped_404} bi 404")

    if success >= 5:
        print("[PASS] Du >= 5 bai bao!")
    else:
        print(f"[WARN] Can them {5 - success} bai nua.")


if __name__ == "__main__":
    asyncio.run(crawl_all())

"""
Task 3 — Convert toàn bộ file trong data/landing/ thành Markdown.

Sử dụng MarkItDown của Microsoft:
    https://github.com/microsoft/markitdown

Cài đặt:
    pip install markitdown

Hướng dẫn:
    1. Scan toàn bộ file trong data/landing/ (PDF, DOCX, JSON)
    2. Convert sang Markdown
    3. Làm sạch dữ liệu (xóa nav menu, quảng cáo, boilerplate)
    4. Lưu vào data/standardized/ giữ nguyên cấu trúc thư mục
"""

import json
import re
from pathlib import Path

from markitdown import MarkItDown

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


# ---------------------------------------------------------------------------
# Hàm làm sạch Markdown cho bài báo
# ---------------------------------------------------------------------------

def clean_markdown(text: str) -> str:
    """
    Làm sạch nội dung Markdown crawled từ báo điện tử:
    - Xóa các dòng chỉ là Markdown link: [text](url)
    - Xóa bullet list toàn link (menu điều hướng)
    - Xóa các dòng chứa URL ảnh/icon (static, cdn, svg)
    - Xóa các dòng boilerplate (Copyright, hotline, social share, ...)
    - Chuẩn hóa khoảng trắng thừa
    """

    lines = text.splitlines()
    cleaned = []

    # Regex phát hiện dòng chỉ là một Markdown link
    ONLY_LINK = re.compile(r"^\s*\[.*?\]\(https?://[^\)]+\)\s*$")
    # Regex phát hiện bullet list item chứa link
    BULLET_LINK = re.compile(r"^\s*[\*\-]\s+\[.*?\]\(https?://[^\)]+\)\s*$")
    # Dòng chứa CDN/static asset (ảnh, icon svg)
    ASSET_LINE = re.compile(
        r"(cdn|static|mediacdn|vnncdn|staticfile|logo|icon|loading\.svg|avatar)",
        re.IGNORECASE,
    )
    # Dòng boilerplate (hotline, copyright, email tòa soạn, social buttons)
    BOILERPLATE = re.compile(
        r"(HOTLINE|hotline|\bFax\b|Điện thoại:|Email:|Tổng biên tập|"
        r"Cơ quan chủ quản|Giấy phép|Tải ứng dụng|Theo dõi chúng tôi|"
        r"Bản quyền|All rights reserved|Đặt báo|Rao vặt|"
        r"Đăng nhập|Đăng xuất|Lịch sử giao dịch|Cài đặt tài khoản|"
        r"Chia sẻ|Sao chép liên kết|Lưu bài|Xem nhiều|Podcast|YouTube|"
        r"Google News|Apple Store|Google Play|Liên hệ quảng cáo|"
        r"Liên hệ tòa soạn|Trụ sở chính|Thông tin toà soạn|"
        r"Tặng sao|Tặng cho tác giả|Bạn đang có|Gửi bình luận|"
        r"Bình luận \(|Xem tất cả bình luận|Tối đa:.*ký tự|"
        r"Trở thành người đầu tiên|Được quan tâm nhất|Mới nhất|"
        r"Hiện chưa có bình luận|Xin chào,|Tất cả chuyên mục|"
        r"Đóng menu|Vào trang|Thoát trang|Tin đọc nhiều|"
        r"Tin cùng chuyên mục|Có thể bạn quan tâm|Thông tin doanh nghiệp)",
        re.IGNORECASE,
    )
    # Dòng chứa javascript: (inline JS handler)
    JS_LINE = re.compile(r"javascript:", re.IGNORECASE)
    # Dòng breadcrumb / category nav (nhiều link phân tách bằng >)
    BREADCRUMB = re.compile(r"\[.+?\]\(.+?\)\s*(>|·|\|)\s*\[.+?\]\(.+?\)")

    # Đếm consecutive blank lines để giới hạn
    blank_count = 0

    for line in lines:
        stripped = line.strip()

        # Bỏ dòng trống liên tiếp (giữ tối đa 1)
        if stripped == "":
            blank_count += 1
            if blank_count <= 1:
                cleaned.append("")
            continue
        blank_count = 0

        # Bỏ dòng chứa javascript:
        if JS_LINE.search(stripped):
            continue

        # Bỏ dòng chỉ là một link markdown
        if ONLY_LINK.match(stripped):
            continue

        # Bỏ bullet list item toàn link (menu nav)
        if BULLET_LINK.match(stripped):\
            continue

        # Bỏ bullet "Xem thêm..." (menu collapse)
        if re.match(r"^\s*[\*\-\+]\s*(Xem thêm\.{0,3}|Đóng\s*)$", stripped, re.IGNORECASE):
            continue

        # Bỏ dòng quá ngắn kiểu UI fragment (x1, x5, x10, Đóng, ...)
        if re.match(r"^\s*(x\d+|Đóng|Đóng \w*)\s*$", stripped, re.IGNORECASE):
            continue

        # Bỏ dòng chứa CDN/asset (logo, icon, ảnh nav)
        # Chỉ áp dụng nếu dòng KHÔNG có nội dung text thực sự bên cạnh
        if ASSET_LINE.search(stripped) and re.match(r"^\s*!?\[.*?\]\(https?://.*?\)\s*$", stripped):
            continue

        # Bỏ dòng boilerplate
        if BOILERPLATE.search(stripped):
            continue

        # Bỏ breadcrumb / navigation trail
        if BREADCRUMB.search(stripped):
            continue

        # Bỏ dòng quá ngắn chỉ có ký tự đặc biệt (----, ====, ...)
        if re.match(r"^[-=*_]{3,}\s*$", stripped):
            # Giữ lại nếu là separator hợp lệ (ngay sau header)
            if cleaned and cleaned[-1].strip().startswith("#"):
                cleaned.append(line)
            continue

        cleaned.append(line)

    # Loại bỏ khoảng trắng ở đầu và cuối
    result = "\n".join(cleaned).strip()

    # ── TRÍCH XUẤT PHẦN THÂN BÀI CHÍNH ──
    # Tìm heading đầu tiên thực sự (# hoặc ##) để cắt phần header/nav trước nó
    # Nhưng chỉ áp dụng nếu trước heading có nhiều hơn 3 dòng (tức là có nav thật)
    heading_match = re.search(r"^#{1,2} .+", result, re.MULTILINE)
    if heading_match:
        lines_before = result[: heading_match.start()].count("\n")
        if lines_before > 3:
            result = result[heading_match.start():]

    # Cắt phần cuối khi gặp các section footer/comment
    TAIL_MARKERS = re.compile(
        r"\n(Chủ đề:|Tags:|Bình luận \(|Xem các bình luận|"
        r"Đọc nhiều trong|Tin liên quan|Tin mới|Dòng sự kiện|"
        r"Tuổi Trẻ Online Newsletters|Đăng ký email|"
        r"Thông tin của bạn|Vui lòng nhập|Ý kiến của bạn sẽ|"
        r"Địa chỉ: \d|Phòng Quảng Cáo|© \d{4}|"
        r"Chuyển sao tặng|Hoặc nhập số sao|Bạn đã tặng)",
        re.IGNORECASE,
    )
    tail = TAIL_MARKERS.search(result)
    if tail:
        result = result[: tail.start()].strip()

    # Xóa các block liên tiếp chỉ toàn heading nhỏ + link (related articles)
    result = re.sub(
        r"(###\s+\[.+?\]\(https?://.+?\)\n)+",
        "",
        result,
    )

    # Xóa "Xem thêm..." standalone
    result = re.sub(r"\n\s*Xem thêm\.{0,3}\s*\n", "\n", result)

    # Xóa dòng caption ảnh dạng "... - Ảnh: X.Y."
    result = re.sub(r"\n[^\n]{5,80} - Ảnh: [A-Z]\.[A-Z]\.\s*\n", "\n", result)

    # Thu gọn 3+ dòng trống thành 1
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result


# ---------------------------------------------------------------------------
# Convert functions
# ---------------------------------------------------------------------------

def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not legal_dir.exists():
        print("  ⚠ Thư mục data/landing/legal/ không tồn tại.")
        return 0

    md = MarkItDown()
    count = 0

    for filepath in legal_dir.iterdir():
        if filepath.suffix.lower() in (".pdf", ".docx", ".doc"):
            print(f"  Converting: {filepath.name} ...", end=" ", flush=True)
            try:
                result = md.convert(str(filepath))
                output_path = output_dir / f"{filepath.stem}.md"
                output_path.write_text(result.text_content, encoding="utf-8")
                size_kb = len(result.text_content) // 1024
                print(f"✓ ({size_kb} KB) → {output_path.name}")
                count += 1
            except Exception as e:
                print(f"✗ Lỗi: {e}")

    return count


def convert_news_articles():
    """Convert JSON crawled articles trong data/landing/news/ sang markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not news_dir.exists():
        print("  ⚠ Thư mục data/landing/news/ không tồn tại.")
        return 0

    count = 0

    for filepath in news_dir.iterdir():
        if filepath.suffix.lower() == ".json":
            print(f"  Converting: {filepath.name} ...", end=" ", flush=True)
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                output_path = output_dir / f"{filepath.stem}.md"

                # Metadata header
                title = data.get("title", "Unknown")
                url = data.get("url", "N/A")
                date_crawled = data.get("date_crawled", "N/A")
                raw_content = data.get("content_markdown", "")

                # ── LÀM SẠCH NỘI DUNG ──
                clean_content = clean_markdown(raw_content)

                header = f"# {title}\n\n"
                header += f"**Nguồn:** {url}\n"
                header += f"**Ngày crawl:** {date_crawled}\n\n"
                header += "---\n\n"

                full_content = header + clean_content
                output_path.write_text(full_content, encoding="utf-8")

                raw_kb = len(raw_content) // 1024
                clean_kb = len(clean_content) // 1024
                reduction = 100 - int(clean_kb / max(raw_kb, 1) * 100)
                print(f"✓ ({raw_kb}KB → {clean_kb}KB, -{reduction}%) → {output_path.name}")
                count += 1
            except Exception as e:
                print(f"✗ Lỗi: {e}")

    return count


def convert_all():
    """Convert toàn bộ files."""
    print("=" * 55)
    print("Task 3: Convert to Markdown (MarkItDown + Clean)")
    print("=" * 55)

    print("\n--- Legal Documents ---")
    legal_count = convert_legal_docs()

    print("\n--- News Articles ---")
    news_count = convert_news_articles()

    total = legal_count + news_count
    print("\n" + "=" * 55)
    print(f"✓ Đã convert {total} file ({legal_count} luật + {news_count} báo)")
    print(f"✓ Output tại: {OUTPUT_DIR}")

    if total > 0:
        print("✅ PASS — Task 3 hoàn thành!")
    else:
        print("⚠ Chưa có file nào được convert.")


if __name__ == "__main__":
    convert_all()

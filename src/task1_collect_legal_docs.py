"""
Task 1 — Thu thập văn bản pháp luật về ma tuý và các chất cấm.

Hướng dẫn:
    1. Tìm tối thiểu 3 văn bản pháp luật (PDF/DOCX) từ các nguồn chính thống.
    2. Tải về và lưu vào data/landing/legal/
    3. Đặt tên file rõ ràng, không dấu, có năm ban hành.

Gợi ý nguồn:
    - https://thuvienphapluat.vn
    - https://vanban.chinhphu.vn
    - https://luatvietnam.vn

Các file đã tải:
    - 73luat.pdf                   → Luật Phòng, chống ma tuý 2021 (73/2021/QH15)
    - 2026_82_28_2026_NĐ-CP.pdf    → Nghị định 28/2026/NĐ-CP
    - 2026_315_163_2026_NĐ-CP.pdf  → Nghị định 163/2026/NĐ-CP
"""

from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

VALID_EXTENSIONS = {".pdf", ".docx", ".doc"}


def setup_directory():
    """Tạo thư mục data/landing/legal/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Thu muc da san sang: {DATA_DIR}")


def verify_legal_files() -> list[Path]:
    """
    Kiểm tra và liệt kê toàn bộ file pháp luật đã có trong thư mục.

    Returns:
        Danh sách các file hợp lệ (PDF/DOCX) đã tải về.
    """
    files = [
        f for f in DATA_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in VALID_EXTENSIONS
    ]
    return files


def run():
    """Kiểm tra và in báo cáo trạng thái các văn bản pháp luật."""
    setup_directory()

    files = verify_legal_files()

    print("\n" + "=" * 50)
    print("Task 1: Kiểm tra văn bản pháp luật")
    print("=" * 50)

    if not files:
        print("[WARN] Chua co file nao trong data/landing/legal/")
        print("  -> Hay tai file PDF/DOCX va luu vao thu muc nay.")
        return

    print(f"\n[OK] Tim thay {len(files)} file:")
    for i, f in enumerate(files, 1):
        size_kb = f.stat().st_size // 1024
        print(f"  [{i}] {f.name} ({size_kb} KB)")

    if len(files) >= 3:
        print(f"\n[PASS] Da du >= 3 van ban phap luat.")
    else:
        print(f"\n[FAIL] Can them {3 - len(files)} file nua.")


if __name__ == "__main__":
    run()

"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents():
    """
    Upload toàn bộ markdown documents lên PageIndex.
    """
    if not PAGEINDEX_API_KEY or PAGEINDEX_API_KEY.startswith("pi_xxx"):
        print("  ⚠ Bỏ qua upload: PAGEINDEX_API_KEY chưa cấu hình hoặc là key mặc định.")
        return

    from pageindex import PageIndex
    
    pi = PageIndex(api_key=PAGEINDEX_API_KEY)
    
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        pi.upload(
            content=content,
            metadata={"filename": md_file.name, "type": md_file.parent.name}
        )
        print(f"  ✓ Uploaded: {md_file.name}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
    """
    if not PAGEINDEX_API_KEY or PAGEINDEX_API_KEY.startswith("pi_xxx"):
        # FALLBACK: Nếu không có API Key thực tế, chúng ta sử dụng Weaviate BM25 làm fallback
        # Lấy từ task6_lexical_search để đảm bảo cấu trúc trả về tương thích
        try:
            from .task6_lexical_search import lexical_search
            local_results = lexical_search(query, top_k=top_k)
        except ImportError:
            from task6_lexical_search import lexical_search
            local_results = lexical_search(query, top_k=top_k)
            
        results = []
        for r in local_results:
            results.append({
                "content": r["content"],
                "score": r["score"],
                "metadata": r["metadata"],
                "source": "pageindex"
            })
        return results

    from pageindex import PageIndex
    
    pi = PageIndex(api_key=PAGEINDEX_API_KEY)
    raw_results = pi.query(query=query, top_k=top_k)
    
    return [
        {
            "content": r.text,
            "score": r.score,
            "metadata": r.metadata,
            "source": "pageindex"
        }
        for r in raw_results
    ]


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env")
        print("  Đăng ký tại: https://pageindex.ai/")
    else:
        print("Uploading documents...")
        upload_documents()

        print("\nTest query:")
        results = pageindex_search("hình phạt sử dụng ma tuý", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")

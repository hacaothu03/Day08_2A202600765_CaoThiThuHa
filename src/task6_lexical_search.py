"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25
"""

import weaviate
from weaviate.classes.query import MetadataQuery

# Dummy CORPUS to match template requirements if needed
CORPUS: list[dict] = []


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.
    Lưu ý: Vì sử dụng Weaviate BM25 built-in, cơ chế index đã được thực hiện
    tự động khi nạp dữ liệu ở Task 4. Hàm này được giữ lại để tương thích cấu trúc.
    """
    pass


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng Weaviate BM25 built-in search.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score từ Weaviate
            'metadata': dict
        }
        Sorted by score descending.
    """
    from weaviate.classes.init import AdditionalConfig, Timeout

    # Kết nối tới local Weaviate và thực hiện BM25 search với timeout cấu hình tăng cường
    with weaviate.connect_to_local(
        additional_config=AdditionalConfig(timeout=Timeout(init=10, query=30, insert=30))
    ) as client:
        collection = client.collections.get("DrugLawDocs")
        
        results = collection.query.bm25(
            query=query,
            limit=top_k,
            return_metadata=MetadataQuery(score=True)
        )
        
        formatted_results = []
        for obj in results.objects:
            score = obj.metadata.score if obj.metadata.score is not None else 0.0
            formatted_results.append({
                "content": obj.properties.get("content", ""),
                "score": float(score),
                "metadata": {
                    "source": obj.properties.get("source", ""),
                    "doc_type": obj.properties.get("doc_type", ""),
                    "chunk_index": obj.properties.get("chunk_index", 0)
                }
            })
            
    # Sắp xếp kết quả giảm dần theo điểm số score
    formatted_results.sort(key=lambda x: x["score"], reverse=True)
    return formatted_results[:top_k]


if __name__ == "__main__":
    # Test thử nghiệm tìm kiếm từ khóa
    results = lexical_search("Điều 248 tàng trữ trái phép chất ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")

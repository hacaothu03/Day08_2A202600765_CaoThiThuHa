"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""

import os
from dotenv import load_dotenv
import weaviate
from weaviate.classes.query import MetadataQuery
from openai import OpenAI

# Load cấu hình
load_dotenv()

# Sử dụng chung cấu hình Embedding model với Task 4
EMBEDDING_MODEL = "text-embedding-3-small"


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score
            'metadata': dict     # source, doc_type, chunk_index
        }
        Sorted by score descending.
    """
    # Lấy API Key và kết nối
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY không tồn tại trong môi trường hoặc file .env")

    # Tạo query embedding qua OpenAI API
    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(
        input=[query],
        model=EMBEDDING_MODEL
    )
    query_vector = response.data[0].embedding

    from weaviate.classes.init import AdditionalConfig, Timeout

    # Kết nối đến local Weaviate và thực hiện near_vector search với timeout cấu hình tăng cường
    with weaviate.connect_to_local(
        additional_config=AdditionalConfig(timeout=Timeout(init=10, query=30, insert=30))
    ) as weaviate_client:
        collection = weaviate_client.collections.get("DrugLawDocs")
        
        # Query
        results = collection.query.near_vector(
            near_vector=query_vector,
            limit=top_k,
            return_metadata=MetadataQuery(distance=True)
        )
        
        # Định dạng và trả về kết quả
        formatted_results = []
        for obj in results.objects:
            # Weaviate distance = 1 - similarity cho cosine metric
            distance = obj.metadata.distance if obj.metadata.distance is not None else 1.0
            score = 1.0 - distance
            
            formatted_results.append({
                "content": obj.properties.get("content", ""),
                "score": score,
                "metadata": {
                    "source": obj.properties.get("source", ""),
                    "doc_type": obj.properties.get("doc_type", ""),
                    "chunk_index": obj.properties.get("chunk_index", 0)
                }
            })
            
    # Đảm bảo sắp xếp giảm dần theo điểm số score
    formatted_results.sort(key=lambda x: x["score"], reverse=True)
    return formatted_results[:top_k]


if __name__ == "__main__":
    # Test thử nghiệm
    results = semantic_search("hình phạt cho tội tàng trữ ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")

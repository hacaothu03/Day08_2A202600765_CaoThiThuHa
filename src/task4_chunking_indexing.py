"""
Task 4 — Chunking & Indexing vào Vector Store.

Hướng dẫn:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chọn 1 chunking strategy (giải thích lý do)
    3. Chọn 1 embedding model (giải thích lý do)
    4. Index vào vector store (Weaviate khuyến cáo)

Chunking options (langchain-text-splitters):
    - RecursiveCharacterTextSplitter: an toàn, phổ biến
    - MarkdownHeaderTextSplitter: tốt cho file có heading
    - SemanticChunker: dùng embedding để tách (nâng cao)

Embedding model options:
    - sentence-transformers/all-MiniLM-L6-v2 (384 dim, nhẹ)
    - BAAI/bge-m3 (1024 dim, multilingual, tốt cho tiếng Việt)
    - OpenAI text-embedding-3-small (1536 dim, API)

Vector store options:
    - Weaviate (khuyến cáo: hỗ trợ hybrid search built-in)
    - ChromaDB (đơn giản, local)
    - FAISS (chỉ dense search)

Cài đặt:
    pip install langchain-text-splitters sentence-transformers weaviate-client
"""

from pathlib import Path

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn của bạn trong comment
# =============================================================================

# CHUNK_SIZE = 500: Chọn 500 vì độ dài này vừa đủ để chứa ngữ cảnh hoàn chỉnh của các điều khoản luật phòng chống ma túy
# cũng như các đoạn văn tin tức mà không làm loãng thông tin khi đưa vào vector search.
# CHUNK_OVERLAP = 50: Chọn 50 để đảm bảo các câu/từ vựng nằm ở ranh giới giữa 2 chunk không bị mất ngữ cảnh,
# giúp kết nối thông tin giữa các chunk tốt hơn.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"  # Sử dụng recursive vì nó xử lý thông minh các dấu phân tách cấu trúc (\n\n, \n, ., dấu cách)

# EMBEDDING_MODEL = "text-embedding-3-small": Sử dụng mô hình OpenAI để bypass lỗi nạp thư viện PyTorch (c10.dll) trên môi trường máy cục bộ
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

# VECTOR_STORE = "weaviate": Weaviate hỗ trợ hybrid search mạnh mẽ (kết hợp BM25 và Vector Search) và chạy tốt cục bộ qua Docker.
VECTOR_STORE = "weaviate"


# =============================================================================
# CUSTOM PURE-PYTHON RECURSIVE SPLITTER TO BYPASS PYTORCH CRASH
# =============================================================================

class PurePythonRecursiveCharacterTextSplitter:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, separators: list = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> list[str]:
        return self._recursive_split(text, self.separators)

    def _recursive_split(self, text: str, separators: list) -> list[str]:
        if not separators:
            return [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size - self.chunk_overlap)]
        
        separator = separators[0]
        next_separators = separators[1:]
        
        parts = text.split(separator)
        chunks = []
        current_chunk = ""
        
        for part in parts:
            if len(current_chunk) + len(part) + (len(separator) if current_chunk else 0) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                    current_chunk = current_chunk[overlap_start:]
                
                if len(part) > self.chunk_size:
                    sub_chunks = self._recursive_split(part, next_separators)
                    for sc in sub_chunks:
                        if len(current_chunk) + len(sc) + (len(separator) if current_chunk else 0) > self.chunk_size:
                            if current_chunk:
                                chunks.append(current_chunk)
                                overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                                current_chunk = current_chunk[overlap_start:]
                        if current_chunk:
                            current_chunk += separator + sc
                        else:
                            current_chunk = sc
                else:
                    if current_chunk:
                        current_chunk += separator + part
                    else:
                        current_chunk = part
            else:
                if current_chunk:
                    current_chunk += separator + part
                else:
                    current_chunk = part
                    
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str}}
    """
    documents = []
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in str(md_file.parent) or "legal" in str(md_file) else "news"
        documents.append({
            "content": content,
            "metadata": {"source": md_file.name, "type": doc_type}
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo strategy đã chọn.

    Returns:
        List of {'content': str, 'metadata': dict} — mỗi item là 1 chunk
    """
    splitter = PurePythonRecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = []
    for doc in documents:
        splits = splitter.split_text(doc["content"])
        for i, chunk_text in enumerate(splits):
            chunks.append({
                "content": chunk_text,
                "metadata": {**doc["metadata"], "chunk_index": i}
            })
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng model đã chọn.

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    import os
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY không tồn tại trong môi trường hoặc file .env")

    client = OpenAI(api_key=api_key)
    texts = [c["content"] for c in chunks]

    batch_size = 500
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        response = client.embeddings.create(
            input=batch_texts,
            model=EMBEDDING_MODEL
        )
        embeddings.extend([item.embedding for item in response.data])

    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb

    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """
    Lưu chunks vào vector store đã chọn.
    """
    import weaviate
    from weaviate.classes.config import Configure, Property, DataType

    # Kết nối tới local Weaviate chạy bằng Docker
    with weaviate.connect_to_local() as client:
        # Nếu collection đã tồn tại, xóa đi tạo lại để đảm bảo sạch dữ liệu
        if client.collections.exists("DrugLawDocs"):
            client.collections.delete("DrugLawDocs")

        # Tạo collection
        collection = client.collections.create(
            name="DrugLawDocs",
            vectorizer_config=Configure.Vectorizer.none(),  # Tự truyền vector embedding tự tạo
            properties=[
                Property(name="content", data_type=DataType.TEXT),
                Property(name="source", data_type=DataType.TEXT),
                Property(name="doc_type", data_type=DataType.TEXT),
                Property(name="chunk_index", data_type=DataType.INT),
            ]
        )

        # Insert các chunk vào vector store
        with collection.batch.dynamic() as batch:
            for chunk in chunks:
                batch.add_object(
                    properties={
                        "content": chunk["content"],
                        "source": chunk["metadata"]["source"],
                        "doc_type": chunk["metadata"]["type"],
                        "chunk_index": chunk["metadata"]["chunk_index"],
                    },
                    vector=chunk["embedding"]
                )


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n✓ Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"✓ Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"✓ Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("✓ Indexed to vector store")


if __name__ == "__main__":
    run_pipeline()

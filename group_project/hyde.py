# --- GROUP C6 - RAG PIPELINE PROJECT ---
import os
from openai import OpenAI

def generate_hypothetical_document(query: str, history: list = None) -> str:
    """
    Tạo ra một 'tài liệu giả định' (Hypothetical Document) bằng LLM.
    Mục tiêu: Đóng vai một chuyên gia pháp luật trả lời ngắn gọn câu hỏi, 
    chứa nhiều từ khóa chuyên ngành để dùng kết quả này đi search Vector DB.
    
    Args:
        query: Câu hỏi hiện tại của người dùng.
        history: Lịch sử hội thoại (để hiểu ngữ cảnh nếu câu hỏi bị thiếu chủ ngữ).
        
    Returns:
        Đoạn văn bản giả định dùng để search.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    system_prompt = """Bạn là một chuyên gia pháp luật và tin tức tại Việt Nam.
Nhiệm vụ của bạn là viết một đoạn văn ngắn (khoảng 2-3 câu) trả lời trực tiếp cho câu hỏi của người dùng.
Không cần trích dẫn, không cần chính xác 100%, nhưng PHẢI sử dụng đúng các từ khóa chuyên ngành, thuật ngữ pháp lý và bối cảnh sự việc.
Đoạn văn này sẽ được dùng làm query để tìm kiếm các văn bản pháp luật và bài báo liên quan trong Vector Database (HyDE algorithm)."""

    messages = [{"role": "system", "content": system_prompt}]
    
    # Nếu có lịch sử, nhồi thêm vào để hiểu context
    if history:
        # Lấy tối đa 3 lượt chat gần nhất để tránh loãng
        for msg in history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
    messages.append({"role": "user", "content": query})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"HyDE generation error: {e}")
        # Fallback to original query if API fails
        return query

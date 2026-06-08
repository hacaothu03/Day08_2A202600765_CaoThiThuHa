# --- GROUP C6 - RAG PIPELINE PROJECT ---
import streamlit as st
import os
import sys

# Đảm bảo import được module từ thư mục src ở thư mục gốc
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.task10_generation import generate_with_citation
from group_project.hyde import generate_hypothetical_document

st.set_page_config(page_title="Pháp Luật Chatbot", page_icon="⚖️", layout="wide")

# ==========================================
# CUSTOM CSS INJECTION (Nâng cấp UI/UX Premium)
# ==========================================
st.markdown("""
<style>
/* Gradient Title */
h1 {
    background: -webkit-linear-gradient(45deg, #1A2980, #26D0CE);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
}

/* Hiệu ứng nổi bọt cho tin nhắn Chat */
.stChatMessage {
    background: rgba(255, 255, 255, 0.7);
    border-radius: 15px;
    padding: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    backdrop-filter: blur(10px);
    margin-bottom: 15px;
    border: 1px solid rgba(255, 255, 255, 0.3);
}

/* Expander (Nguồn trích dẫn) Animation */
.stExpander {
    background: #f8f9fa;
    border-radius: 12px !important;
    border: 1px solid #e9ecef;
    transition: all 0.3s ease;
}
.stExpander:hover {
    border-color: #26D0CE;
    box-shadow: 0 8px 24px rgba(38, 208, 206, 0.15);
    transform: translateY(-2px);
}

/* Chat Input Styling */
.stChatInputContainer {
    border-radius: 24px !important;
    border: 2px solid #26D0CE !important;
    box-shadow: 0 8px 24px rgba(38, 208, 206, 0.2) !important;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #f4f6f9 !important;
    border-right: 1px solid #e0e0e0;
}
</style>
""", unsafe_allow_html=True)

st.title("⚖️ Chatbot Trợ Lý Pháp Luật & Tin Tức Ma Tuý")
st.markdown("Hỏi đáp về các quy định pháp luật và thông tin các vụ án ma tuý sử dụng RAG Pipeline (Hybrid Search + RRF + HyDE).")

# Sidebar cấu hình
with st.sidebar:
    st.header("⚙️ Cấu hình Nâng Cao")
    use_memory = st.toggle("Bật Conversation Memory", value=True, help="Giúp Bot nhớ ngữ cảnh của các câu hỏi trước đó để chat liên tục.")
    use_hyde = st.toggle("Bật Thuật Toán HyDE", value=True, help="Sinh câu trả lời nháp (Hypothetical Document) để đi tìm kiếm, giúp tăng độ chính xác lên mức tối đa.")
    
    st.divider()
    if st.button("🗑️ Xoá lịch sử chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Khởi tạo memory trong session_state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Gửi tin nhắn chào mừng
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Xin chào! Tôi là trợ lý pháp luật. Tôi có thể giải đáp các quy định của Luật Phòng chống ma tuý 2021 hoặc điểm tin các vụ án giải trí. Bạn muốn hỏi gì?"
    })

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander(f"📚 {len(msg['sources'])} Nguồn trích dẫn"):
                for s in msg["sources"]:
                    source_name = s['metadata'].get('source', 'Unknown')
                    st.caption(f"⭐ Rank Score: {s['score']:.4f} | 📄 {source_name}")

# Nhận input từ người dùng
if prompt := st.chat_input("Nhập câu hỏi của bạn (VD: Hình phạt tội tàng trữ?)..."):
    
    # Hiển thị tin nhắn người dùng
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Lấy history nếu dùng memory
    chat_history = st.session_state.messages if use_memory else None
    
    # Thêm user query vào memory ngay
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Tạo box chờ của bot
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        with st.spinner("🧠 Đang phân tích và tìm kiếm dữ liệu..."):
            search_query = prompt
            
            # Kích hoạt HyDE
            if use_hyde:
                search_query = generate_hypothetical_document(prompt, history=chat_history)
            
            # Chạy RAG Pipeline (Task 9 + Task 10)
            try:
                result = generate_with_citation(
                    query=prompt, 
                    search_query=search_query, 
                    chat_history=chat_history
                )
                
                answer = result["answer"]
                sources = result["sources"]
                retrieval_method = result["retrieval_source"]
                
                # Hiển thị câu trả lời
                message_placeholder.markdown(answer)
                
                # Hiển thị trích dẫn (nếu có)
                if sources:
                    with st.expander(f"📚 {len(sources)} Nguồn trích dẫn (via {retrieval_method})"):
                        for s in sources:
                            source_name = s['metadata'].get('source', 'Unknown')
                            st.caption(f"⭐ Rank Score: {s['score']:.4f} | 📄 {source_name}")
                            st.markdown(f"> *{s['content'][:150]}...*")
                            
                # Lưu vào bộ nhớ
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "sources": sources
                })
                
            except Exception as e:
                st.error(f"Đã xảy ra lỗi hệ thống: {e}\nHãy kiểm tra xem bạn đã cấu hình đúng OPENAI_API_KEY chưa.")

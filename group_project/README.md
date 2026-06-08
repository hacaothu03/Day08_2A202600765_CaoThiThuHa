# Báo Cáo Kiến Trúc Nhóm - RAG Chatbot

**Thông tin Nhóm:** Nhóm C6 - Phòng 402

## 👥 Phân Công Nhiệm Vụ
| STT | Họ và Tên | MSSV | Vai trò / Nhiệm vụ chính trong Project |
|:---:|:---|:---|:---|
| 1 | Hà Trung Kiên | 2A202600709 | Xây dựng giao diện Chatbot Streamlit, quản lý trạng thái Conversation Memory |
| 2 | Cao Thị Thu Hà | 2A202600765 | Thiết lập quy trình Evaluation (DeepEval), thu thập và dán nhãn Golden Dataset |
| 3 | Nguyễn Lâm Phương Thảo | 2A202600873 | Cài đặt thuật toán HyDE, tinh chỉnh Prompt cho LLM Generation có trích dẫn |
| 4 | Nguyễn Bình Huy | 2A202600689 | Quản lý Vector DB (ChromaDB), đấu nối và tối ưu hoá Hybrid Retrieval Pipeline |

---

Dự án này là kết quả của phần Bài Tập Nhóm, triển khai **Option B: RAG Chatbot**. 
Hệ thống kết nối trực tiếp với RAG pipeline từ bài cá nhân (Task 4 - Task 10) và được nâng cấp thêm các tính năng mở rộng để tối ưu hóa khả năng tìm kiếm và nâng cao trải nghiệm người dùng.

## 🌟 Tính Năng Nổi Bật

1. **Giao diện Chatbot Streamlit (UI/UX chất lượng)**
   - Mô phỏng giao diện ChatGPT quen thuộc.
   - Hiển thị rành mạch các đoạn hội thoại giữa User và Assistant.
   - Ẩn/Hiện thông tin trích dẫn chi tiết (Sources) bằng tính năng Expander rất gọn gàng.

2. **Conversation Memory (Bộ nhớ đa lượt)**
   - Hệ thống lưu trữ lịch sử chat thông qua `st.session_state`.
   - Lịch sử (6 tin nhắn gần nhất) sẽ được gài vào Prompt của OpenAI để cung cấp bối cảnh. Nhờ đó người dùng có thể hỏi các câu hỏi follow-up (như: "Hãy tóm tắt lại câu trả lời trên") mà bot vẫn hiểu được.

3. **Thuật toán HyDE (Hypothetical Document Embeddings)**
   - Thay vì dùng câu hỏi của người dùng để đi tìm kiếm văn bản (Vector Search) một cách thô sơ, hệ thống tích hợp module `hyde.py`.
   - **Cách hoạt động:** Khi có câu hỏi, hệ thống dùng GPT-4o-mini để sinh ra một "câu trả lời giả định" (chứa nhiều thuật ngữ và từ khóa chuyên môn). Sau đó dùng câu trả lời giả định này đi query vào ChromaDB. Kết quả giúp RAG vượt qua giới hạn của tìm kiếm từ vựng thông thường, tăng độ bao phủ của dữ liệu tìm được.

4. **Trích dẫn minh bạch (Citations)**
   - Prompt chuẩn hóa buộc LLM phải đặt trích dẫn `[Tên văn bản/Bài báo]` sau mỗi luận điểm.
   - Giao diện cung cấp phần mở rộng bên dưới mỗi câu trả lời để người dùng có thể đọc trực tiếp các đoạn nội dung gốc (kèm điểm số Rank Score) chứng minh cho câu trả lời của Bot.

## 🛠 Cách Cài Đặt & Chạy

1. Hãy chắc chắn bạn đã điền `OPENAI_API_KEY` vào file `.env`.
2. Đảm bảo bạn đã chạy `task4_chunking_indexing.py` ít nhất một lần để nạp dữ liệu vào ChromaDB.
3. Khởi chạy giao diện Chatbot bằng lệnh:
```bash
streamlit run group_project/app.py
```

## 🧠 Kiến Trúc Hệ Thống (Flow)

```text
Người dùng nhập query
       │
       ▼
[Kiểm tra bật HyDE?]
  ├─ Bật: GPT-4o sinh ra "Tài liệu giả định" (HyDE doc) 
  └─ Tắt: Giữ nguyên query
       │
       ▼
Retrieval Pipeline (task9)
(ChromaDB Semantic + BM25 Lexical) 
       │
       ▼
Gộp kết quả bằng thuật toán RRF (Reciprocal Rank Fusion)
       │
       ▼
Generation (task10)
Đưa vào GPT-4o-mini kèm theo [Lịch sử hội thoại] và [Các chunks đã tìm được]
       │
       ▼
In kết quả ra màn hình Giao diện Streamlit (Có trích dẫn nguồn)
```
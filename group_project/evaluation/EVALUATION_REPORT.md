# Báo Cáo Đánh Giá Kiểm Thử Hệ Thống (Evaluation Report)

**Thực hiện bởi Nhóm C6 - Phòng 402**
- Hà Trung Kiên - 2A202600709
- Cao Thị Thu Hà - 2A202600765
- Nguyễn Lâm Phương Thảo - 2A202600873
- Nguyễn Bình Huy - 2A202600689

---

> *Ghi chú: Điểm số được lấy tự động từ công cụ DeepEval sau khi chạy 4 sample (Demo mục đích).*

**1. Thông tin Dataset:**
- Số lượng sample chạy test: 4 câu hỏi (2 câu Luật, 2 câu Tin tức)
- Công cụ chấm điểm: `deepeval` với giám khảo `gpt-4o-mini`.

**2. Kết quả A/B Testing:**
- **Config A (Baseline - Không HyDE) - Pass Rate: 50%:**
  - Faithfulness: 0.83/1.0
  - Answer Relevancy: 0.92/1.0
  - Contextual Precision: 0.83/1.0
  - Contextual Recall: 1.00/1.0
- **Config B (Có HyDE) - Pass Rate: 75%:**
  - Faithfulness: 0.94/1.0
  - Answer Relevancy: 0.92/1.0
  - Contextual Precision: 0.81/1.0
  - Contextual Recall: 1.00/1.0

**Phân tích A/B:**
- *Nhận xét:* Config B (Có HyDE) tỏ ra vượt trội hơn hẳn Config A với tỷ lệ Pass Rate tăng từ 50% lên 75%. Điểm Faithfulness (Tính trung thực) của HyDE cũng đạt mức xuất sắc 0.94 so với 0.83 của Baseline.
- *Kết luận:* Thuật toán HyDE thực sự hoạt động hiệu quả bằng cách tạo ra các từ khóa ngữ cảnh phụ trợ, giúp AI không bị "ảo giác" (bịa ra thông tin sai) khi trả lời các câu hỏi về thông tin tin tức pháp luật phức tạp.

**3. Phân tích Worst Performers (Các trường hợp điểm thấp nhất):**
- **Câu hỏi bị Fail:** *"Lê Ánh Nhật (ca sĩ Miu Lê) bị cơ quan Công an TPHCM khởi tố về hành vi gì?"* (Bị Fail ở Config A).
- **Lý do (Theo DeepEval log):** Trượt tiêu chí **Faithfulness** (Tính trung thực). AI bị "ảo giác" (Hallucination) khi tự động bịa ra ngày tháng là "16 tháng 5 năm 2026", trong khi văn bản gốc không hề đề cập ngày này gắn với Miu Lê.
- **Hướng khắc phục:** 
  1. Cải thiện lại Prompt: Yêu cầu AI tuyệt đối tuân thủ văn bản, cấm tự suy diễn ngày tháng.
  2. Bật HyDE (Config B) đã khắc phục hoàn toàn được lỗi này (Điểm Faithfulness tăng mạnh và câu hỏi này đã Pass ở Config B).

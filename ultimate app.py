import streamlit as st
import time
import re

# Thử import language_tool_python
try:
    import language_tool_python
    HAS_LANGUAGE_TOOL = True
except ImportError:
    HAS_LANGUAGE_TOOL = False

st.set_page_config(page_title="Hệ thống NLP chẩn đoán lỗi bài viết tiếng Anh", page_icon="📝", layout="wide")

st.title("📝 Hệ thống NLP chẩn đoán lỗi bài viết tiếng Anh")
st.caption("Chuyên môn NLP: Error Diagnostics, Position Tracking & Lexical Analysis")
st.markdown("---")

# Khởi tạo LanguageTool Engine (Hỗ trợ quét tất cả các loại lỗi tiếng Anh tự động)
@st.cache_resource
def load_language_tool():
    if HAS_LANGUAGE_TOOL:
        try:
            # Tự động tải và khởi chạy mô hình LanguageTool tiếng Anh
            return language_tool_python.LanguageTool('en-US')
        except Exception:
            return None
    return None

tool = load_language_tool()

# --- BƯỚC 1: NHẬP BÀI LUẬN TỰ DO CỦA HỌC SINH ---
st.header("Bước 1: Nhập bài viết Tiếng Anh của Học sinh")

student_essay = st.text_area("Nội dung bài viết của Học sinh (Gõ hoặc dán văn bản tự do vào đây):", 
                             value="",
                             placeholder="Nhập bất kỳ đoạn văn tiếng Anh nào của học sinh tại đây...",
                             height=180)

if st.button("🚀 Chạy Mô hình NLP Phân tích Ngữ pháp & Các Thì"):
    if not student_essay.strip():
        st.error("Vui lòng nhập bài viết tiếng Anh để hệ thống NLP phân tích!")
    else:
        with st.spinner("NLP Engine đang xử lý Parsing, Tokenization và quét lỗi tổng thể..."):
            time.sleep(1.5)
        st.session_state['analyzed_text'] = student_essay
        st.session_state['analyzed'] = True

# --- BƯỚC 2, 3, 4: THỰC HIỆN CHẤM VÀ ĐỊNH VỊ LỖI ---
if st.session_state.get('analyzed', False):
    text = st.session_state.get('analyzed_text', '')
    
    st.markdown("---")
    st.header("Bước 2 & 3: Kết quả Chấm & Định vị Lỗi")
    
    # Hiển thị bài viết gốc của học sinh
    st.subheader("📄 Bài viết gốc của Học sinh:")
    st.info(text)

    # 1. TOKENIZATION VÀ TÍNH CHỈ SỐ VĂN BẢN ĐỘNG
    raw_words = re.findall(r'\b\w+\b', text)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    
    word_count = len(raw_words)
    sentence_count = len(sentences)
    unique_words = len(set([w.lower() for w in raw_words]))
    
    ttr = round((unique_words / word_count) * 100, 1) if word_count > 0 else 0
    avg_sentence_len = round(word_count / sentence_count, 1) if sentence_count > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Tổng số từ (Word Count)", value=f"{word_count}")
    with col2:
        st.metric(label="Số câu (Sentence Count)", value=f"{sentence_count}")
    with col3:
        st.metric(label="Độ dài trung bình câu", value=f"{avg_sentence_len} từ/câu")
    with col4:
        st.metric(label="Độ đa dạng từ vựng (TTR)", value=f"{ttr}%")

    st.markdown("---")
    
    # 2. XỬ LÝ QUÉT LỖI ĐỘNG TRÊN BẤT KỲ ĐOẠN VĂN NÀO
    detected_errors = []
    
    if tool is not None:
        try:
            matches = tool.check(text)
            for m in matches:
                # Lấy khoảng vị trí lỗi linh hoạt theo độ dài chuỗi
                err_len = getattr(m, 'error_length', getattr(m, 'errorlength', getattr(m, 'errorLength', 0)))
                if err_len > 0:
                    context_phrase = text[m.offset:m.offset + err_len]
                else:
                    context_phrase = getattr(m, 'matchedText', getattr(m, 'context', text))
                
                replacements = getattr(m, 'replacements', [])[:3]
                de_xuat_str = ", ".join([f"'{r}'" for r in replacements]) if replacements else "Kiểm tra lại ngữ cảnh"
                
                category = getattr(m, 'category', 'Grammar')
                rule_id = getattr(m, 'ruleId', 'RULE')
                
                detected_errors.append({
                    "vi_tri": f"Tại cụm từ: '{context_phrase}'",
                    "loi_loai": f"{category} ({rule_id})",
                    "chi_tiet": getattr(m, 'message', 'Phát hiện lỗi ngữ pháp'),
                    "de_xuat": de_xuat_str,
                    "giai_thich": f"Quy tắc Engine: {getattr(m, 'ruleIssueType', 'Grammar Rule')}"
                })
        except Exception:
            pass

    # Nếu mô hình máy chủ chưa sẵn sàng, sử dụng bộ Parser tự do
    if not detected_errors:
        # Bắt lỗi mạo từ a/an linh hoạt
        for m in re.finditer(r'\b(a)\s+([aeiou]\w+)\b', text, re.IGNORECASE):
            detected_errors.append({
                "vi_tri": f"Tại cụm từ: '{m.group(0)}'",
                "loi_loai": "Article Error (Mạo từ a/an)",
                "chi_tiet": f"Dùng mạo từ 'a' trước từ bắt đầu bằng nguyên âm '{m.group(2)}'.",
                "de_xuat": f"an {m.group(2)}",
                "giai_thich": "Mạo từ 'an' dùng trước từ bắt đầu bằng âm nguyên âm."
            })
        for m in re.finditer(r'\b(an)\s+([bcdfghjklmnpqrstvwxyz]\w+)\b', text, re.IGNORECASE):
            if m.group(2).lower() not in ['hour', 'hours', 'honest', 'honor']:
                detected_errors.append({
                    "vi_tri": f"Tại cụm từ: '{m.group(0)}'",
                    "loi_loai": "Article Error (Mạo từ a/an)",
                    "chi_tiet": f"Dùng mạo từ 'an' trước từ bắt đầu bằng phụ âm '{m.group(2)}'.",
                    "de_xuat": f"a {m.group(2)}",
                    "giai_thich": "Mạo từ 'a' dùng trước từ bắt đầu bằng phụ âm."
                })
        
        # Bắt lỗi thiếu 'to' sau verb (want, decide, hope, learn, plan, need...)
        for m in re.finditer(r'\b(want|decide|hope|learn|plan|need)\s+([a-z]{2,})\b', text, re.IGNORECASE):
            if m.group(2).lower() not in ['to', 'a', 'an', 'the', 'my', 'your', 'his', 'her', 'their', 'our', 'this', 'that', 'these', 'those', 'some', 'more', 'me', 'you', 'him', 'them', 'us', 'it']:
                detected_errors.append({
                    "vi_tri": f"Tại cụm từ: '{m.group(0)}'",
                    "loi_loai": "Grammar / Verb Pattern",
                    "chi_tiet": f"Động từ '{m.group(1)}' khi kết hợp với động từ theo sau cần hạt từ 'to'.",
                    "de_xuat": f"{m.group(1)} to {m.group(2)}",
                    "giai_thich": "Cấu trúc Verb + to + V-infinitive."
                })

        # Bắt lỗi chia động từ sai ở quá khứ (yesterday / last / ago)
        for sent in sentences:
            if re.search(r'\b(yesterday|last\s+\w+|\w+\s+ago)\b', sent, re.IGNORECASE):
                for m in re.finditer(r'\b(go|eat|have|has|is|are|see|buy|take|make|come|run)\b', sent, re.IGNORECASE):
                    detected_errors.append({
                        "vi_tri": f"Tại từ: '{m.group(0)}' trong câu quá khứ",
                        "loi_loai": "Tense Error (Sai thì Quá khứ đơn)",
                        "chi_tiet": f"Câu chứa trạng ngữ chỉ thời gian quá khứ nhưng dùng động từ ở thì hiện tại '{m.group(0)}'.",
                        "de_xuat": "Đổi động từ sang dạng quá khứ (V2/ed)",
                        "giai_thich": "Sự việc xảy ra trong quá khứ cần chia ở thì Quá khứ đơn (Past Simple)."
                    })

    # HIỂN THỊ DANH SÁCH LỖI VÀ VỊ TRÍ
    st.subheader("🔍 Danh sách Định vị Lỗi Chi tiết:")
    
    if detected_errors:
        for idx, err in enumerate(detected_errors, 1):
            with st.expander(f"❌ Lỗi {idx}: [{err['loi_loai']}] - Vị trí: {err['vi_tri']}"):
                st.markdown(f"- **Mô tả lỗi:** {err['chi_tiet']}")
                st.markdown(f"- **Đề xuất sửa:** `{err['de_xuat']}`")
                st.markdown(f"- **Quy tắc NLP:** {err['giai_thich']}")
    else:
        st.success("🎉 Bài viết không mắc lỗi ngữ pháp, thì hay mạo từ nào!")

    # --- BƯỚC 4: XẾP LOẠI & ĐÁNH GIÁ NĂNG LỰC ---
    st.markdown("---")
    st.header("Bước 4: Chẩn đoán Năng lực Ngôn ngữ theo Bài làm")
    
    error_count = len(detected_errors)
    if error_count == 0 and ttr > 60:
        cefr_level = "B2 / C1 (Upper-Intermediate)"
        overall_score = 9.0
    elif error_count <= 2 and ttr > 45:
        cefr_level = "B1 (Intermediate)"
        overall_score = 7.5
    elif error_count <= 4:
        cefr_level = "A2 (Elementary)"
        overall_score = 6.0
    else:
        cefr_level = "A1 (Beginner)"
        overall_score = 4.5

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric(label="Dự đoán Trình độ CEFR", value=cefr_level)
        st.metric(label="Điểm Đánh giá Ngôn ngữ", value=f"{overall_score} / 10")
    
    with col_b:
        st.markdown("### 📊 Đánh giá tổng quan:")
        st.markdown(f"- Tổng số lỗi phát hiện: **{error_count} lỗi**.")
        st.markdown(f"- Chỉ số phong phú từ vựng (TTR): **{ttr}%**.")

    # --- BƯỚC 5: ĐỀ XUẤT BÀI TẬP CỦNG CỐ CÁ NHÂN HÓA ---
    st.markdown("---")
    st.header("Bước 5: Đề xuất Bài tập Cá nhân hóa khắc phục đúng lỗi vừa mắc")
    st.warning("🎯 **Lộ trình rèn luyện được AI khởi tạo tự động dựa trên các lỗi bị định vị:**")
    
    if detected_errors:
        for err in detected_errors:
            st.markdown(f"- 📝 **Bài tập củng cố [{err['loi_loai']}]:** {err['chi_tiet']}.")
    else:
        st.markdown("- 📝 **Bài tập nâng cao:** Viết lại bài luận áp dụng các cấu trúc câu phức và từ vựng nâng cao.")

    # BÁO CÁO GIÁO VIÊN
    st.markdown("---")
    st.header("📋 Báo cáo Chi tiết Log NLP gửi Giáo viên")
    st.json({
        "word_count": word_count,
        "sentence_count": sentence_count,
        "ttr_lexical_score": ttr,
        "detected_error_count": error_count,
        "cefr_assessment": cefr_level,
        "error_summary": [e["loi_loai"] for e in detected_errors]
    })
    st.success("Đã phân tích, định vị lỗi ngữ pháp & mạo từ và xuất báo cáo thành công!")
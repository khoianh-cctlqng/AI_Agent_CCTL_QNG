import os

import streamlit as st
import uuid
from click import prompt
from openai import OpenAI


# =========================
# CẤU HÌNH TRANG
# =========================
st.set_page_config(
    page_title="AI Agent CCTLQNG",
    page_icon="💧",
    layout="wide",
)
st.markdown(
    """
    <style>
    /* Ẩn thanh menu và phần chân trang mặc định */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    /* Thu gọn khoảng trống phía trên */
    .block-container {
        max-width: 900px;
        padding-top: 1.5rem;
        padding-bottom: 7rem;
    }

    /* Thanh bên trái */
    [data-testid="stSidebar"] {
        min-width: 280px;
        max-width: 280px;
        background-color: #f7f7f8;
        border-right: 1px solid #e5e5e5;
    }

    [data-testid="stSidebarContent"] {
        padding-top: 1rem;
    }

    /* Nút trong sidebar */
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        border: none;
        border-radius: 8px;
        text-align: left;
        justify-content: flex-start;
        background-color: transparent;
        padding: 0.65rem 0.75rem;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #ececf1;
    }

    /* Tin nhắn */
    [data-testid="stChatMessage"] {
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
    }

    /* Ô nhập chat */
    [data-testid="stChatInput"] {
        max-width: 850px;
        margin-left: auto;
        margin-right: auto;
    }

    [data-testid="stChatInput"] textarea {
        border-radius: 18px;
    }

    /* Tiêu đề ứng dụng */
    .agent-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 700;
        margin-top: 0.5rem;
        margin-bottom: 0.25rem;
    }

    .agent-caption {
        text-align: center;
        color: #6b6b6b;
        margin-bottom: 1.5rem;
    }
    /* Ô nhập giống ChatGPT */
[data-testid="stChatInput"] {
    position: sticky;
    bottom: 0;
    background: white;
    padding-top: 12px;
    padding-bottom: 12px;
}

[data-testid="stChatInput"] textarea {
    border-radius: 24px;
    border: 1px solid #d9d9d9;
    padding: 12px 16px;
    font-size: 16px;
}

[data-testid="stChatInput"] button {
    border-radius: 50%;
}
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# KẾT NỐI OPENAI
# =========================
api_key = os.getenv("OPENAI_API_KEY")
vector_store_id = os.getenv("OPENAI_VECTOR_STORE_ID")

if not api_key:
    st.error(
        "Chưa tìm thấy OPENAI_API_KEY. "
        "Hãy kiểm tra lại biến môi trường trên máy tính."
    )
    st.stop()

if not vector_store_id:
    st.error(
        "Chưa tìm thấy OPENAI_VECTOR_STORE_ID. "
        "Hãy kiểm tra lại biến môi trường trên máy tính."
    )
    st.stop()

client = OpenAI(api_key=api_key)

# =========================
# GIAO DIỆN
# =========================
st.markdown(
    '<div class="agent-title">💧 AI Agent CCTLQNG</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="agent-caption">'
    'Trợ lý hỗ trợ công việc Chi cục Thủy lợi Quảng Ngãi '
    'được xây dựng và phát triển bởi Hồ Hải Khôi Anh'
    '</div>',
    unsafe_allow_html=True,
)

# =========================
# KHỞI TẠO LỊCH SỬ HỘI THOẠI
# =========================
if "conversations" not in st.session_state:
    first_id = str(uuid.uuid4())

    st.session_state.conversations = {
        first_id: {
            "title": "Cuộc trò chuyện mới",
            "messages": [
                {
                    "role": "assistant",
                    "content": (
                        "Xin chào! Tôi là trợ lý hỗ trợ công việc "
                        "Chi cục Thủy lợi tỉnh Quảng Ngãi. "
                        "Bạn cần tôi hỗ trợ nội dung gì?"
                    ),
                }
            ],
        }
    }

    st.session_state.current_conversation_id = first_id
    current_id = st.session_state.current_conversation_id
    current_conversation = st.session_state.conversations[current_id]
    messages = current_conversation["messages"]


# =========================
# NÚT XÓA HỘI THOẠI
# =========================
with st.sidebar:
    st.header("Lịch sử trò chuyện")

    if st.button(
        "➕ Cuộc trò chuyện mới",
        use_container_width=True
    ):
        new_id = str(uuid.uuid4())

        st.session_state.conversations[new_id] = {
            "title": "Cuộc trò chuyện mới",
            "messages": [
                {
                    "role": "assistant",
                    "content": "Xin chào! Đây là cuộc trò chuyện mới.",
                }
            ],
        }

        st.session_state.current_conversation_id = new_id
        st.rerun()

    st.divider()

    for conversation_id, conversation_data in reversed(
        list(st.session_state.conversations.items())
    ):
        title = conversation_data["title"]

        if st.button(
            title,
            key=f"conversation_{conversation_id}",
            use_container_width=True
        ):
            st.session_state.current_conversation_id = conversation_id
            st.rerun()

    st.divider()

    if st.button(
        "🗑️ Xóa cuộc trò chuyện hiện tại",
        use_container_width=True
    ):
        current_id = st.session_state.current_conversation_id

        del st.session_state.conversations[current_id]

        if st.session_state.conversations:
            st.session_state.current_conversation_id = next(
                iter(st.session_state.conversations)
            )
        else:
            new_id = str(uuid.uuid4())

            st.session_state.conversations[new_id] = {
                "title": "Cuộc trò chuyện mới",
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Xin chào! Đây là cuộc trò chuyện mới.",
                    }
                ],
            }

            st.session_state.current_conversation_id = new_id

        st.rerun()


# =========================
# HIỂN THỊ LỊCH SỬ
# =========================
current_id = st.session_state.current_conversation_id
current_conversation = st.session_state.conversations[current_id]
messages = current_conversation["messages"]

for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =========================
# NHẬN CÂU HỎI
# =========================
# Khu vực đính kèm tài liệu ngay trên khung chat
uploaded_files = st.file_uploader(
    "📎 Đính kèm tài liệu",
    type=["pdf", "docx", "txt", "md"],
    accept_multiple_files=True,
    key="chat_file_uploader"
)

if uploaded_files:
    if st.button("Đưa tài liệu vào kho dữ liệu", type="primary"):
        with st.spinner("Đang tải và xử lý tài liệu..."):
            try:
                for uploaded_file in uploaded_files:

                    # Đưa con trỏ file về đầu
                    uploaded_file.seek(0)

                    # Tải file lên OpenAI
                    openai_file = client.files.create(
                        file=(
                            uploaded_file.name,
                            uploaded_file.getvalue()
                        ),
                        purpose="assistants"
                    )

                    # Gắn file vào Vector Store đang sử dụng
                    client.vector_stores.files.create(
                        vector_store_id=vector_store_id,
                        file_id=openai_file.id
                    )

                st.success(
                    f"Đã đưa {len(uploaded_files)} tài liệu vào kho dữ liệu."
                )

            except Exception as e:
                st.error(f"Không thể tải tài liệu: {e}")
question = st.chat_input("Nhập câu hỏi về công tác thủy lợi...")

if question:
    # Lưu và hiển thị câu hỏi
    messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    # Tạo nội dung gửi đến OpenAI
    conversation = [
        {
            "role": "developer",
            "content": (
                "Bạn là trợ lý chuyên môn hỗ trợ công việc của cơ quan "
                "quản lý nhà nước về thủy lợi, đê điều, phòng chống thiên tai, "
                "khí tượng thủy văn và tài nguyên nước tại Việt Nam. "
                "Trả lời bằng tiếng Việt, rõ ràng, thận trọng và có cấu trúc. "
                "Không tự tạo số hiệu văn bản, điều khoản hoặc dữ liệu khi "
                "không có căn cứ. Khi chưa đủ thông tin, phải nói rõ."
            ),
        }
    ]
    conversation = [
        {
            "role": message["role"],
            "content": message["content"]
        }
        for message in messages
    ]
    # Gọi API
    with st.chat_message("assistant"):
        with st.spinner("Agent đang xử lý..."):
            try:
                response = client.responses.create(
                    model="gpt-5-mini",
                    input=conversation,
                    tools=[
                        {
                            "type": "file_search",
                            "vector_store_ids": [vector_store_id],
                            "max_num_results": 10,
                        }
                    ],
                )
                answer = response.output_text

                st.markdown(answer)

                messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

            except Exception as error:
                st.error(f"Đã xảy ra lỗi: {error}")

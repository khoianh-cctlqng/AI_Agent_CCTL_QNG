import os
import uuid

import streamlit as st
from openai import OpenAI


# =========================
# CẤU HÌNH TRANG
# =========================
st.set_page_config(
    page_title="AI Agent CCTLQNG",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================
# CSS GIAO DIỆN
# =========================
st.markdown(
    """
    <style>
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    .stApp {
        background-color: #ffffff;
    }

    .block-container {
        max-width: 920px;
        padding-top: 1.2rem;
        padding-bottom: 7rem;
    }

    [data-testid="stSidebar"] {
        background-color: #f7f7f8;
        border-right: 1px solid #e5e5e5;
        min-width: 270px;
        max-width: 270px;
    }

    [data-testid="stSidebarContent"] {
        padding: 1rem 0.75rem;
    }

    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        border: none;
        border-radius: 8px;
        text-align: left;
        justify-content: flex-start;
        background-color: transparent;
        padding: 0.65rem 0.7rem;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #ececf1;
    }

    .agent-header {
        text-align: center;
        margin-top: 0.5rem;
        margin-bottom: 1.5rem;
    }

    .agent-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }

    .agent-caption {
        color: #6b6b6b;
        font-size: 0.9rem;
    }

    [data-testid="stChatMessage"] {
        padding: 0.75rem 0;
        background: transparent;
    }

    [data-testid="stChatInput"] {
        max-width: 850px;
        margin-left: auto;
        margin-right: auto;
    }

    [data-testid="stChatInput"] textarea {
        border-radius: 24px;
        border: 1px solid #d9d9d9;
        min-height: 52px;
        padding: 12px 52px 12px 18px;
        font-size: 16px;
    }

    [data-testid="stChatInput"] button {
        border-radius: 50%;
    }

    .recent-label {
        font-size: 0.8rem;
        color: #777777;
        margin: 1rem 0 0.35rem 0.4rem;
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
    st.error("Chưa tìm thấy OPENAI_API_KEY.")
    st.stop()

if not vector_store_id:
    st.error("Chưa tìm thấy OPENAI_VECTOR_STORE_ID.")
    st.stop()

client = OpenAI(api_key=api_key)


# =========================
# KHỞI TẠO HỘI THOẠI
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


# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("### 💧 AI Agent")

    if st.button(
        "＋ Đoạn chat mới",
        use_container_width=True,
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

    st.markdown(
        '<div class="recent-label">Gần đây</div>',
        unsafe_allow_html=True,
    )

    for conversation_id, conversation_data in reversed(
        list(st.session_state.conversations.items())
    ):
        title = conversation_data["title"]

        if st.button(
            title,
            key=f"conversation_{conversation_id}",
            use_container_width=True,
        ):
            st.session_state.current_conversation_id = conversation_id
            st.rerun()

    st.divider()

    if st.button(
        "🗑 Xóa cuộc trò chuyện hiện tại",
        use_container_width=True,
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
# CUỘC TRÒ CHUYỆN HIỆN TẠI
# =========================
current_id = st.session_state.current_conversation_id
current_conversation = st.session_state.conversations[current_id]
messages = current_conversation["messages"]
st.divider()


# =========================
# TIÊU ĐỀ
# =========================
st.markdown(
    """
    <div class="agent-header">
        <div class="agent-title">💧 AI Agent CCTLQNG</div>
        <div class="agent-caption">
        Trợ lý hỗ trợ công việc Chi cục Thủy lợi tỉnh Quảng Ngãi <br>
        Được xây dựng và phát triển bởi Hồ Hải Khôi Anh
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================
# HIỂN THỊ HỘI THOẠI
# =========================
chat_container = st.container(height=700, border=False)

with chat_container:
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# =========================
# NHẬP CÂU HỎI
# =========================
question = st.chat_input("Hỏi AI Agent")

if question:
    messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    if current_conversation["title"] == "Cuộc trò chuyện mới":
        title = question.strip()

        if len(title) > 38:
            title = title[:38] + "..."

        current_conversation["title"] = title

    conversation = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in messages
    ]

    with st.spinner("AI Agent đang xử lý..."):
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

            messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

            st.rerun()

        except Exception as error:
            st.error(f"Đã xảy ra lỗi: {error}")
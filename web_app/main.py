import streamlit as st

st.set_page_config(
    page_title="Trợ lý CCTL_QNG",
    page_icon="💧",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* Ẩn các thành phần mặc định không cần thiết */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    html, body, [data-testid="stAppViewContainer"] {
        margin: 0;
        padding: 0;
        background: #ffffff;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    /* Giới hạn chiều rộng nội dung giống giao diện ChatGPT */
    .block-container {
        max-width: 920px;
        padding-top: 128px;
        padding-bottom: 48px;
    }

    /* Tiêu đề cố định */
    .cctl-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 1000;
        min-height: 98px;
        padding: 14px 20px;
        background: rgba(255, 255, 255, 0.97);
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        box-sizing: border-box;
    }

    .cctl-title {
        margin: 0 0 3px 0;
        font-size: 22px;
        font-weight: 700;
        line-height: 1.25;
    }

    .cctl-subtitle {
        margin: 0;
        font-size: 15px;
        line-height: 1.4;
    }

    .cctl-author {
        margin-top: 2px;
        font-size: 13px;
        color: #6b7280;
    }

    /* Lời chào */
    .welcome-box {
        margin: 0 0 14px 0;
        padding: 14px 18px;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        background: #f8fafc;
        font-size: 15px;
    }

    /* Ô nhập câu hỏi */
    div[data-testid="stTextInput"] input {
        min-height: 52px;
        padding: 12px 18px;
        border: 1px solid #d1d5db;
        border-radius: 26px;
        font-size: 15px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #9ca3af;
        box-shadow: 0 0 0 1px #9ca3af;
    }

    /* Nút gửi */
    div[data-testid="stFormSubmitButton"] button {
        min-height: 48px;
        border-radius: 24px;
        font-weight: 600;
    }

    /* Tin nhắn */
    div[data-testid="stChatMessage"] {
        border-radius: 18px;
        padding: 10px 14px;
        margin-bottom: 10px;
    }

    @media (max-width: 700px) {
        .block-container {
            padding-top: 142px;
            padding-left: 14px;
            padding-right: 14px;
        }

        .cctl-title {
            font-size: 19px;
        }

        .cctl-subtitle {
            font-size: 13px;
        }
    }
    </style>

    <div class="cctl-header">
        <div class="cctl-title">💧 Trợ lý CCTL_QNG</div>
        <div class="cctl-subtitle">Trợ lý hỗ trợ công việc Chi cục Thủy lợi tỉnh Quảng Ngãi</div>
        <div class="cctl-author">Được xây dựng và phát triển bởi Hồ Hải Khôi Anh</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown(
    '<div class="welcome-box">Xin chào! Tôi là trợ lý hỗ trợ công việc Chi cục Thủy lợi tỉnh Quảng Ngãi.</div>',
    unsafe_allow_html=True,
)

# Ô hỏi nằm ngay dưới lời chào, không bị ghim ở cuối màn hình.
with st.form("question_form", clear_on_submit=True):
    question = st.text_input(
        "Hỏi Trợ lý CCTL_QNG",
        placeholder="Hỏi Trợ lý CCTL_QNG...",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Gửi", use_container_width=True)

# Hiển thị lịch sử trò chuyện bên dưới ô nhập.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if submitted and question.strip():
    question = question.strip()
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    # Thay phần trả lời mẫu dưới đây bằng đoạn gọi OpenAI/vector store hiện có của anh.
    reply = "Tôi đã nhận câu hỏi. Anh hãy nối phần xử lý OpenAI hiện có vào vị trí này."
    st.session_state.messages.append({"role": "assistant", "content": reply})

    with st.chat_message("assistant"):
        st.markdown(reply)

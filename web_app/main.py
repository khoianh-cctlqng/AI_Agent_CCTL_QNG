from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI


# =========================================================
# CẤU HÌNH ỨNG DỤNG
# =========================================================
APP_TITLE = "Trợ lý CCTL_QNG"
APP_ICON = "💧"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "conversations.json"

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
FAST_MODEL = os.getenv("OPENAI_FAST_MODEL", "gpt-5-nano")
DEEP_MODEL = os.getenv("OPENAI_DEEP_MODEL", DEFAULT_MODEL)
DEFAULT_VECTOR_STORE_ID = os.getenv("OPENAI_VECTOR_STORE_ID", "").strip()

SYSTEM_INSTRUCTIONS = """
Bạn là Trợ lý CCTL_QNG, hỗ trợ công tác tham mưu của Chi cục Thủy lợi tỉnh Quảng Ngãi.

Nguyên tắc trả lời:
- Trả lời bằng tiếng Việt, trừ khi người dùng yêu cầu ngôn ngữ khác.
- Ưu tiên độ chính xác, tính tuân thủ, văn phong hành chính và khả năng áp dụng thực tế.
- Khi sử dụng tài liệu trong kho, chỉ kết luận trong phạm vi nội dung tìm thấy.
- Không tự tạo căn cứ pháp lý, số hiệu văn bản hoặc số liệu.
- Khi chưa đủ dữ liệu, nêu rõ nội dung còn thiếu.
- Với yêu cầu soạn thảo văn bản, trình bày chặt chẽ, rõ ý, đúng thể thức diễn đạt hành chính.
""".strip()


# =========================================================
# THIẾT LẬP TRANG
# =========================================================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --border: #e6e8eb;
        --muted: #6b7280;
        --panel: #f8fafc;
        --blue-soft: #eaf4ff;
    }

    #MainMenu, footer {visibility: hidden;}

    [data-testid="stAppViewContainer"] {
        background: #ffffff;
    }

    [data-testid="stHeader"] {
        background: rgba(255,255,255,0.94);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(230,232,235,0.7);
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid var(--border);
        background: #fbfbfc;
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    .block-container {
        max-width: 1050px;
        padding-top: 0.5rem;
        padding-bottom: 3rem;
    }

    /* Thông tin thương hiệu đặt trong sidebar trái */
    .sidebar-subtitle {
        margin-top: 0.15rem;
        font-size: 0.78rem;
        color: #374151;
        line-height: 1.4;
    }

    .sidebar-author {
        margin-top: -0.35rem;
        margin-bottom: 0.55rem;
        font-size: 0.70rem;
        color: var(--muted);
        line-height: 1.25;
    }

    [data-testid="stMainBlockContainer"] {
        padding-top: 1.2rem;
        padding-bottom: 8.5rem;
    }

    /* CHAT */
    div[data-testid="stChatMessage"] {
        border: 1px solid #eef0f2;
        border-radius: 20px;
        padding: 0.65rem 0.8rem;
        margin-bottom: 0.55rem;
        background: #fff;
    }

    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: var(--blue-soft);
    }

    /* Khung nhập dưới cùng giống ChatGPT */
    div[data-testid="stChatInput"] {
        max-width: 860px;
        margin: 0 auto;
    }

    div[data-testid="stChatInput"] > div {
        min-height: 58px;
        border-radius: 28px !important;
        border: 1px solid #d7dce1 !important;
        background: #fff !important;
        box-shadow: 0 8px 28px rgba(15,23,42,0.12);
    }

    div[data-testid="stChatInput"] textarea {
        padding-top: 0.95rem !important;
        padding-bottom: 0.85rem !important;
    }

    /* SIDEBAR */
    .sidebar-brand {
        font-size: 1.05rem;
        font-weight: 800;
        padding: 0.2rem 0 0.75rem 0;
    }

    [data-testid="stSidebar"] .stButton > button {
        border-radius: 12px;
        min-height: 2.6rem;
        text-align: left;
    }

    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: #111827;
        border-color: #111827;
    }

    /* Nút xóa cuộc trò chuyện bên cạnh tiêu đề */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        gap: 0.35rem;
        align-items: center;
    }

    [data-testid="stSidebar"] [data-testid="column"]:last-child .stButton > button {
        min-height: 2.6rem;
        padding-left: 0.35rem;
        padding-right: 0.35rem;
        border-radius: 10px;
    }

    /* PANEL PHẢI */
    .right-panel-title {
        font-size: 0.95rem;
        font-weight: 750;
        margin-bottom: 0.6rem;
    }

    .info-card {
        border: 1px solid var(--border);
        border-radius: 16px;
        background: var(--panel);
        padding: 0.85rem;
        margin-bottom: 0.7rem;
    }

    .info-label {
        color: var(--muted);
        font-size: 0.74rem;
        margin-bottom: 0.12rem;
    }

    .info-value {
        font-size: 0.86rem;
        font-weight: 650;
        word-break: break-word;
    }

    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #22c55e;
        margin-right: 6px;
    }

    .small-note {
        color: var(--muted);
        font-size: 0.74rem;
        line-height: 1.45;
    }

    @media (max-width: 900px) {
        [data-testid="stMainBlockContainer"] {
            padding-top: 1rem;
            padding-bottom: 8rem;
        }

        .block-container {
            padding-left: 0.75rem;
            padding-right: 0.75rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HÀM DỮ LIỆU
# =========================================================
def now_text() -> str:
    return datetime.now().isoformat(timespec="seconds")


def new_database() -> dict[str, Any]:
    return {
        "active_id": None,
        "vector_store_id": DEFAULT_VECTOR_STORE_ID,
        "uploaded_files": [],
        "conversations": {},
    }


def save_database(database: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = DATA_FILE.with_suffix(".tmp")
    temp_path.write_text(
        json.dumps(database, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp_path.replace(DATA_FILE)


def load_database() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not DATA_FILE.exists():
        database = new_database()
        save_database(database)
        return database

    try:
        database = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        database = new_database()

    database.setdefault("active_id", None)
    database.setdefault("vector_store_id", DEFAULT_VECTOR_STORE_ID)
    database.setdefault("uploaded_files", [])
    database.setdefault("conversations", {})
    return database


def create_conversation(
    database: dict[str, Any],
    title: str = "Yêu cầu hỗ trợ mới",
) -> str:
    conversation_id = uuid.uuid4().hex
    database["conversations"][conversation_id] = {
        "id": conversation_id,
        "title": title,
        "created_at": now_text(),
        "updated_at": now_text(),
        "messages": [],
    }
    database["active_id"] = conversation_id
    save_database(database)
    return conversation_id


def get_active_conversation(database: dict[str, Any]) -> dict[str, Any]:
    active_id = database.get("active_id")
    if not active_id or active_id not in database["conversations"]:
        active_id = create_conversation(database)
    return database["conversations"][active_id]


def shorten_title(text: str, max_length: int = 38) -> str:
    text = " ".join(text.split())
    return text if len(text) <= max_length else text[: max_length - 1].rstrip() + "…"


def append_message(
    database: dict[str, Any],
    conversation_id: str,
    role: str,
    content: str,
) -> None:
    conversation = database["conversations"][conversation_id]
    conversation["messages"].append(
        {
            "role": role,
            "content": content,
            "created_at": now_text(),
        }
    )
    conversation["updated_at"] = now_text()

    # Cập nhật tên trong mục "Trò chuyện gần đây" theo câu hỏi mới nhất
    if role == "user":
        conversation["title"] = shorten_title(content)

    save_database(database)


# =========================================================
# OPENAI
# =========================================================
def get_api_key() -> str:
    try:
        secret_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        secret_key = ""
    return secret_key or os.getenv("OPENAI_API_KEY", "")


@st.cache_resource(show_spinner=False)
def create_openai_client(api_key: str) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        timeout=45.0,
        max_retries=1,
    )


def get_client() -> OpenAI:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "Chưa khai báo OPENAI_API_KEY trong biến môi trường "
            "hoặc file .streamlit/secrets.toml."
        )
    return create_openai_client(api_key)


def ensure_vector_store(client: OpenAI, database: dict[str, Any]) -> str:
    vector_store_id = database.get("vector_store_id", "").strip()
    if vector_store_id:
        return vector_store_id

    vector_store = client.vector_stores.create(
        name="Kho tài liệu CCTL_QNG",
        description="Kho tài liệu phục vụ công tác tham mưu Chi cục Thủy lợi.",
    )
    database["vector_store_id"] = vector_store.id
    save_database(database)
    return vector_store.id


def upload_document(
    client: OpenAI,
    database: dict[str, Any],
    uploaded_file: Any,
) -> None:
    vector_store_id = ensure_vector_store(client, database)
    suffix = Path(uploaded_file.name).suffix

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        temp_path = Path(temp_file.name)

    try:
        with temp_path.open("rb") as file_handle:
            openai_file = client.files.create(
                file=file_handle,
                purpose="assistants",
            )

        client.vector_stores.files.create_and_poll(
            vector_store_id=vector_store_id,
            file_id=openai_file.id,
        )

        database["uploaded_files"].append(
            {
                "name": uploaded_file.name,
                "openai_file_id": openai_file.id,
                "uploaded_at": now_text(),
            }
        )
        save_database(database)
    finally:
        temp_path.unlink(missing_ok=True)


def build_api_input(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in messages[-12:]
        if message["role"] in {"user", "assistant"}
    ]


def stream_openai_answer(
    client: OpenAI,
    database: dict[str, Any],
    messages: list[dict[str, Any]],
    *,
    use_file_search: bool,
    fast_mode: bool,
):
    model = FAST_MODEL if fast_mode else DEEP_MODEL

    request: dict[str, Any] = {
        "model": model,
        "instructions": SYSTEM_INSTRUCTIONS,
        "input": build_api_input(messages),
        "stream": True,
        "reasoning": {"effort": "minimal" if fast_mode else "medium"},
        "text": {"verbosity": "low" if fast_mode else "high"},
        "max_output_tokens": 900 if fast_mode else 2400,
    }

    vector_store_id = database.get("vector_store_id", "").strip()
    if use_file_search and vector_store_id:
        request["tools"] = [
            {
                "type": "file_search",
                "vector_store_ids": [vector_store_id],
                "max_num_results": 8,
            }
        ]

    stream = client.responses.create(**request)

    for event in stream:
        if event.type == "response.output_text.delta":
            yield event.delta


# =========================================================
# KHỞI TẠO SESSION
# =========================================================
if "database" not in st.session_state:
    st.session_state.database = load_database()

database = st.session_state.database
conversation = get_active_conversation(database)


# =========================================================
# SIDEBAR TRÁI
# =========================================================
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">💧 Trợ lý CCTL_QNG</div>
        <div class="sidebar-author">
            Được xây dựng và phát triển bởi Hồ Hải Khôi Anh
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "💧  Yêu cầu hỗ trợ tham mưu mới",
        use_container_width=True,
        type="primary",
    ):
        create_conversation(database)
        st.rerun()

    st.markdown("##### Trò chuyện gần đây")

    conversations = sorted(
        [
            item
            for item in database["conversations"].values()
            if item.get("messages")
        ],
        key=lambda item: item.get("updated_at", ""),
        reverse=True,
    )[:15]

    for item in conversations:
        selected = item["id"] == database["active_id"]
        col_open, col_delete = st.columns([5.8, 1])

        with col_open:
            if st.button(
                item["title"],
                key=f"open_{item['id']}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                database["active_id"] = item["id"]
                save_database(database)
                st.rerun()

        with col_delete:
            if st.button(
                "🗑️",
                key=f"delete_{item['id']}",
                help="Xóa cuộc trò chuyện này",
                use_container_width=True,
            ):
                database["conversations"].pop(item["id"], None)

                if database.get("active_id") == item["id"]:
                    database["active_id"] = None

                save_database(database)
                st.rerun()

    st.divider()
    st.markdown("##### Chế độ trả lời")

    answer_mode = st.radio(
        "Chọn chế độ",
        options=["⚡ Nhanh", "📚 Chuyên sâu"],
        index=0,
        label_visibility="collapsed",
        help=(
            "Chế độ Nhanh dùng model gọn và không tra kho tài liệu. "
            "Chế độ Chuyên sâu dùng model tốt hơn và tự tra tài liệu đã nạp."
        ),
    )

    fast_mode = answer_mode == "⚡ Nhanh"
    use_file_search = answer_mode == "📚 Chuyên sâu"

    if fast_mode:
        st.caption("Phù hợp câu hỏi hằng ngày, phản hồi nhanh.")
    else:
        st.caption("Phù hợp tra cứu hồ sơ, văn bản và soạn thảo quan trọng.")

    st.divider()
    st.markdown("##### Tài liệu dùng chung")

    uploaded_files = st.file_uploader(
        "Tải tài liệu",
        type=["pdf", "docx", "doc", "txt", "md", "csv", "xlsx"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files and st.button(
        "Đưa tài liệu vào kho",
        use_container_width=True,
    ):
        try:
            client = get_client()
            progress = st.progress(0)
            status_box = st.empty()

            for index, uploaded_file in enumerate(uploaded_files, start=1):
                status_box.write(f"Đang xử lý: {uploaded_file.name}")
                upload_document(client, database, uploaded_file)
                progress.progress(index / len(uploaded_files))

            status_box.success("Đã đưa tài liệu vào kho.")
            st.rerun()
        except Exception as error:
            st.error(f"Không thể tải tài liệu: {error}")

    if database["uploaded_files"]:
        with st.expander(f"{len(database['uploaded_files'])} tài liệu đã nạp"):
            for file_info in database["uploaded_files"][-20:]:
                st.caption(f"• {file_info['name']}")

    st.divider()
    current_model = FAST_MODEL if fast_mode else DEEP_MODEL
    st.caption(f"Model đang dùng: {current_model}")


# =========================================================
# KHU VỰC TRÒ CHUYỆN
# =========================================================
if not conversation["messages"]:
    with st.chat_message("assistant", avatar="💧"):
        st.markdown(
            """Xin chào! Tôi là trợ lý hỗ trợ công việc Chi cục Thủy lợi tỉnh Quảng Ngãi.

Anh có thể hỏi về thủy lợi, đê điều, phòng chống thiên tai, tài nguyên nước, khí tượng thủy văn hoặc các tài liệu đã đưa vào kho."""
        )
else:
    visible_messages = conversation["messages"][-30:]
    hidden_count = len(conversation["messages"]) - len(visible_messages)

    if hidden_count > 0:
        st.caption(f"Đã ẩn {hidden_count} tin nhắn cũ để tăng tốc hiển thị.")

    for message in visible_messages:
        avatar = "👤" if message["role"] == "user" else "💧"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

# Điểm neo cuối cuộc trò chuyện
st.markdown('<div id="chat-bottom-anchor"></div>', unsafe_allow_html=True)

# Tự động cuộn xuống tin nhắn mới nhất
components.html(
    """
    <script>
    setTimeout(() => {
        const anchor = window.parent.document.getElementById("chat-bottom-anchor");
        if (anchor) {
            anchor.scrollIntoView({ behavior: "auto", block: "end" });
        }
    }, 80);
    </script>
    """,
    height=0,
)


# =========================================================
# Ô NHẬP DƯỚI CÙNG VÀ XỬ LÝ CÂU HỎI
# =========================================================
question = st.chat_input("Hỏi Trợ lý CCTL_QNG...")

if question:
    question = question.strip()

    if question:
        conversation_id = conversation["id"]
        append_message(database, conversation_id, "user", question)

        with st.chat_message("user", avatar="👤"):
            st.markdown(question)

        with st.chat_message("assistant", avatar="💧"):
            try:
                client = get_client()
                current_messages = database["conversations"][conversation_id]["messages"]

                answer = st.write_stream(
                    stream_openai_answer(
                        client,
                        database,
                        current_messages,
                        use_file_search=use_file_search,
                        fast_mode=fast_mode,
                    )
                )

                if not answer:
                    answer = "Tôi chưa tạo được câu trả lời. Anh vui lòng thử lại."
                    st.markdown(answer)

            except Exception as error:
                answer = (
                    "Không thể kết nối hoặc xử lý yêu cầu với OpenAI. "
                    f"Chi tiết lỗi: `{error}`"
                )
                st.error(answer)

        append_message(database, conversation_id, "assistant", answer)
        st.rerun()

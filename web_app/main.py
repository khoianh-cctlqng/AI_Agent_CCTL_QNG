from __future__ import annotations

import json
import os
import re
import tempfile
import httpx
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
    initial_sidebar_state="collapsed",
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

    /* GIAO DIỆN HỘI THOẠI THEO MẪU ĐÃ THỐNG NHẤT */
    div[data-testid="stChatMessage"] {
        border: 1px solid #e4e8ee !important;
        border-radius: 18px !important;
        padding: 0.78rem 0.9rem !important;
        margin-bottom: 0.72rem !important;
        background: #ffffff !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.035);
    }

    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: #ffffff !important;
        border-color: #ead9ab !important;
    }

    div[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarUser"],
    div[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarAssistant"] {
        width: 2.35rem !important;
        height: 2.35rem !important;
        min-width: 2.35rem !important;
        border-radius: 12px !important;
        border: 1px solid #dde3ea;
        background: #f8fafc !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 1.35rem !important;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.05);
    }

    div[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarUser"] {
        background: #fff8dc !important;
        border-color: #f0c85a !important;
    }

    div[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarAssistant"] {
        background: #eef7ff !important;
        border-color: #cfe6fb !important;
    }

    div[data-testid="stChatMessage"] p,
    div[data-testid="stChatMessage"] li {
        font-size: 0.97rem;
        line-height: 1.58;
    }

    div[data-testid="stChatInput"] > div {
        border-radius: 24px !important;
        border: 1px solid #d8dee6 !important;
        box-shadow: 0 6px 22px rgba(15, 23, 42, 0.08) !important;
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


    /* Màn hình chào theo mẫu điện thoại */
    .welcome-shell {
        width: min(100%, 680px);
        margin: 0 auto;
        text-align: center;
        padding: 2.9rem 0.55rem 0.35rem;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .welcome-logo {
        width: 84px;
        height: 84px;
        object-fit: contain;
        display: block;
        margin: 0 auto 0.45rem;
        align-self: center;
        transform: translateX(-1px);
        filter: drop-shadow(0 2px 5px rgba(0, 91, 150, 0.12));
    }

    .welcome-shell .welcome-title {
        display: block;
        width: 100%;
        text-align: center !important;
        font-size: clamp(1.26rem, 4vw, 1.9rem);
        line-height: 1.02;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #005B96 !important;
        -webkit-text-fill-color: #005B96 !important;
        margin: 0 auto 0.52rem;
    }

    .welcome-card {
        width: min(100%, 610px);
        margin: 0 auto 0.42rem;
        padding: 0.62rem 0.82rem;
        border: 1px solid #e3e7eb;
        border-radius: 18px;
        background: rgba(255,255,255,0.99);
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.035);
        color: #222222;
        font-size: clamp(0.78rem, 2.7vw, 0.94rem);
        line-height: 1.2;
        text-align: center;
    }

    .welcome-card-large {
        padding-top: 0.66rem;
        padding-bottom: 0.66rem;
    }

    /* Khi chưa có hội thoại, tạo khoảng thở như mẫu */
    .welcome-spacer {
        height: 0;
    }

    @media (max-width: 700px) {
        [data-testid="stMainBlockContainer"] {
            padding-top: 0.05rem;
            padding-left: 0.55rem;
            padding-right: 0.55rem;
            padding-bottom: 6.1rem;
        }

        .welcome-shell {
            padding-top: 3.15rem;
            padding-left: 0.18rem;
            padding-right: 0.18rem;
            padding-bottom: 0.18rem;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .welcome-logo {
            width: 78px;
            height: 78px;
            margin: 0 auto 0.38rem;
            align-self: center;
            transform: translateX(-1px);
        }

        .welcome-shell .welcome-title {
            display: block;
            width: 100%;
            text-align: center !important;
            font-size: 1.22rem;
            margin: 0 auto 0.46rem;
            color: #005B96 !important;
            -webkit-text-fill-color: #005B96 !important;
        }

        .welcome-card {
            width: 100%;
            border-radius: 17px;
            padding: 0.56rem 0.68rem;
            margin-bottom: 0.38rem;
            font-size: 0.78rem;
            line-height: 1.18;
            text-align: center;
        }

        .welcome-card-large {
            padding-top: 0.62rem;
            padding-bottom: 0.62rem;
        }

        div[data-testid="stChatInput"] {
            width: calc(100% - 1rem);
            bottom: 0.35rem !important;
        }

        div[data-testid="stChatInput"] > div {
            min-height: 50px;
            border-radius: 25px !important;
            box-shadow: none;
        }

        [data-testid="stChatInputTextArea"] {
            font-size: 0.84rem !important;
            line-height: 1.12 !important;
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

    configured_vector_store_id = get_configured_vector_store_id()
    if configured_vector_store_id:
        database["vector_store_id"] = configured_vector_store_id

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


def get_configured_vector_store_id() -> str:
    """Đọc ID kho tài liệu cố định từ Streamlit Secrets hoặc biến môi trường."""
    try:
        secret_id = st.secrets.get("OPENAI_VECTOR_STORE_ID", "")
    except Exception:
        secret_id = ""

    return (
        str(secret_id).strip()
        or os.getenv("OPENAI_VECTOR_STORE_ID", "").strip()
        or DEFAULT_VECTOR_STORE_ID
    )


@st.cache_resource(show_spinner=False)
def create_openai_client(api_key: str) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        timeout=120.0,
        max_retries=2,
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
    configured_vector_store_id = get_configured_vector_store_id()
    if configured_vector_store_id:
        database["vector_store_id"] = configured_vector_store_id
        save_database(database)
        return configured_vector_store_id

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
    """
    Tải tài liệu lên OpenAI và giữ nguyên tên file gốc.

    Trước đây NamedTemporaryFile tạo tên dạng tmpxxxx.doc, nên OpenAI lưu luôn
    tên tạm đó. Bản này tạo một thư mục tạm nhưng tên file bên trong vẫn là
    tên người dùng đã tải lên.
    """
    vector_store_id = ensure_vector_store(client, database)

    original_name = Path(uploaded_file.name).name
    safe_name = re.sub(r'[<>:"/\\\\|?*]+', "_", original_name).strip()
    if not safe_name:
        safe_name = f"tai_lieu_{uuid.uuid4().hex[:8]}.bin"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / safe_name
        temp_path.write_bytes(uploaded_file.getbuffer())

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
            "name": original_name,
            "openai_file_id": openai_file.id,
            "uploaded_at": now_text(),
        }
    )
    save_database(database)


def build_api_input(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in messages[-12:]
        if message["role"] in {"user", "assistant"}
    ]


def question_requests_documents(question: str) -> bool:
    """Tự bật tra cứu kho khi câu hỏi rõ ràng yêu cầu dùng tài liệu."""
    normalized = " ".join(question.lower().split())
    terms = [
        "theo tài liệu", "tài liệu dùng chung", "trong kho", "theo hồ sơ",
        "theo văn bản", "quyết định", "quy trình", "quy định", "biên bản",
        "báo cáo", "phụ lục", "file pdf", "file word", "tài liệu đã nạp",
        "căn cứ tài liệu", "tra cứu", "liên hồ",
    ]
    return any(term in normalized for term in terms)


def search_vector_store_context(
    client: OpenAI,
    vector_store_id: str,
    question: str,
    filename_map: dict[str, str] | None = None,
) -> tuple[str, list[str], list[dict[str, Any]]]:
    """
    Tìm trực tiếp trong kho bằng nhiều cách diễn đạt.
    Trả về:
    - các đoạn liên quan;
    - tên tài liệu;
    - danh sách file ứng viên để có thể đọc toàn bộ khi cần.
    """
    expanded_queries = [
        question,
        (
            question
            + " họ tên tên cá nhân chức danh chức vụ lãnh đạo "
              "Chi cục trưởng Phó Chi cục trưởng trưởng phòng phó trưởng phòng"
        ),
        (
            "danh sách cán bộ công chức viên chức; họ và tên; chức vụ; "
            "chức danh; đơn vị công tác; cơ cấu tổ chức Chi cục Thủy lợi"
        ),
    ]

    collected: list[tuple[float, str, str, str]] = []
    seen_chunks: set[str] = set()
    search_errors: list[str] = []

    for query in expanded_queries:
        try:
            page = client.vector_stores.search(
                vector_store_id=vector_store_id,
                query=query,
                max_num_results=20,
                rewrite_query=True,
            )
        except Exception as error:
            search_errors.append(str(error))
            continue

        for result in getattr(page, "data", []) or []:
            file_id = getattr(result, "file_id", "") or ""
            raw_filename = (
                getattr(result, "filename", "")
                or "Tài liệu không rõ tên"
            )
            filename = (
                (filename_map or {}).get(file_id)
                or raw_filename
            )
            score = float(getattr(result, "score", 0.0) or 0.0)

            parts: list[str] = []
            for item in getattr(result, "content", []) or []:
                item_text = getattr(item, "text", "") or ""
                if item_text.strip():
                    parts.append(item_text.strip())

            chunk_text = "\n".join(parts).strip()
            if not chunk_text:
                continue

            fingerprint = f"{file_id}|{chunk_text[:300]}"
            if fingerprint in seen_chunks:
                continue

            seen_chunks.add(fingerprint)
            collected.append((score, file_id, filename, chunk_text))

    collected.sort(key=lambda row: row[0], reverse=True)
    selected = collected[:20]

    if not selected:
        if search_errors:
            unique_errors = list(dict.fromkeys(search_errors))
            raise RuntimeError(
                "Không gọi được chức năng tìm kiếm Vector Store: "
                + " | ".join(unique_errors[:2])
            )
        return "", [], []

    filenames: list[str] = []
    candidates_by_file: dict[str, dict[str, Any]] = {}
    context_blocks: list[str] = []

    for index, (score, file_id, filename, chunk_text) in enumerate(selected, start=1):
        if filename not in filenames:
            filenames.append(filename)

        if file_id:
            current = candidates_by_file.get(file_id)
            if current is None or score > current["score"]:
                candidates_by_file[file_id] = {
                    "file_id": file_id,
                    "filename": filename,
                    "score": score,
                }

        context_blocks.append(
            f"[Kết quả {index} | Tài liệu: {filename} | Điểm: {score:.3f}]\n"
            f"{chunk_text}"
        )

    candidates = sorted(
        candidates_by_file.values(),
        key=lambda item: item["score"],
        reverse=True,
    )

    return "\n\n".join(context_blocks), filenames, candidates


def should_read_full_document(question: str) -> bool:
    """
    Các câu hỏi cần rà soát đầy đủ thường dễ bị bỏ sót nếu chỉ dùng vài đoạn RAG.
    """
    normalized = " ".join(question.lower().split())
    trigger_terms = [
        "ai ",
        "là ai",
        "họ tên",
        "tên và chức danh",
        "chức danh",
        "chức vụ",
        "danh sách",
        "liệt kê",
        "từng cá nhân",
        "từng người",
        "bao nhiêu",
        "mấy ",
        "toàn bộ",
        "đầy đủ",
        "cuối tài liệu",
        "phía sau",
        "trong bảng",
        "phụ lục",
        "chức năng nhiệm vụ",
        "chức năng, nhiệm vụ",
        "cơ cấu tổ chức",
        "các phòng",
        "các đơn vị",
        "theo quy định",
        "theo tài liệu",
        "theo văn bản",
        "quy trình",
        "gồm những",
        "có những",
    ]
    return any(term in normalized for term in trigger_terms)


def fetch_parsed_vector_file_content(
    api_key: str,
    vector_store_id: str,
    file_id: str,
) -> str:
    """
    Lấy toàn bộ phần nội dung đã được OpenAI phân tích của một file trong Vector Store.
    Đây là lớp dự phòng khi tìm kiếm theo đoạn có nguy cơ bỏ sót bảng hoặc danh sách.
    """
    url = (
        f"https://api.openai.com/v1/vector_stores/"
        f"{vector_store_id}/files/{file_id}/content"
    )

    response = httpx.get(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=60.0,
    )
    response.raise_for_status()
    payload = response.json()

    parts: list[str] = []
    for item in payload.get("content", []) or []:
        item_text = item.get("text", "")
        if item_text and item_text.strip():
            parts.append(item_text.strip())

    return "\n\n".join(parts)


def build_full_document_context(
    api_key: str,
    vector_store_id: str,
    candidates: list[dict[str, Any]],
    *,
    max_files: int = 2,
    max_total_chars: int = 120_000,
) -> tuple[str, list[str], list[str]]:
    """
    Đọc toàn bộ nội dung đã phân tích của tối đa vài file phù hợp nhất.
    Trả thêm danh sách lỗi để có thể chẩn đoán thay vì bỏ qua âm thầm.
    """
    blocks: list[str] = []
    filenames: list[str] = []
    errors: list[str] = []
    total_chars = 0

    for candidate in candidates[:max_files]:
        file_id = candidate.get("file_id", "")
        filename = candidate.get("filename", "Tài liệu không rõ tên")
        if not file_id:
            errors.append(f"{filename}: không có file_id.")
            continue

        try:
            full_text = fetch_parsed_vector_file_content(
                api_key,
                vector_store_id,
                file_id,
            )
        except Exception as error:
            errors.append(f"{filename}: {error}")
            continue

        if not full_text.strip():
            errors.append(
                f"{filename}: OpenAI không trả về phần chữ đã phân tích."
            )
            continue

        remaining = max_total_chars - total_chars
        if remaining <= 0:
            break

        clipped = full_text[:remaining]
        blocks.append(
            f"[TOÀN VĂN ĐÃ PHÂN TÍCH | Tài liệu: {filename}]\\n{clipped}"
        )
        filenames.append(filename)
        total_chars += len(clipped)

    return "\\n\\n".join(blocks), filenames, errors


def stream_openai_answer(
    client: OpenAI,
    database: dict[str, Any],
    messages: list[dict[str, Any]],
    *,
    use_file_search: bool,
    fast_mode: bool,
):
    model = FAST_MODEL if fast_mode else DEEP_MODEL

    api_input = build_api_input(messages)
    instructions = SYSTEM_INSTRUCTIONS
    vector_store_id = ""
    diagnostics: dict[str, Any] = {
        "enabled": use_file_search,
        "model": model,
        "vector_store_id": "",
        "question": "",
        "manual_search_files": [],
        "candidate_files": [],
        "retrieved_context_chars": 0,
        "full_document_files": [],
        "full_document_chars": 0,
        "full_document_errors": [],
        "native_file_search_enabled": False,
    }

    if use_file_search:
        vector_store_id = (
            get_configured_vector_store_id()
            or database.get("vector_store_id", "").strip()
        )
        if not vector_store_id:
            raise RuntimeError(
                "Chưa xác định được OPENAI_VECTOR_STORE_ID cho kho tài liệu."
            )

        diagnostics["vector_store_id"] = vector_store_id

        latest_question = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                latest_question = str(message.get("content", "")).strip()
                break

        diagnostics["question"] = latest_question

        original_filename_map = {
            str(item.get("openai_file_id", "")).strip(): str(
                item.get("name", "")
            ).strip()
            for item in database.get("uploaded_files", [])
            if item.get("openai_file_id") and item.get("name")
        }

        (
            retrieved_context,
            source_files,
            candidates,
        ) = search_vector_store_context(
            client,
            vector_store_id,
            latest_question,
            filename_map=original_filename_map,
        )

        diagnostics["manual_search_files"] = source_files
        diagnostics["candidate_files"] = [
            {
                "filename": item.get("filename", ""),
                "score": round(float(item.get("score", 0.0) or 0.0), 3),
            }
            for item in candidates
        ]
        diagnostics["retrieved_context_chars"] = len(retrieved_context)

        full_document_context = ""
        full_document_files: list[str] = []
        full_document_errors: list[str] = []

        if candidates:
            # Câu hỏi tổng hợp, danh sách, chức danh, số lượng... đọc tối đa 2 file.
            # Các câu hỏi còn lại vẫn đọc toàn văn file phù hợp nhất để tránh
            # trường hợp chỉ lấy được vài đoạn rời rạc.
            full_file_limit = (
                2 if should_read_full_document(latest_question) else 1
            )
            full_char_limit = (
                120_000 if full_file_limit == 2 else 80_000
            )

            (
                full_document_context,
                full_document_files,
                full_document_errors,
            ) = build_full_document_context(
                get_api_key(),
                vector_store_id,
                candidates,
                max_files=full_file_limit,
                max_total_chars=full_char_limit,
            )

        diagnostics["full_document_files"] = full_document_files
        diagnostics["full_document_chars"] = len(full_document_context)
        diagnostics["full_document_errors"] = full_document_errors

        combined_context_parts: list[str] = []
        if retrieved_context:
            combined_context_parts.append(
                "CÁC ĐOẠN TÌM KIẾM LIÊN QUAN:\\n" + retrieved_context
            )
        if full_document_context:
            combined_context_parts.append(
                "NỘI DUNG TOÀN FILE DỰ PHÒNG:\\n" + full_document_context
            )

        combined_context = "\\n\\n".join(combined_context_parts).strip()

        if combined_context:
            api_input.append(
                {
                    "role": "user",
                    "content": (
                        "Dưới đây là kết quả tra cứu từ kho tài liệu. "
                        "Hãy ưu tiên dùng nội dung này để trả lời câu hỏi trước đó. "
                        "Kiểm tra kỹ bảng, danh sách, phần cuối tài liệu, họ tên, "
                        "chức danh, ngày tháng và các dòng liền kề.\\n\\n"
                        f"{combined_context}"
                    ),
                }
            )

            all_sources: list[str] = []
            for name in source_files + full_document_files:
                if name not in all_sources:
                    all_sources.append(name)

            source_text = ", ".join(all_sources)
            instructions += f"""

YÊU CẦU TRẢ LỜI THEO KHO TÀI LIỆU:
- Ưu tiên nội dung tra cứu đã được cung cấp.
- Nếu nội dung cung cấp chưa đủ, bắt buộc dùng công cụ file_search để tra tiếp trong kho.
- Đọc kỹ cả bảng, danh sách, dòng liền trước và liền sau.
- Ghép đúng họ tên với chức danh và mốc thời gian tương ứng.
- Không tự suy đoán ngoài tài liệu.
- Cuối câu trả lời ghi chính xác: "Tài liệu đã tra: {source_text}".
- Chỉ dùng đúng tên tài liệu trong dòng trên; không tự thay bằng tên tạm kiểu tmp... hoặc tên do hệ thống suy đoán.
- Nếu có mâu thuẫn, nêu rõ từng phương án và tài liệu tương ứng.
- Phải kết thúc trọn câu, trọn ý; không dừng giữa câu hoặc giữa danh sách.
"""
        else:
            instructions += """

YÊU CẦU TRẢ LỜI THEO KHO TÀI LIỆU:
- Kết quả tìm kiếm thủ công chưa lấy được đoạn phù hợp.
- Bắt buộc sử dụng công cụ file_search để tìm trực tiếp trong Vector Store trước khi trả lời.
- Chỉ kết luận theo nội dung tìm được; không tự suy đoán.
"""

    request: dict[str, Any] = {
        "model": model,
        "instructions": instructions,
        "input": api_input,
        "stream": True,
        "reasoning": {"effort": "minimal" if fast_mode else "medium"},
        "text": {"verbosity": "low" if fast_mode else "high"},
        "max_output_tokens": 1400 if fast_mode else 5000,
    }

    if use_file_search and vector_store_id:
        request["tools"] = [
            {
                "type": "file_search",
                "vector_store_ids": [vector_store_id],
                "max_num_results": 20,
            }
        ]
        diagnostics["native_file_search_enabled"] = True

    st.session_state["rag_diagnostics"] = diagnostics

    stream = client.responses.create(**request)

    for event in stream:
        event_type = getattr(event, "type", "")

        if event_type == "response.output_text.delta":
            yield event.delta

        elif event_type == "response.file_search_call.searching":
            diagnostics["native_file_search_status"] = "Đang tìm kiếm"

        elif event_type == "response.file_search_call.completed":
            diagnostics["native_file_search_status"] = "Hoàn tất"

        elif event_type == "response.file_search_call.failed":
            diagnostics["native_file_search_status"] = "Lỗi"

        st.session_state["rag_diagnostics"] = diagnostics


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
        index=1,
        label_visibility="collapsed",
        help=(
            "Chế độ Nhanh dùng model gọn và không tra kho tài liệu. "
            "Chế độ Chuyên sâu dùng model tốt hơn và tự tra tài liệu đã nạp."
        ),
    )

    fast_mode = answer_mode == "⚡ Nhanh"
    use_file_search = answer_mode == "📚 Chuyên sâu"

    if fast_mode:
        st.caption("Phù hợp câu hỏi hằng ngày. Câu hỏi có cụm 'theo tài liệu' vẫn tự động tra kho.")
    else:
        st.caption("Đang bật tra cứu kho tài liệu cho mọi câu hỏi.")

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
            visible_files = list(reversed(database["uploaded_files"][-20:]))

            for index, file_info in enumerate(visible_files):
                file_id = str(file_info.get("openai_file_id", "")).strip()
                file_name = str(file_info.get("name", "Tài liệu không rõ tên"))

                col_name, col_delete = st.columns([8, 1])
                with col_name:
                    st.caption(f"• {file_name}")

                with col_delete:
                    if st.button(
                        "🗑️",
                        key=f"request_delete_document_{file_id}_{index}",
                        help=f"Yêu cầu xóa {file_name}",
                        use_container_width=True,
                    ):
                        st.session_state["pending_delete_document"] = {
                            "file_id": file_id,
                            "file_name": file_name,
                        }
                        st.rerun()

            pending_delete = st.session_state.get("pending_delete_document")
            if pending_delete:
                pending_file_id = str(
                    pending_delete.get("file_id", "")
                ).strip()
                pending_file_name = str(
                    pending_delete.get("file_name", "Tài liệu")
                )

                st.warning(
                    f"Xác nhận xóa **{pending_file_name}** khỏi kho tài liệu? "
                    "Thao tác này sẽ làm Agent không còn tra cứu file này."
                )
                confirm_col, cancel_col = st.columns(2)

                with confirm_col:
                    if st.button(
                        "Xóa tài liệu",
                        key="confirm_delete_document",
                        type="primary",
                        use_container_width=True,
                    ):
                        try:
                            if not pending_file_id:
                                raise RuntimeError(
                                    "Tài liệu không có OpenAI file ID để xóa."
                                )

                            client = get_client()
                            vector_store_id = ensure_vector_store(
                                client,
                                database,
                            )

                            # Gỡ khỏi Vector Store để Agent ngừng tra cứu.
                            client.vector_stores.files.delete(
                                vector_store_id=vector_store_id,
                                file_id=pending_file_id,
                            )

                            # Xóa file gốc khỏi OpenAI để tránh lưu thừa.
                            try:
                                client.files.delete(pending_file_id)
                            except Exception:
                                # File đã được gỡ khỏi kho là yêu cầu chính;
                                # lỗi xóa bản gốc không làm hỏng danh sách kho.
                                pass

                            database["uploaded_files"] = [
                                item
                                for item in database["uploaded_files"]
                                if str(item.get("openai_file_id", ""))
                                != pending_file_id
                            ]
                            save_database(database)
                            st.session_state.pop(
                                "pending_delete_document",
                                None,
                            )
                            st.success(
                                f"Đã xóa tài liệu: {pending_file_name}"
                            )
                            st.rerun()
                        except Exception as error:
                            st.error(
                                f"Không thể xóa {pending_file_name}: {error}"
                            )

                with cancel_col:
                    if st.button(
                        "Hủy",
                        key="cancel_delete_document",
                        use_container_width=True,
                    ):
                        st.session_state.pop(
                            "pending_delete_document",
                            None,
                        )
                        st.rerun()

    if st.button(
        "🔎 Kiểm tra kho tài liệu",
        use_container_width=True,
        help="Kiểm tra trực tiếp trạng thái kho tài liệu trên OpenAI.",
    ):
        try:
            client = get_client()
            vector_store_id = ensure_vector_store(client, database)
            vector_store = client.vector_stores.retrieve(
                vector_store_id=vector_store_id
            )
            counts = vector_store.file_counts
            st.success(
                "Kho đang hoạt động — "
                f"Hoàn tất: {counts.completed}; "
                f"Đang xử lý: {counts.in_progress}; "
                f"Lỗi: {counts.failed}; "
                f"Tổng: {counts.total}."
            )
            st.caption(f"Vector Store ID: {vector_store_id}")
        except Exception as error:
            st.error(f"Không kiểm tra được kho tài liệu: {error}")

    if use_file_search and st.session_state.get("rag_diagnostics"):
        diagnostic = st.session_state["rag_diagnostics"]
        with st.expander("🧪 Chẩn đoán tra cứu tài liệu", expanded=False):
            st.caption(
                f"Vector Store: {diagnostic.get('vector_store_id') or 'Chưa xác định'}"
            )
            st.caption(
                "File tìm thấy: "
                f"{len(diagnostic.get('manual_search_files', []))}; "
                "Ký tự từ tìm kiếm: "
                f"{diagnostic.get('retrieved_context_chars', 0):,}; "
                "Ký tự toàn file: "
                f"{diagnostic.get('full_document_chars', 0):,}."
            )

            candidate_files = diagnostic.get("candidate_files", [])
            if candidate_files:
                st.markdown("**File ứng viên:**")
                for item in candidate_files[:8]:
                    st.caption(
                        f"• {item.get('filename', 'Không rõ tên')} "
                        f"— điểm {item.get('score', 0)}"
                    )
            else:
                st.warning("Tìm kiếm thủ công chưa trả về file ứng viên.")

            full_errors = diagnostic.get("full_document_errors", [])
            if full_errors:
                st.markdown("**Lỗi khi đọc toàn file:**")
                for error_text in full_errors[:5]:
                    st.error(error_text)

            native_status = diagnostic.get(
                "native_file_search_status",
                "Đã bật, chờ câu hỏi",
            )
            st.caption(f"File Search trực tiếp: {native_status}")

            if (
                diagnostic.get("retrieved_context_chars", 0) > 0
                and diagnostic.get("full_document_chars", 0) == 0
                and not full_errors
            ):
                st.info(
                    "Đã tìm được đoạn liên quan. Câu hỏi trước có thể chưa kích hoạt "
                    "đọc toàn văn; bản cập nhật mới sẽ luôn đọc ít nhất file phù hợp nhất."
                )

    st.divider()
    current_model = FAST_MODEL if fast_mode else DEEP_MODEL
    st.caption(f"Model đang dùng: {current_model}")


# =========================================================
# KHU VỰC TRÒ CHUYỆN
# =========================================================
if not conversation["messages"]:
    st.markdown(
        """
        <section class="welcome-shell">
            <div id="welcome-top-anchor" style="height:1px; scroll-margin-top:132px;"></div>
            <img class="welcome-logo" src="data:image/png;base64,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" alt="Logo Chi cục Thủy lợi Quảng Ngãi">
            <h1 class="welcome-title">Xin chào!</h1>
            <div class="welcome-card">
                Tôi là trợ lý hỗ trợ công việc của Chi cục Thủy lợi tỉnh Quảng Ngãi.
            </div>
            <div class="welcome-card welcome-card-large">
                Anh/chị có thể yêu cầu tôi tham mưu về thủy lợi, cấp nước sạch nông thôn, đê điều,
                phòng, chống thiên tai, tài nguyên nước, khí tượng thủy văn; quản lý chất lượng,
                thi công xây dựng và bảo trì công trình xây dựng chuyên ngành trên địa bàn tỉnh Quảng Ngãi.
            </div>
            <div class="welcome-spacer"></div>
        </section>
        """,
        unsafe_allow_html=True,
    )
else:
    visible_messages = conversation["messages"][-30:]
    hidden_count = len(conversation["messages"]) - len(visible_messages)

    if hidden_count > 0:
        st.caption(f"Đã ẩn {hidden_count} tin nhắn cũ để tăng tốc hiển thị.")

    for message in visible_messages:
        avatar = "👨🏻" if message["role"] == "user" else "💧"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

# Điều khiển vị trí cuộn:
# - Có hội thoại: cuộn xuống tin nhắn mới nhất.
# - Chưa có hội thoại: luôn đưa màn hình về logo ở đầu trang.
if conversation["messages"]:
    st.markdown('<div id="chat-bottom-anchor"></div>', unsafe_allow_html=True)

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
else:
    components.html(
        """
        <script>
        const forceWelcomeTop = () => {
            const parentWindow = window.parent;
            const parentDoc = parentWindow.document;

            const active = parentDoc.activeElement;
            if (active && typeof active.blur === "function") {
                active.blur();
            }

            parentDoc
                .querySelectorAll('textarea, input')
                .forEach((element) => {
                    if (typeof element.blur === "function") {
                        element.blur();
                    }
                });

            const welcomeAnchor =
                parentDoc.getElementById("welcome-top-anchor");

            if (welcomeAnchor) {
                welcomeAnchor.scrollIntoView({
                    behavior: "auto",
                    block: "start"
                });
            } else {
                parentWindow.scrollTo({
                    top: 0,
                    left: 0,
                    behavior: "auto"
                });
            }

            const main = parentDoc.querySelector(
                '[data-testid="stMain"], section.main, .main'
            );
            if (main) {
                main.scrollTop = 0;
            }
        };

        [0, 100, 300, 700, 1400, 2200].forEach((delay) => {
            setTimeout(forceWelcomeTop, delay);
        });

        window.parent.addEventListener("pageshow", forceWelcomeTop, {
            once: true
        });
        </script>
        """,
        height=0,
    )


# =========================================================
# Ô NHẬP DƯỚI CÙNG VÀ XỬ LÝ CÂU HỎI
# =========================================================
# Ô chat native của Streamlit:
# - Nút dấu cộng để đính kèm một hoặc nhiều tài liệu;
# - Shift + Enter để xuống dòng;
# - Enter để gửi.
chat_submission = st.chat_input(
    "Hỏi Trợ lý CCTL_QNG...",
    key="main_chat_input",
    accept_file="multiple",
    file_type=["pdf", "docx", "doc", "txt", "md", "csv", "xlsx"],
    max_upload_size=200,
)

question = ""
chat_files: list[Any] = []

if chat_submission:
    # Khi accept_file được bật, st.chat_input trả về đối tượng có
    # thuộc tính text và files.
    question = str(getattr(chat_submission, "text", "") or "").strip()
    chat_files = list(getattr(chat_submission, "files", []) or [])

    # Đưa ngay các file đính kèm ở khung chat vào Vector Store.
    upload_messages: list[str] = []
    if chat_files:
        try:
            client = get_client()

            for attached_file in chat_files:
                upload_document(client, database, attached_file)
                upload_messages.append(attached_file.name)

        except Exception as error:
            st.error(f"Không thể đưa file đính kèm vào kho: {error}")
            st.stop()

    # Cho phép chỉ đính kèm file mà không cần nhập câu hỏi.
    if not question and upload_messages:
        conversation_id = conversation["id"]
        attached_text = (
            "Đã đính kèm tài liệu: "
            + ", ".join(upload_messages)
        )
        append_message(
            database,
            conversation_id,
            "user",
            attached_text,
        )

        with st.chat_message("user", avatar="👤"):
            st.markdown(attached_text)

        answer = (
            "Tôi đã đưa tài liệu vào kho dùng chung. "
            "Anh/chị có thể đặt câu hỏi về nội dung tài liệu ngay bây giờ."
        )

        with st.chat_message("assistant", avatar="💧"):
            st.markdown(answer)

        append_message(
            database,
            conversation_id,
            "assistant",
            answer,
        )
        st.rerun()

if question:
    conversation_id = conversation["id"]

    # Ghi kèm tên file trong tin nhắn để lịch sử trò chuyện rõ ràng.
    displayed_question = question
    if chat_files:
        displayed_question += (
            "\n\n📎 **Tệp đính kèm:** "
            + ", ".join(file.name for file in chat_files)
        )

    append_message(database, conversation_id, "user", displayed_question)

    with st.chat_message("user", avatar="👤"):
        st.markdown(displayed_question)

    with st.chat_message("assistant", avatar="💧"):
        try:
            client = get_client()
            current_messages = database["conversations"][conversation_id]["messages"]

            # Có file vừa đính kèm thì luôn bật tra cứu kho cho câu hỏi này.
            auto_document_search = (
                bool(chat_files)
                or (
                    bool(database.get("uploaded_files"))
                    and question_requests_documents(question)
                )
            )
            effective_file_search = use_file_search or auto_document_search
            effective_fast_mode = fast_mode and not effective_file_search

            # Thu toàn bộ nội dung trước rồi mới hiển thị một lần.
            # Cách này tránh hiện tượng chữ/bullet bị ngắt quãng khi mạng chậm
            # hoặc từng delta Markdown được Streamlit vẽ chưa trọn vẹn.
            with st.spinner("Đang tổng hợp câu trả lời..."):
                answer_parts: list[str] = []
                for text_delta in stream_openai_answer(
                    client,
                    database,
                    current_messages,
                    use_file_search=effective_file_search,
                    fast_mode=effective_fast_mode,
                ):
                    if text_delta:
                        answer_parts.append(str(text_delta))

                answer = "".join(answer_parts).strip()

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

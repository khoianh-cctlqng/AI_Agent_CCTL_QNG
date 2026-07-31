import os
from pathlib import Path

from openai import OpenAI


VECTOR_STORE_NAME = "CCTLQNG_Kho_Tai_Lieu"
DOCUMENT_FOLDER = Path("tai_lieu")

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".txt",
    ".md",
}


def main():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("LỖI: Chưa tìm thấy OPENAI_API_KEY.")
        return

    client = OpenAI(api_key=api_key)

    if not DOCUMENT_FOLDER.exists():
        print("LỖI: Không tìm thấy thư mục tai_lieu.")
        return

    documents = [
        file_path
        for file_path in DOCUMENT_FOLDER.iterdir()
        if file_path.is_file()
        and file_path.suffix.lower() in ALLOWED_EXTENSIONS
    ]

    if not documents:
        print("LỖI: Thư mục tai_lieu chưa có tài liệu.")
        return

    vector_store = client.vector_stores.create(
        name=VECTOR_STORE_NAME
    )

    print("\nĐã tạo Vector Store")
    print("Tên:", vector_store.name)
    print("vector_store_id:", vector_store.id)

    file_streams = []

    try:
        for document in documents:
            print("Chuẩn bị tải:", document.name)
            file_streams.append(document.open("rb"))

        result = client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            files=file_streams,
        )

        print("\nKẾT QUẢ XỬ LÝ")
        print("Trạng thái:", result.status)
        print("Số lượng tệp:", result.file_counts)

        if result.status == "completed":
            print("\nTẠO VECTOR STORE THÀNH CÔNG")
            print("VECTOR_STORE_ID =", vector_store.id)
        else:
            print("\nTài liệu chưa xử lý thành công hoàn toàn.")

    finally:
        for file_stream in file_streams:
            file_stream.close()


if __name__ == "__main__":
    main()
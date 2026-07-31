import os

from openai import OpenAI


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    vector_store_id = os.getenv("OPENAI_VECTOR_STORE_ID")

    if not api_key:
        print("LỖI: Chưa có OPENAI_API_KEY.")
        return

    if not vector_store_id:
        print("LỖI: Chưa có OPENAI_VECTOR_STORE_ID.")
        return

    client = OpenAI(api_key=api_key)

    files = client.vector_stores.files.list(
        vector_store_id=vector_store_id
    )

    if not files.data:
        print("Vector Store không có tài liệu.")
        return

    file_id = files.data[0].id

    content = client.vector_stores.files.content(
        vector_store_id=vector_store_id,
        file_id=file_id,
    )

    print("FILE ID:", file_id)
    print("SỐ ĐOẠN NỘI DUNG:", len(content.data))
    print("=" * 70)

    for index, part in enumerate(content.data[:5], start=1):
        print(f"\nĐOẠN {index}")
        print("-" * 70)
        print(part.text[:2000])


if __name__ == "__main__":
    main()
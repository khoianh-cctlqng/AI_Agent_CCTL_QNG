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

    print("VECTOR STORE:", vector_store_id)
    print("SỐ TỆP:", len(files.data))

    for item in files.data:
        print("-" * 50)
        print("FILE ID:", item.id)
        print("TRẠNG THÁI:", item.status)
        print("LỖI:", item.last_error)

        file_info = client.files.retrieve(item.id)
        print("TÊN FILE:", file_info.filename)


if __name__ == "__main__":
    main()
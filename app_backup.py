import streamlit as st
from agents import Agent, Runner

st.set_page_config(
    page_title="AI Agent CCTLQNG",
    page_icon="💧"
)

agent = Agent(
    name="AI_Agent_CCTLQNG",
    instructions="""
Bạn là trợ lý AI hỗ trợ kỹ sư thủy lợi.
Trả lời bằng tiếng Việt, rõ ràng, chính xác.
Không tự bịa số liệu.
Nếu không đủ thông tin, phải nói rõ chưa đủ căn cứ.
"""
)

st.title("💧 AI Agent CCTLQNG")
st.caption("Trợ lý hỗ trợ công việc thủy lợi")

cau_hoi = st.text_area(
    "Nhập câu hỏi:",
    placeholder="Ví dụ: Hồ chứa thủy lợi có những nhiệm vụ gì?"
)

if st.button("Gửi câu hỏi"):
    if not cau_hoi.strip():
        st.warning("Anh chưa nhập câu hỏi.")
    else:
        with st.spinner("Agent đang xử lý..."):
            try:
                ket_qua = Runner.run_sync(agent, cau_hoi)
                st.subheader("Trả lời")
                st.write(ket_qua.final_output)
            except Exception as loi:
                st.error(f"Không chạy được Agent: {loi}")
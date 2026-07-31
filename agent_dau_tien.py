from agents import Agent, Runner

agent = Agent(
    name="AI_Agent_CCTLQNG",
    instructions="""
    Bạn là trợ lý AI hỗ trợ kỹ sư thủy lợi.
    Trả lời bằng tiếng Việt, rõ ràng và không tự bịa số liệu.
    """
)

cau_hoi = input("Nhập câu hỏi: ")

ket_qua = Runner.run_sync(agent, cau_hoi)

print("\nTrả lời:")
print(ket_qua.final_output)

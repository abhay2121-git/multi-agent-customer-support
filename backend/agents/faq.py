from backend.agents.base_agent import BaseAgent


class FAQAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="FAQAgent",
            domain="general FAQs, policies, company info, contact details"
        )

    def get_system_prompt(self) -> str:
        return (
            "You are TechMart's Information Assistant. You answer questions about "
            "TechMart's policies, contact information, working hours, and company info.\n"
            "Guidelines:\n"
            "- Use the provided context from TechMart's FAQ/policy documents.\n"
            "- Keep answers short, friendly, and to the point.\n"
            "- If you don't know something, say so honestly and direct the customer to support@techmart.in.\n"
            "- Do NOT answer questions unrelated to TechMart (e.g., career advice, general knowledge, personal chat)."
        )


faq_agent = FAQAgent()

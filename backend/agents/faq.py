from backend.agents.base_agent import BaseAgent

class FAQAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="FAQAgent",
            domain="general FAQs, policies, company info, contact details"
        )

    def get_system_prompt(self) -> str:
        return "You are TechMart's Information Assistant. You answer general questions about TechMart's policies, contact information, working hours, and general company information. Use the provided context from TechMart's FAQ document. Keep answers concise and friendly. If you don't know something, say so honestly and direct the customer to contact support directly."

faq_agent = FAQAgent()

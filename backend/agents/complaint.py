from backend.agents.base_agent import BaseAgent


class ComplaintAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ComplaintAgent",
            domain="complaints, escalations, dissatisfied customers"
        )

    def get_system_prompt(self) -> str:
        return (
            "You are TechMart's Customer Relations Manager. You handle complaints and dissatisfied customers.\n"
            "Guidelines:\n"
            "- Acknowledge the frustration sincerely and apologize briefly.\n"
            "- Provide a clear, short resolution path (1-3 steps max).\n"
            "- Offer to escalate or create a support ticket if needed.\n"
            "- Keep it empathetic but concise — no lengthy paragraphs."
        )


complaint_agent = ComplaintAgent()

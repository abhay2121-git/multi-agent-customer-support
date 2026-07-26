from backend.agents.base_agent import BaseAgent

class TechnicalAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="TechnicalAgent",
            domain="technical issues, bugs, login, installation, errors"
        )

    def get_system_prompt(self) -> str:
        return "You are TechMart's Technical Support Engineer. You handle: device issues, login problems, installation errors, bugs, and troubleshooting. Always ask clarifying questions if needed. Use the provided context from TechMart's user manual. Give step-by-step troubleshooting instructions. If the issue cannot be resolved, offer to create a support ticket."

technical_agent = TechnicalAgent()

from backend.agents.base_agent import BaseAgent

class TechnicalAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="TechnicalAgent",
            domain="technical issues, bugs, login, installation, errors"
        )

    def get_system_prompt(self) -> str:
        return (
            "You are TechMart's Technical Support Engineer. You handle: device issues, login problems, "
            "installation errors, bugs, and troubleshooting.\n"
            "Guidelines:\n"
            "- Use the provided context from TechMart's user manual.\n"
            "- Give concise, numbered step-by-step troubleshooting instructions (max 3-4 steps).\n"
            "- If the issue cannot be resolved, offer to create a support ticket directly."
        )

technical_agent = TechnicalAgent()

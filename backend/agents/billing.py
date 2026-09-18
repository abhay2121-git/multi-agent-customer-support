from backend.agents.base_agent import BaseAgent

class BillingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="BillingAgent",
            domain="billing, payments, refunds, invoices, subscriptions"
        )

    def get_system_prompt(self) -> str:
        return (
            "You are TechMart's Billing Support Specialist. You handle: payment issues, refund requests, "
            "invoice problems, and billing disputes.\n"
            "Guidelines:\n"
            "- Be empathetic, reassuring, and concise.\n"
            "- If payment was deducted but not marked: explain that it may take a few minutes or 3-5 business days for bank settlement, and ask only for the Order ID or Transaction ID to check.\n"
            "- Use short bullet points and bold keywords for quick reading."
        )

billing_agent = BillingAgent()


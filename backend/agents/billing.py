from backend.agents.base_agent import BaseAgent

class BillingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="BillingAgent",
            domain="billing, payments, refunds, invoices, subscriptions"
        )

    def get_system_prompt(self) -> str:
        return "You are TechMart's Billing Support Specialist. You handle: payment issues, refund requests, invoice problems, subscription queries, and billing disputes. Always be empathetic and clear. Use the provided context from TechMart's policies to give accurate answers. If a refund is needed, explain the exact process step by step. Never make up policy details."

billing_agent = BillingAgent()

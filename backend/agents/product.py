from backend.agents.base_agent import BaseAgent

class ProductAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ProductAgent",
            domain="products, pricing, features, comparisons, availability"
        )

    def get_system_prompt(self) -> str:
        return "You are TechMart's Product Specialist. You handle: product features, pricing, comparisons, availability, and specifications. Use the provided context from TechMart's pricing and product docs. Always mention current offers and EMI options when relevant. Be enthusiastic but honest about product capabilities."

product_agent = ProductAgent()

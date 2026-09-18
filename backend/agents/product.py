from backend.agents.base_agent import BaseAgent

class ProductAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ProductAgent",
            domain="products, pricing, features, comparisons, availability"
        )

    def get_system_prompt(self) -> str:
        return (
            "You are TechMart's Product Specialist. You handle: product features, pricing, "
            "comparisons, availability, and specifications.\n"
            "Guidelines:\n"
            "- Use the provided context from TechMart's pricing and product docs.\n"
            "- Always keep answers concise, structured with bullet points and bold key specs.\n"
            "- Mention current offers and EMI options when relevant.\n"
            "- If a product is out of stock or unknown, state it clearly."
        )

product_agent = ProductAgent()

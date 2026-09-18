import json
import logging
from backend.llm_client import groq_client

logger = logging.getLogger(__name__)

INTENTS = ["billing", "technical", "product", "complaint", "faq", "general"]

INTENT_EXAMPLES = {
    "billing": [
        "I was charged twice",
        "I need a refund",
        "My invoice is wrong"
    ],
    "technical": [
        "My laptop won't turn on",
        "The app keeps crashing",
        "I cannot login to my account"
    ],
    "product": [
        "What features does this have?",
        "How much does the laptop cost?",
        "Compare the pro and standard versions"
    ],
    "complaint": [
        "This is unacceptable",
        "I want to speak to a manager",
        "Terrible service"
    ],
    "faq": [
        "What are your working hours?",
        "Where is your office located?",
        "How can I contact support?"
    ],
    "general": [
        "Hello there",
        "Good morning",
        "Thanks for the help"
    ]
}

SYSTEM_PROMPT_TEMPLATE = """You are an intent classification system for TechMart Electronics customer support. Classify the customer message into one or more of these categories: {intents}. Return ONLY a JSON array of category names. Examples: {examples}"""

def detect_intent(message: str) -> list[str]:
    lower_msg = message.lower()
    
    # 1. Direct domain keyword matching
    keyword_intents = []
    billing_keywords = [
        "payment", "charged", "invoice", "refund", "deducted", "bill",
        "transaction", "debited", "pay", "paid", "upi", "card"
    ]
    if any(k in lower_msg for k in billing_keywords):
        keyword_intents.append("billing")

    tech_keywords = [
        "not working", "won't turn on", "crash", "screen", "flicker",
        "battery", "bluetooth", "wifi", "connect", "repair", "hardware",
        "software", "freeze", "bug", "damaged"
    ]
    if any(k in lower_msg for k in tech_keywords):
        keyword_intents.append("technical")

    complaint_keywords = [
        "unacceptable", "terrible", "worst", "manager", "horrible",
        "cheat", "scam", "fraud", "complaint", "escalate", "sue"
    ]
    if any(k in lower_msg for k in complaint_keywords):
        keyword_intents.append("complaint")

    product_keywords = [
        "specification", "features", "compare", "warranty period",
        "price of", "cost of", "in stock", "specs"
    ]
    if any(k in lower_msg for k in product_keywords):
        keyword_intents.append("product")

    # 2. LLM classification
    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        intents=json.dumps(INTENTS),
        examples=json.dumps(INTENT_EXAMPLES, indent=2)
    )
    prompt += f"\n\nCustomer message: {message}"
    
    try:
        response = groq_client.classify(prompt, INTENTS)
        import re
        match = re.search(r'\[.*?\]', response, re.DOTALL)
        if match:
            response = match.group(0)
        else:
            response = response.strip()
        
        detected_intents = json.loads(response)
        if not isinstance(detected_intents, list):
            detected_intents = [str(detected_intents)]
            
        llm_intents = [intent for intent in detected_intents if intent in INTENTS]
    except Exception as e:
        logger.warning("LLM intent parsing error: %s", e)
        llm_intents = []

    # Combine keyword and LLM intents preserving order
    combined = []
    for intent in keyword_intents + llm_intents:
        if intent in INTENTS and intent not in combined:
            combined.append(intent)

    if not combined:
        combined = ["faq"]

    logger.info("Detected intents for '%s': %s", message[:50], combined)
    return combined


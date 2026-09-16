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
    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        intents=json.dumps(INTENTS),
        examples=json.dumps(INTENT_EXAMPLES, indent=2)
    )
    prompt += f"\n\nCustomer message: {message}"
    
    response = groq_client.classify(prompt, INTENTS)
    
    try:
        import re
        match = re.search(r'\[.*?\]', response, re.DOTALL)
        if match:
            response = match.group(0)
        else:
            response = response.strip()
        
        detected_intents = json.loads(response)
        if not isinstance(detected_intents, list):
            detected_intents = [str(detected_intents)]
            
        valid_intents = [intent for intent in detected_intents if intent in INTENTS]
        if not valid_intents:
            valid_intents = ["faq"]
            
        logger.info(f"Detected intents: {valid_intents}")
        return valid_intents
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse intent JSON: {e}. Defaulting to ['faq']")
        return ["faq"]

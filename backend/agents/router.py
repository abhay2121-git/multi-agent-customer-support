import logging
from backend.agents.intent_detector import detect_intent
from backend.agents.billing import billing_agent
from backend.agents.technical import technical_agent
from backend.agents.product import product_agent
from backend.agents.complaint import complaint_agent
from backend.agents.faq import faq_agent
from backend.llm_client import groq_client

logger = logging.getLogger(__name__)

AGENT_MAP = {
    "billing": billing_agent,
    "technical": technical_agent,
    "product": product_agent,
    "complaint": complaint_agent,
    "faq": faq_agent,
    "general": faq_agent
}

def route_and_respond(message: str, conversation_history: list[dict], session_id: str) -> dict:
    intents = detect_intent(message)
    logger.info(f"Session {session_id} - Detected intents: {intents}")
    
    agents_to_call = []
    for intent in intents:
        if intent in AGENT_MAP and AGENT_MAP[intent] not in agents_to_call:
            agents_to_call.append(AGENT_MAP[intent])
            
    if not agents_to_call:
        agents_to_call = [faq_agent]
        
    responses = []
    sources = []
    agent_names = []
    
    for agent in agents_to_call:
        result = agent.respond(message, conversation_history)
        responses.append({
            "agent": agent.name,
            "response": result["response"]
        })
        agent_names.append(agent.name)
        for source in result["context_sources"]:
            if source not in sources:
                sources.append(source)
                
    if len(responses) == 1:
        final_response = responses[0]["response"]
    else:
        combining_prompt = (
            "You are TechMart Customer Support. Combine the expert inputs below into one concise, easy-to-read answer for the customer.\n"
            "Rules:\n"
            "- Keep the response brief, clear, and easy to interpret (under 120-150 words).\n"
            "- Use short bullet points or numbered steps with bold headers.\n"
            "- Do not repeat overlapping information.\n"
            "- If user details are needed, ask for only 1 or 2 essential items.\n\n"
            "Expert Inputs:\n"
        )
        for r in responses:
            agent_name = r["agent"].replace("Agent", " Expert")
            combining_prompt += f"{agent_name}: {r['response']}\n"

        final_response = groq_client.chat(
            system_prompt=combining_prompt,
            user_message=message,
            conversation_history=conversation_history,
            temperature=0.3,
            max_tokens=350,
        )

        
    logger.info(f"Session {session_id} - Routing decision: Used {agent_names}")
        
    return {
        "response": final_response,
        "intents_detected": intents,
        "agents_used": agent_names,
        "context_sources": sources
    }

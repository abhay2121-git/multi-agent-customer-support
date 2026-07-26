import sys
import os
from pathlib import Path

# Add the project root to sys.path so 'backend' can be resolved
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.agents.router import route_and_respond

def main():
    test_messages = [
        "What is your refund policy?",
        "My laptop won't turn on",
        "How much does the laptop cost?",
        "I was charged twice and the app keeps crashing",
        "This is unacceptable, I want to speak to a manager",
        "What are your working hours?"
    ]
    
    for i, msg in enumerate(test_messages):
        print(f"\n--- Test {i+1} ---")
        print(f"Input message: {msg}")
        
        result = route_and_respond(msg, [], f"test_session_{i}")
        
        print(f"Detected intents: {result['intents_detected']}")
        print(f"Agents used: {result['agents_used']}")
        print(f"Context sources used: {result['context_sources']}")
        print(f"Final response (first 200 chars): {result['response'][:200]}")

if __name__ == "__main__":
    main()

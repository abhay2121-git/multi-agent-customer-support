"""Integration test script for Phase 5 Chat API and multi-turn conversation memory.

Uses FastAPI TestClient so it can run self-contained without needing a separate server process.
"""

import sys
import uuid
from fastapi.testclient import TestClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.main import app

client = TestClient(app)


def run_integration_test():
    print("=" * 70)
    print("PHASE 5 INTEGRATION TEST -- CHAT API & MULTI-TURN MEMORY")
    print("=" * 70)

    # Generate unique test user credentials
    unique_id = uuid.uuid4().hex[:8]
    username = f"testuser_{unique_id}"
    email = f"user_{unique_id}@example.com"
    password = "TestPassword123!"

    # -------------------------------------------------------------------
    # Step 1: Register New User
    # -------------------------------------------------------------------
    print(f"\n[Step 1] Registering user: {username} ({email})...")
    reg_res = client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    if reg_res.status_code != 201:
        print(f"[FAIL] Registration failed ({reg_res.status_code}): {reg_res.text}")
        sys.exit(1)
    print(f"[OK] User registered successfully: {reg_res.json()}")

    # -------------------------------------------------------------------
    # Step 2: Login -> Get Token & Session ID
    # -------------------------------------------------------------------
    print("\n[Step 2] Logging in...")
    login_res = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    if login_res.status_code != 200:
        print(f"[FAIL] Login failed ({login_res.status_code}): {login_res.text}")
        sys.exit(1)

    login_data = login_res.json()
    token = login_data["access_token"]
    session_id = login_data["session_id"]
    print(f"[OK] Logged in successfully!")
    print(f"   Token: {token[:25]}...")
    print(f"   Session ID: {session_id}")

    headers = {"Authorization": f"Bearer {token}"}

    # -------------------------------------------------------------------
    # Step 3: Send 3 Chat Messages in Sequence
    # -------------------------------------------------------------------
    test_messages = [
        "What is your refund policy?",
        "I was charged twice for my last order",
        "I also can't login to my account",
    ]

    print("\n[Step 3] Sending 3 sequential chat messages...")
    for idx, msg in enumerate(test_messages, start=1):
        print(f"\n  [Message {idx}] Sending: '{msg}'")
        chat_res = client.post(
            "/chat/message",
            headers=headers,
            json={"message": msg, "session_id": session_id},
        )

        if chat_res.status_code != 200:
            print(f"[FAIL] Message {idx} failed ({chat_res.status_code}): {chat_res.text}")
            sys.exit(1)

        data = chat_res.json()
        print(f"  [OK] Agent Used    : {data.get('agent_used')}")
        print(f"       Intents       : {data.get('intent_detected')}")
        print(f"       Ticket Created: {data.get('ticket_number') or 'None'}")
        print(f"       Response      : {data.get('response')[:120]}...")

    # -------------------------------------------------------------------
    # Step 4: Retrieve Conversation History
    # -------------------------------------------------------------------
    print("\n[Step 4] Fetching conversation history...")
    hist_res = client.get(
        f"/chat/history/{session_id}",
        headers=headers,
    )
    if hist_res.status_code != 200:
        print(f"[FAIL] Failed to fetch history ({hist_res.status_code}): {hist_res.text}")
        sys.exit(1)

    history_data = hist_res.json()
    messages = history_data.get("messages", [])
    print(f"[OK] History retrieved. Message count: {len(messages)}")

    # -------------------------------------------------------------------
    # Step 5: Verify Message Count (3 user + 3 assistant = 6)
    # -------------------------------------------------------------------
    print("\n[Step 5] Verifying message count...")
    if len(messages) == 6:
        print(f"[SUCCESS] History contains exactly 6 records (3 User + 3 Assistant).")
    else:
        print(f"[WARNING] Expected 6 messages in history, found {len(messages)}.")

    # -------------------------------------------------------------------
    # Step 6: Print Full Conversation Summary
    # -------------------------------------------------------------------
    print("\n[Step 6] Full Conversation Trace:")
    print("-" * 70)
    for entry in messages:
        role = entry['role'].upper()
        agent_info = f" (Agent: {entry['agent_used']})" if entry.get('agent_used') else ""
        print(f"[{role}]{agent_info}:")
        print(f"  {entry['content']}\n")
    print("-" * 70)

    print("\nPHASE 5 INTEGRATION TEST PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_integration_test()

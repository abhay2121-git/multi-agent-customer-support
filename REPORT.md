# Project Report: TechMart Multi-Agent AI Customer Support Assistant

## 1. Executive Summary
The TechMart Customer Support AI is a highly scalable, multi-agent AI system designed to handle tier-1 customer inquiries autonomously. By combining Retrieval-Augmented Generation (RAG) with specialized Language Model (LLM) agents, the system can triage, diagnose, and resolve customer issues ranging from billing disputes to technical troubleshooting, while seamlessly escalating unresolved issues to human agents via an automated ticketing system.

## 2. Technical Architecture
The application is built on a modern, decoupled architecture:
- **Frontend**: A lightweight, responsive web interface built with HTML5, Vanilla JavaScript, and Bootstrap 5. It manages secure session state via JWT tokens and local storage.
- **Backend API**: A high-performance FastAPI Python application that serves as the orchestration layer. It handles authentication, validates user sessions, and manages database interactions.
- **Database Layer**: PostgreSQL handles persistent storage for Users, Conversations, Sessions, and Support Tickets. 
- **AI Engine (Multi-Agent System)**: Powered by Groq's low-latency Llama 3 inference engine. The orchestration logic analyzes user intent and routes the query to one or more of five specialized agents: Billing, Technical, Product, FAQ, and Complaint.
- **Vector Search (RAG)**: Uses FAISS and HuggingFace's `all-MiniLM-L6-v2` embeddings to perform semantic search across company PDF manuals.

## 3. Key Achievements & Features
- **Dynamic Intent Routing**: The system avoids monolithic LLM prompts by classifying intent first, then invoking specialized, domain-specific agents, ensuring higher accuracy and lower hallucination rates.
- **Contextual Memory**: By storing rolling chat histories in PostgreSQL, the AI maintains deep conversational context across multi-turn interactions.
- **Silent Escalation Workflow**: Angry or frustrated customers trigger the `ComplaintAgent`, which automatically generates a high-priority support ticket in the database without disrupting the user flow.
- **Cloud-Native Deployment**: The backend is container-ready and deployed on Render, while the frontend is statically hosted via GitHub Pages, demonstrating a cost-effective, scalable cloud deployment strategy.

## 4. Challenges & Solutions
- *Challenge*: Coordinating multiple agents to provide a single, cohesive response when a user asks a complex, multi-domain question (e.g., "Why did my router break, and how do I get a refund?").
- *Solution*: Implemented a map-reduce style agent router. The router calls the Technical and Billing agents independently, then uses a final LLM call to synthesize their answers into one unified response.

## 5. Future Enhancements
- **WebSockets integration** for real-time streaming of LLM tokens to the UI.
- **Admin Dashboard** for human agents to view, claim, and resolve the automatically generated support tickets.
- **Analytics Pipeline** to measure agent resolution rates and identify gaps in the RAG knowledge base.

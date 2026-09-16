# Multi-Agent AI Customer Support Assistant

## 🎯 Project Overview
This project is an intelligent, multi-agent AI customer support platform designed for TechMart. It utilizes specialized autonomous agents (Billing, Technical, Product, Complaint, FAQ) routed dynamically based on intent detection to deliver accurate, context-aware responses to user queries.

## 🏗️ System Architecture
```text
┌───────────────┐           ┌───────────────────┐           ┌──────────────┐
│               │           │                   │           │              │
│  User (Web)   │ ◄───────► │ FastAPI Backend   │ ◄───────► │ PostgreSQL   │
│               │   Auth &  │                   │   Store   │ (Users,      │
└───────────────┘   Chat    └─────────┬─────────┘           │  Tickets,    │
                                      │                     │  Sessions)   │
                                      ▼                     └──────────────┘
                            ┌───────────────────┐
                            │   Intent Router   │
                            └────┬─────────┬────┘
                                 │         │
                   ┌─────────────▼─┐     ┌─▼─────────────┐
                   │  Specialized  │     │  Specialized  │
                   │  Agents (x5)  │     │  Agents (x5)  │
                   └─────┬─────────┘     └─────────┬─────┘
                         │                         │
                         ▼                         ▼
                  ┌──────────────┐          ┌──────────────┐
                  │    FAISS     │          │  Groq (LLM)  │
                  │ Vector Store │          │   Llama 3    │
                  └──────────────┘          └──────────────┘
```

## ✨ Features
- [x] Multi-agent routing (Intent-based dynamically selected agents)
- [x] RAG with company knowledge base (FAISS + Sentence Transformers)
- [x] JWT authentication (Secure login/registration)
- [x] Conversation memory (Chronological DB retrieval per session)
- [x] Auto ticket creation (Silent escalation for complaints)
- [x] 5 specialized agents (Billing, Tech, Product, Complaint, FAQ)

## 🛠️ Tech Stack
| Component       | Technology Used                                 |
|-----------------|-------------------------------------------------|
| **Frontend**    | HTML5, Bootstrap 5 (CDN), Vanilla JS            |
| **Backend**     | Python 3.11, FastAPI, Uvicorn, Pydantic         |
| **AI / NLP**    | Groq (Llama 3), Sentence-Transformers, LangChain|
| **Database**    | PostgreSQL, SQLAlchemy, FAISS (Vector DB)       |
| **Deployment**  | Render (Backend), GitHub Pages (Frontend)       |

## 📁 Project Structure
```text
customer-support-ai/
├── backend/
│   ├── agents/          # Multi-agent definitions & intent router
│   ├── api/             # FastAPI route handlers (auth, chat)
│   ├── database/        # SQLAlchemy models and connection
│   ├── rag/             # Document loader, chunker, FAISS embedder
│   ├── config.py        # Environment & Pydantic settings
│   ├── main.py          # FastAPI application entry point
│   ├── memory.py        # Conversation memory and ticket logic
│   ├── schemas.py       # Pydantic validation schemas
│   └── auth_utils.py    # JWT and password hashing utilities
├── frontend/
│   ├── css/             # Shared styling
│   ├── js/              # Client-side logic (chat.js, auth.js)
│   ├── login.html       # Authentication portal
│   ├── register.html    # Account creation
│   └── chat.html        # Main support chat interface
├── knowledge_base/      # Source PDFs for RAG ingestion
├── vectorstore/         # Generated FAISS index files
├── .env                 # Environment variables
├── requirements.txt     # Python dependencies
├── Procfile             # Render deployment config
└── runtime.txt          # Python version target
```

## 🚀 Quick Start (Local Setup)

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Groq API Key (free at [console.groq.com](https://console.groq.com))

### Installation
1. **Clone repo**: `git clone https://github.com/yourusername/customer-support-ai.git`
2. **Create virtual environment**: `python -m venv .venv` and activate it.
3. **Install requirements**: `pip install -r requirements.txt`
4. **Create .env file**: Copy the template below and configure your variables.
5. **Create PostgreSQL database**: Ensure your local Postgres server is running and create a DB named `techmart_dev`.
6. **Build Vector Index**: `python -m backend.rag.build_index`
7. **Run Server**: `uvicorn backend.main:app --reload`
8. **Run Frontend**: `cd frontend && python -m http.server 8080`

### Environment Variables
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (e.g. `postgresql://user:pass@localhost:5432/db`) |
| `SECRET_KEY` | JWT signing secret |
| `GROQ_API_KEY` | API key for LLM access |
| `GROQ_MODEL` | Default LLM model (e.g. `llama-3.1-8b-instant`) |
| `EMBEDDING_MODEL` | HuggingFace model for FAISS (e.g. `sentence-transformers/all-MiniLM-L6-v2`) |
| `ALLOWED_ORIGINS` | Comma-separated or JSON list of allowed CORS domains |

## 📡 API Endpoints
| Method | Path | Auth Required | Description |
|--------|------|---------------|-------------|
| POST   | `/auth/register` | No | Create a new user account |
| POST   | `/auth/login`    | No | Authenticate and receive JWT |
| POST   | `/chat/message`  | Yes | Send message to AI agents |
| GET    | `/chat/history/{id}`| Yes | Fetch session message history |
| POST   | `/chat/new-session` | Yes | Generate a new chat session UUID |
| GET    | `/chat/sessions` | Yes | Get all sessions for current user |
| GET    | `/chat/tickets`  | Yes | Retrieve support tickets |

## 🤖 Agent Details
| Agent Name | Domain | Knowledge Source |
|------------|--------|------------------|
| **BillingAgent** | Refunds, payments, invoices | `billing_policies.pdf`, `refunds.pdf` |
| **TechnicalAgent** | Troubleshooting, bugs, tech specs | `technical_manual.pdf` |
| **ProductAgent** | Inventory, product details, specs | `product_catalog.pdf` |
| **ComplaintAgent** | Escalations, angry customers | N/A (Auto-triggers Tickets) |
| **FAQAgent** | General inquiries, store hours | `faq_general.pdf` |

## 📊 Evaluation Criteria Coverage
| Rubric Item | Implementation Details |
|-------------|------------------------|
| Multi-Agent Routing | Built custom Intent Detector that dynamically spawns 1 or more agents based on NLP routing logic in `router.py`. |
| RAG Integration | `backend/rag/` module parses PDFs, chunks text, and stores semantic vectors in FAISS for retrieval by domain agents. |
| Memory Management | Database-backed conversation history. `memory.py` pulls the last N messages to inject context into the Groq prompt. |
| Ticket Escalation | Silent ticket creation triggered when `ComplaintAgent` is activated, securely stored in PostgreSQL. |
| Production Ready | Configured for Render backend deployment with `Procfile`, graceful env fallbacks, and strict CORS handling. |

## 🌐 Deployment
- **Frontend Live Demo**: [https://yourusername.github.io/customer-support-ai/](https://yourusername.github.io/customer-support-ai/)
- **Backend API URL**: [https://techmart-support-ai.onrender.com](https://techmart-support-ai.onrender.com)

## 🌐 Multilingual Support
- Supports English, Hindi (Devanagari), and Hinglish
- Dynamic language adaptation mid-conversation
- Users can switch language style without restarting session
- Handles code-switched queries naturally 
  (e.g. "mera payment ho gaya but status update nahi hua")
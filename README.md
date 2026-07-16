<div align="center">
  <img src="https://img.shields.io/badge/Status-Production_Ready-brightgreen?style=for-the-badge" alt="Status" />
  <img src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Gemini_3.5-4285F4?style=for-the-badge&logo=google" alt="Gemini" />
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql" alt="PostgreSQL" />
</div>

<h1 align="center">CalAi AI 🥗</h1>

<p align="center">
  <b>The next-generation, agentic AI clinical sports nutritionist.</b> <br>
  CalAi AI autonomously estimates meal volume from photos, cross-references clinical density databases via pgvector, scrapes live nutritional data via Firecrawl, and synthesizes personalized macronutrient advice based on your health goals.
</p>

---

## 🌟 Key Features

*   **📸 Visual Volume Estimation:** Upload a picture of your food. CalAi's Vision-Language Model visually assesses the plate, identifying the food and estimating serving volume without needing depth sensors.
*   **🤖 Agentic RAG Pipeline:** Our LLM isn't just a chatbot—it's an autonomous agent. Using Google Gemini 3.5's Native Function Calling, the agent actively orchestrates between internal `pgvector` similarity searches and live `Firecrawl` web scraping to accurately calculate macros.
*   **🔒 Multi-Tenant Security:** Built for scale. Features a custom JWT/Cookie-based authentication system with strict Row-Level Security (RLS). Every logged meal, chat message, and health goal is mathematically isolated to your unique `user_id`.
*   **💬 Autonomous Chatbot:** Chat with an AI Nutritionist that actually remembers you. The agent has tools to query your PostgreSQL health profile and fetch today's logged meals *before* giving you advice.
*   **🚀 Zero-Downtime CI/CD:** Fully containerized into dual Docker microservices and deployed seamlessly on Render PaaS via Infrastructure-as-Code (`render.yaml`).

---

## 🏗️ Architecture & Flow

CalAi operates on a **4-Node LangGraph Architecture** to process food scans. 

```mermaid
graph TD
    A[User Uploads Food Image] -->|FastAPI| B(Node 1: NLP & Vision Parser)
    
    subgraph "Agentic RAG Pipeline"
        B -->|Food Name + Volume| C{Node 2: Agentic Orchestrator}
        C <-->|Query Internal PDF| D[(PostgreSQL pgvector DB)]
        C <-->|Live Web Scrape| E((Firecrawl API))
    end
    
    C -->|Retrieved Density/Macros| F(Node 3: Math Engine)
    F -->|Weight = Vol × Density| G{Node 4: Agentic Recommender}
    
    subgraph "Personalized AI"
        G <-->|Fetch Live Context| H((Google Search))
    end
    
    G -->|Final Nutrition + Advice| I[(Saved to User's Profile)]
    I --> J[Dashboard Rendered]
```

### 🧠 How the Agentic Chatbot Works

Traditional chatbots are passive. CalAi's chatbot is an active agent powered by a dynamic `while` loop using Native Function Calling.

```mermaid
sequenceDiagram
    participant User
    participant Chatbot (Gemini)
    participant Database (Tools)
    
    User->>Chatbot: "Did I eat enough protein today?"
    Note over Chatbot: Thoughts: "I don't know their goals or what they ate."
    Chatbot->>Database: Call get_user_profile_tool()
    Database-->>Chatbot: Returns: Goal is 160g Protein
    Chatbot->>Database: Call get_recent_meals_tool()
    Database-->>Chatbot: Returns: Chicken (40g P), Eggs (12g P)
    Note over Chatbot: Thoughts: "Total is 52g. They need 108g more."
    Chatbot->>User: "You've only eaten 52g. I recommend a protein shake..."
```

---

## 🛠️ Tech Stack

### Backend
*   **FastAPI:** High-performance async Python framework routing all traffic.
*   **Flask:** Lightweight microservice handling legacy Python 3.6+ CV/Volume estimation models independently.
*   **PostgreSQL (Supabase):** Primary datastore utilizing `pgvector` for similarity search and strict Row Level Security (RLS) for multi-tenant data isolation.

### Frontend
*   **Vanilla HTML/JS:** Blazing fast DOM manipulation without the overhead of heavy SPA frameworks.
*   **Tailwind CSS:** Premium, glassmorphic UI design system.

### AI / Data
*   **Google Gemini 3.5 Flash:** Core LLM driving both the LangGraph pipeline and the Agentic Chatbot.
*   **Firecrawl:** Scrapes live web documentation to fetch exact nutritional profiles when our internal database is missing exotic foods.
*   **LangGraph:** Manages the stateful flow between Node 1 (Vision), Node 2 (RAG), Node 3 (Math), and Node 4 (Recommender).

---

## 🚀 Deployment (Render PaaS)

This application is deployed using a `render.yaml` Blueprint. 

1. **GitHub Watcher:** Render monitors the `main` branch.
2. **Containerization:** On push, Render builds the `Dockerfile` in the cloud.
3. **Dynamic Port Binding:** The FastApi instance dynamically binds to Render's injected `$PORT`.
4. **Environment Variables:** Secrets (`ADMIN_PASSWORD`, `DATABASE_URL`, `GOOGLE_API_KEY`) are securely injected via the Render dashboard, keeping them out of version control.

---

## 👨‍💻 Local Development Setup

If you wish to run CalAi AI locally:

### 1. Clone & Install
```bash
git clone https://github.com/kavyajshah240706/CalAi.git
cd CalAi
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```env
# AI Keys
GOOGLE_API_KEY=your_gemini_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key

# Database
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# Security
ADMIN_PASSWORD=your_secure_login_password
```

### 3. Initialize Database
Run the setup script to create the necessary tables and enable Row-Level Security:
```bash
python src/backend/setup_db.py
```

### 4. Run the Servers
Start the Volume Estimator (Terminal 1):
```bash
python flask_server.py
```
Start the FastAPI Backend (Terminal 2):
```bash
uvicorn src.backend.main:app --reload --port 8000
```
Visit `http://localhost:8000` in your browser and log in with your `ADMIN_PASSWORD`.

---
<div align="center">
  <i>Architected with ❤️ for precision nutrition tracking.</i>
</div>

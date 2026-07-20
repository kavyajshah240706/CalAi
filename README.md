<div align="center">
  <img src="https://img.shields.io/badge/Status-Production_Ready-brightgreen?style=for-the-badge" alt="Status" />
  <img src="https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Google_Vertex_AI-4285F4?style=for-the-badge&logo=google" alt="Vertex AI" />
  <img src="https://img.shields.io/badge/Google_Cloud_Run-4285F4?style=for-the-badge&logo=googlecloud" alt="Cloud Run" />
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql" alt="PostgreSQL" />
</div>

<h1 align="center">CalAi 🥗</h1>

<p align="center">
  <b>The next-generation, agentic AI clinical sports nutritionist.</b> <br>
  CalAi autonomously estimates meal volume from photos using computer vision, identifies food via Google Vertex AI (Gemini 1.5 Flash), calculates precise macronutrients, and synthesizes personalized dietary advice based on your health goals.
</p>

<div align="center">
  <h3>🟢 <b>Live Demo:</b> <a href="https://calai-backend-1041961183692.asia-south1.run.app" target="_blank">Try CalAi Here!</a></h3>
</div>

---

## 🌟 Key Features

*   **📸 Geometric Volume Estimation:** Upload a picture of your food. CalAi delegates the image to an independent Microservice (TensorFlow + OpenCV) to geometrically calculate the exact serving volume in milliliters using depth estimation and segmentation.
*   **🤖 4-Node Agentic Pipeline:** Our AI isn't just a basic prompt—it's an autonomous workflow. CalAi uses a 4-node pipeline (Vision -> Data Retrieval -> Math Engine -> Clinical Recommender) powered by Gemini 1.5 Flash on Vertex AI to guarantee accurate macronutrient math.
*   **🔒 Secure Google OAuth 2.0:** Secure, seamless login using Google OAuth. JWT tokens are verified server-side and issued as strict `HttpOnly` session cookies to prevent XSS attacks. 
*   **💬 Autonomous Chatbot:** Chat with an AI Nutritionist that actually remembers you. The agent executes native function calls to query your PostgreSQL health profile and fetch today's logged meals *before* giving you advice.
*   **🚀 Scalable Cloud Run Microservices:** Fully containerized into dual Docker microservices. The heavy Machine Learning models (TF 1.13 / Python 3.6) are perfectly isolated from the lightning-fast FastAPI backend (Python 3.10) to ensure zero dependency clashes and infinite scalability.

---

## 🏗️ Architecture & Flow

CalAi operates on a **4-Node LangGraph-style Architecture** to process food scans. 

```mermaid
graph TD
    A[User Uploads Food Image] -->|FastAPI| V(Volume Estimator Microservice)
    V -->|Calculated Volume (ml)| B(Node 1: NLP & Vision Parser)
    
    subgraph "Agentic Pipeline"
        B -->|Food Name + Volume| C{Node 2: Agentic Orchestrator}
        C <-->|Retrieve Nutritional Baselines| D[(PostgreSQL DB)]
    end
    
    C -->|Retrieved Density/Macros| F(Node 3: Math Engine)
    F -->|Weight = Vol × Density| G{Node 4: Agentic Recommender}
    
    subgraph "Personalized AI"
        G <-->|Compare against Daily Goals| H[(User Profile)]
    end
    
    G -->|Final Nutrition + Clinical Advice| I[(Saved to Meal Logs)]
    I --> J[Dashboard Rendered]
```

### 🧠 How the Agentic Chatbot Works

Traditional chatbots are passive. CalAi's chatbot is an active agent powered by Native Function Calling.

```mermaid
sequenceDiagram
    participant User
    participant Chatbot (Vertex AI)
    participant Database (Tools)
    
    User->>Chatbot: "Did I eat enough protein today?"
    Note over Chatbot: Thoughts: "I need to check their goals and logged meals."
    Chatbot->>Database: Call get_user_profile_tool()
    Database-->>Chatbot: Returns: Goal is 160g Protein
    Chatbot->>Database: Call get_recent_meals_tool()
    Database-->>Chatbot: Returns: Chicken (40g P), Eggs (12g P)
    Note over Chatbot: Thoughts: "Total is 52g. They need 108g more."
    Chatbot->>User: "You've only eaten 52g today. I recommend 200g of chicken breast for dinner..."
```

---

## 🛠️ Tech Stack

### Backend
*   **FastAPI:** High-performance async Python 3.10 framework routing all traffic.
*   **Volume Estimator Microservice:** Isolated Python 3.6 Flask container running legacy TensorFlow 1.13 Mask R-CNN models for depth estimation.
*   **PostgreSQL:** Primary relational datastore for user health profiles and historical meal logging.

### Frontend
*   **Vanilla HTML/JS:** Blazing fast DOM manipulation without the overhead of heavy SPA frameworks. Served statically via FastAPI.
*   **Tailwind CSS:** Premium, glassmorphic UI design system.

### AI / Cloud
*   **Google Vertex AI (Gemini 1.5 Flash):** Enterprise-grade core LLM driving both the multi-node pipeline and the Agentic Chatbot, utilizing GCP credits.
*   **Google Cloud Run:** Serverless, scale-to-zero container orchestration hosting both microservices.
*   **Google Cloud Build:** CI/CD pipelines defined in `cloudbuild.yaml` and `cloudbuild-volume.yaml`.

---

## 👨‍💻 Local Development Setup

If you wish to run CalAi locally:

### 1. Clone & Install
```bash
git clone https://github.com/kavyajshah240706/CalAi.git
cd CalAi
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```env
# Google Cloud Vertex AI
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/calai_db

# Microservice
VOLUME_ESTIMATOR_URL=http://localhost:5000
```

### 3. Run the Microservices via Docker Compose
To easily spin up the PostgreSQL database, the FastAPI backend, and the Volume Estimator locally, use Docker Compose:
```bash
docker-compose up --build
```
Visit `http://localhost:8000` in your browser.

---
<div align="center">
  <i>Architected with ❤️ for precision nutrition tracking.</i>
</div>

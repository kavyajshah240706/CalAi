<div align="center">

  <h1>🥗 CalAi</h1>
  <h3>The Autonomous AI Clinical Sports Nutritionist</h3>

  <p>
    <img src="https://img.shields.io/badge/Live-Production-brightgreen?style=for-the-badge" alt="Live" />
    <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Vertex_AI-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white" alt="Vertex AI" />
    <img src="https://img.shields.io/badge/Cloud_Run-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white" alt="Cloud Run" />
    <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
    <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
    <img src="https://img.shields.io/badge/LangGraph-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" alt="LangGraph" />
    <img src="https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white" alt="TensorFlow" />
    <img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV" />
  </p>

  <p>
    CalAi autonomously estimates meal volume from photos using computer vision,<br>
    identifies food via Google Vertex AI, calculates precise macronutrients,<br>
    and synthesizes personalized dietary advice based on your health goals.
  </p>

  <h3>
    🟢 Live at: <a href="https://calai-backend-1041961183692.asia-south1.run.app">https://calai-backend-1041961183692.asia-south1.run.app</a>
  </h3>

</div>

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [The Agentic AI Pipeline](#-the-agentic-ai-pipeline)
- [The Autonomous Chatbot](#-the-autonomous-chatbot)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Deployment Infrastructure](#-deployment-infrastructure)
- [Local Development Setup](#-local-development-setup)
- [License](#-license)

---

## 🌟 Key Features

| Feature | Description |
|---------|-------------|
| **📸 Geometric Volume Estimation** | Uploads are routed to an isolated CV microservice running TensorFlow Mask R-CNN and monocular depth estimation to calculate exact food volume in mL. |
| **🤖 4-Node Agentic Pipeline** | A LangGraph `StateGraph` pipeline — Vision → Data Retrieval → Math Engine → Clinical Recommender — ensures accurate, hallucination-resistant macronutrient calculations. |
| **🔐 Google OAuth 2.0** | Secure sign-in via Google. JWTs are verified server-side and issued as strict `HttpOnly` + `Secure` session cookies — tokens never touch LocalStorage. |
| **💬 Autonomous Chatbot** | An AI nutritionist powered by Vertex AI Native Function Calling. It actively queries your database for your goals and today's meals before answering. |
| **🚀 Dual Microservices** | Two independent Docker containers on Cloud Run: a modern Python 3.11 FastAPI backend and a legacy Python 3.6 TensorFlow CV service, fully isolated. |
| **📊 Smart Dashboard** | Real-time macro tracking with animated progress rings, daily caloric summaries, and AI-generated health insights. |

---

## 🏗️ System Architecture

CalAi is built on a decoupled **Microservices Architecture** deployed entirely on Google Cloud Platform.

```mermaid
flowchart TD
    subgraph CLIENT["🖥️ Client Browser"]
        UI["Vanilla HTML/JS + TailwindCSS"]
    end

    subgraph GCP["☁️ Google Cloud Platform"]
        subgraph CR1["Cloud Run Service A"]
            API["FastAPI Backend\nPython 3.11 · Port 8080"]
        end

        subgraph CR2["Cloud Run Service B"]
            VOL["Volume Estimator\nFlask · Python 3.6 · Port 5000\nTensorFlow 1.13 + OpenCV"]
        end

        DB[("PostgreSQL\nCloud SQL")]
        VERTEX["Google Vertex AI\nGemini 1.5 Flash"]
    end

    UI -- "HTTPS REST API" --> API
    API -- "Image payload" --> VOL
    VOL -- "Volume in mL" --> API
    API -- "SQL queries" --> DB
    API -- "LLM prompts" --> VERTEX

    style CLIENT fill:#1e293b,stroke:#38bdf8,color:#f8fafc
    style GCP fill:#0f172a,stroke:#22d3ee,color:#f8fafc
    style CR1 fill:#1e3a5f,stroke:#3b82f6,color:#f8fafc
    style CR2 fill:#3b1f2b,stroke:#f43f5e,color:#f8fafc
    style API fill:#0d9488,stroke:#14b8a6,color:#fff
    style VOL fill:#b91c1c,stroke:#ef4444,color:#fff
    style DB fill:#1d4ed8,stroke:#60a5fa,color:#fff
    style VERTEX fill:#7c3aed,stroke:#a78bfa,color:#fff
```

---

## 🧠 The Agentic AI Pipeline

When a user uploads a food photo, it doesn't just go to a chatbot. It enters a **4-Node LangGraph `StateGraph`** — a deterministic, sequential pipeline that breaks the problem into specialized stages to eliminate LLM hallucinations.

```mermaid
flowchart LR
    START(("📸 Image\nUploaded")) --> N1

    subgraph PIPELINE["LangGraph StateGraph Pipeline"]
        N1["🔍 Node 1\nNLP + Vision Parser\n\nIdentifies food items\nfrom the image"] --> N2

        N2["📊 Node 2\nData Retrieval\n\nFetches nutritional\nbaselines per 100g"] --> N3

        N3["🧮 Node 3\nMath Engine\n\nCalculates exact macros\nfrom geometric volume"] --> N4

        N4["💡 Node 4\nClinical Recommender\n\nCross-references\nuser health goals"]
    end

    N4 --> RESULT(("✅ Logged\nto Dashboard"))

    style START fill:#f59e0b,stroke:#d97706,color:#000
    style RESULT fill:#10b981,stroke:#059669,color:#000
    style N1 fill:#3b82f6,stroke:#2563eb,color:#fff
    style N2 fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style N3 fill:#ef4444,stroke:#dc2626,color:#fff
    style N4 fill:#10b981,stroke:#059669,color:#fff
    style PIPELINE fill:#1e293b,stroke:#475569,color:#f8fafc
```

**How each node works:**

| Node | File | Role |
|------|------|------|
| **Node 1** | `node1_nlp.py` | Sends the image to Vertex AI Gemini with a structured prompt. Returns the food name, estimated serving description, and parsed quantities. |
| **Node 2** | `node2_data.py` | Retrieves standard nutritional baselines — calories, protein, carbs, fat per 100g — from the database or via live data retrieval. |
| **Node 3** | `node3_math.py` | Constrains the LLM to perform strict arithmetic: `macros = baseline_per_100g × (volume_ml × density / 100)`. No guessing allowed. |
| **Node 4** | `node4_recommender.py` | Loads the user's health profile from PostgreSQL and generates a personalized clinical recommendation comparing the meal against their daily targets. |

The pipeline state flows through a Pydantic `GraphState` schema:

```python
class GraphState(BaseModel):
    user_input: str
    image_base64: Optional[str] = None
    parsed_query: Optional[Dict] = None       # Output of Node 1
    profile: Optional[Dict] = None            # Output of Node 2
    calculated_nutrition: Optional[Dict] = None  # Output of Node 3
    recommendations: Optional[str] = None      # Output of Node 4
```

---

## 💬 The Autonomous Chatbot

The chatbot isn't a passive Q&A — it's an **autonomous agent** powered by Vertex AI Native Function Calling. When it lacks context, it actively calls tools to fetch data before responding.

```mermaid
sequenceDiagram
    actor User
    participant Chatbot as Vertex AI Agent
    participant DB as PostgreSQL

    User->>Chatbot: Did I eat enough protein today?

    Note over Chatbot: I need to check their goals<br>and what they ate today.

    Chatbot->>DB: get_user_profile()
    DB-->>Chatbot: Goal = 160g protein/day

    Chatbot->>DB: get_todays_meals()
    DB-->>Chatbot: Chicken 40g P, Eggs 12g P

    Note over Chatbot: Total = 52g. Deficit = 108g.<br>Recommend high-protein dinner.

    Chatbot->>User: You have consumed 52g of your 160g<br>protein goal. I recommend 200g of<br>chicken breast for dinner to close the gap.
```

---

## 📂 Project Structure

```
CalAi/
├── 📄 Dockerfile                  # Main backend container (Python 3.11)
├── 📄 Dockerfile.volume           # Volume estimator container (Python 3.6)
├── 📄 cloudbuild.yaml             # CI/CD pipeline for the backend
├── 📄 cloudbuild-volume.yaml      # CI/CD pipeline for the volume estimator
├── 📄 docker-compose.yml          # Local dev orchestration
├── 📄 requirements.txt            # Backend Python dependencies
├── 📄 config.py                   # App configuration
│
├── 📁 src/
│   ├── 📁 backend/
│   │   ├── 📄 main.py             # FastAPI app — all routes, auth, sessions
│   │   ├── 📄 setup_db.py         # PostgreSQL schema initialization
│   │   ├── 📁 agents/
│   │   │   ├── 📄 schema.py               # Pydantic GraphState model
│   │   │   ├── 📄 langgraph_pipeline.py    # StateGraph builder + runner
│   │   │   ├── 📄 node1_nlp.py            # Vision + NLP food identification
│   │   │   ├── 📄 node2_data.py           # Nutritional data retrieval
│   │   │   ├── 📄 node3_math.py           # Macro calculation engine
│   │   │   └── 📄 node4_recommender.py    # Personalized clinical advice
│   │   └── 📁 database/                   # DB connection utilities
│   │
│   ├── 📁 frontend/
│   │   ├── 📁 login/                      # Google OAuth + demo mode
│   │   ├── 📁 nutriflow_dashboard/        # Main dashboard with macro rings
│   │   ├── 📁 ai_nutrition_scanner/       # Food photo upload + AI analysis
│   │   ├── 📁 nutriflow_chat/             # Autonomous AI chatbot
│   │   ├── 📁 meal_history_logs/          # Historical meal log viewer
│   │   ├── 📁 profile_health_goals/       # User profile + health targets
│   │   └── 📁 vitality_core/              # Settings + additional features
│   │
│   └── 📁 volume_estimator/
│       ├── 📄 app.py                      # Flask API wrapper
│       ├── 📄 volume_estimator.py         # Core CV + depth estimation logic
│       ├── 📄 point_cloud_utils.py        # 3D point cloud volume computation
│       ├── 📁 depth_estimation/           # Monocular depth model
│       ├── 📁 food_segmentation/          # Mask R-CNN food segmentation
│       └── 📁 ellipse_detection/          # Plate ellipse fitting
│
├── 📁 models/                             # Pre-trained ML weights (~450MB)
│   ├── monovideo_fine_tune_food_videos.h5
│   ├── monovideo_fine_tune_food_videos.json
│   └── mask_rcnn_food_segmentation.h5
│
├── 📁 datasets/                           # Nutritional reference data
└── 📁 assets/                             # Static assets
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance async Python 3.11 web framework. Serves the frontend, handles API routes, and manages session authentication. |
| **LangGraph** | Orchestrates the 4-node `StateGraph` pipeline with deterministic edges and Pydantic-validated state transitions. |
| **PostgreSQL** | Primary relational datastore for user profiles, health goals, and historical meal logs. |
| **psycopg2** | PostgreSQL database driver for executing parameterized SQL queries. |

### Volume Estimator Microservice
| Technology | Purpose |
|------------|---------|
| **Flask** | Lightweight Python 3.6 web server exposing the CV pipeline as a REST API. |
| **TensorFlow 1.13** | Runs the monocular depth estimation model to infer pixel-level depth maps from a single 2D image. |
| **OpenCV** | Image preprocessing, contour detection, and food region masking. |
| **Mask R-CNN** | Instance segmentation model trained on food datasets to isolate individual food items from the plate. |
| **scikit-image** | Advanced image processing for ellipse detection and plate boundary fitting. |

### Frontend
| Technology | Purpose |
|------------|---------|
| **Vanilla HTML/JS** | Zero-framework frontend for maximum speed. DOM manipulation via native JS `fetch()` API calls. |
| **Tailwind CSS** | Utility-first CSS framework for the glassmorphic, premium dark-mode UI. |

### Cloud Infrastructure
| Technology | Purpose |
|------------|---------|
| **Google Cloud Run** | Serverless container hosting. Auto-scales from 0 to N instances. Two services: `calai-backend` and `calai-volume-estimator`. |
| **Google Vertex AI** | Enterprise-grade LLM API. Gemini 1.5 Flash powers both the agentic pipeline and the chatbot. |
| **Google Cloud Build** | CI/CD. Builds Docker images, pushes to Artifact Registry, and deploys to Cloud Run on every `git push`. |
| **Google Artifact Registry** | Private Docker image repository in `asia-south1`. |
| **Google OAuth 2.0** | Secure user authentication via Google accounts. |

---

## ☁️ Deployment Infrastructure

CalAi runs on **two independent Google Cloud Run services** deployed via automated CI/CD pipelines.

```mermaid
flowchart TB
    subgraph DEV["👨‍💻 Developer"]
        GIT["git push origin main"]
    end

    subgraph GCB["⚙️ Google Cloud Build"]
        B1["cloudbuild.yaml\nBuilds calai-backend"]
        B2["cloudbuild-volume.yaml\nBuilds calai-volume-estimator"]
    end

    subgraph GAR["📦 Artifact Registry"]
        I1["calai-backend:latest"]
        I2["calai-volume-estimator:latest"]
    end

    subgraph GCR["🚀 Google Cloud Run"]
        S1["calai-backend\n1 CPU · 1GB RAM\nMin 1 instance"]
        S2["calai-volume-estimator\n2 CPU · 4GB RAM\nScale to zero"]
    end

    GIT --> B1
    GIT --> B2
    B1 --> I1
    B2 --> I2
    I1 --> S1
    I2 --> S2
    S1 -- "REST API call" --> S2

    style DEV fill:#1e293b,stroke:#38bdf8,color:#f8fafc
    style GCB fill:#f59e0b,stroke:#d97706,color:#000
    style GAR fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style GCR fill:#10b981,stroke:#059669,color:#fff
```

| Service | Image | CPU | Memory | Scaling | Region |
|---------|-------|-----|--------|---------|--------|
| `calai-backend` | `calai-repo/calai-backend:latest` | 1 vCPU | 1 GB | Min 1, Max 5 | `asia-south1` |
| `calai-volume-estimator` | `calai-repo/calai-volume-estimator:latest` | 2 vCPU | 4 GB | Min 0, Max 3 | `asia-south1` |

> **Why scale-to-zero for the Volume Estimator?** The heavy ML models are only needed when a user actively scans a meal. By scaling to zero at idle, we avoid burning GCP credits 24/7 on a 4GB container.

---

## 👨‍💻 Local Development Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- A Google Cloud project with Vertex AI enabled

### 1. Clone the Repository
```bash
git clone https://github.com/kavyajshah240706/CalAi.git
cd CalAi
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
# Google Cloud Vertex AI
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json

# Database
DATABASE_URL=postgresql://postgres:postgrespassword@db:5432/calai_db

# Volume Estimator Microservice
VOLUME_ESTIMATOR_URL=http://volume_estimator:5000
```

### 3. Run with Docker Compose
Spin up all three services — PostgreSQL, FastAPI backend, and Volume Estimator — with one command:
```bash
docker-compose up --build
```

### 4. Access the App
Open your browser and navigate to:
```
http://localhost:8000
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">
  <sub>Architected with ❤️ for precision nutrition tracking.</sub>
</div>

# CalAi (NutriFlow) Deployment Guide

This document outlines how to deploy the CalAi project into a production environment. The system consists of three main components:
1. **PostgreSQL Database** (with `pgvector`)
2. **FastAPI Backend** (Orchestrator and Static File Server)
3. **Flask Microservice** (Food Volume Estimator using OpenCV/ML)

## 1. Database Deployment (Supabase / Render)

Since the project uses `pgvector` for vector storage, you need a PostgreSQL provider that supports this extension. Supabase is highly recommended.

**Steps:**
1. Create a new project on [Supabase](https://supabase.com/).
2. Get your connection string (URI) from the Database settings (e.g., `postgresql://postgres:password@db.xxxx.supabase.co:5432/postgres`).
3. Run the database setup script locally one time to initialize the tables:
   ```bash
   set DATABASE_URL="your-supabase-url"
   python backend/setup_db.py
   ```

## 2. Flask Volume Estimator Deployment (Docker + AWS EC2 / Render)

The Flask app (`food_volume_estimation/app.py`) requires heavy computer vision libraries (OpenCV, Torch). It is already containerized using a Dockerfile.

**Steps using Render (Web Service):**
1. Connect your GitHub repository to [Render](https://render.com/).
2. Create a new "Web Service".
3. Point the Root Directory to `food_volume_estimation`.
4. Render will automatically detect the `Dockerfile` and build it.
5. Once deployed, note the service URL (e.g., `https://calai-volume-estimator.onrender.com`).

**Steps using AWS EC2 (Docker):**
1. Launch an EC2 instance (Ubuntu).
2. Install Docker.
3. Clone the repo and navigate to `food_volume_estimation`.
4. Run: `docker build -t volume_estimator .`
5. Run: `docker run -d -p 5000:5000 volume_estimator`

## 3. FastAPI Backend Deployment (Vercel / Railway / Render)

The FastAPI app (`backend/main.py`) acts as the orchestrator. It needs to know where the Database and the Flask service are located.

**Steps:**
1. Host the backend on a service like Render, Railway, or Heroku.
2. Set the following Environment Variables in your hosting dashboard:
   - `DATABASE_URL`: Your Supabase connection string.
   - `GEMINI_API_KEY`: Your Google Gemini API Key.
   - `VOLUME_ESTIMATOR_URL`: The URL of your deployed Flask service (e.g., `https://calai-volume-estimator.onrender.com`). *Note: You'll need to update `backend/agents/node3_orchestrator.py` to use this env var instead of hardcoding `localhost:5000`.*
3. Ensure the start command is:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```
4. *Important:* The FastAPI app serves the static frontend UI (`stitch_nutrivision_ai` folder). Ensure this folder is included in the deployment bundle.

## Post-Deployment Checklist
- [ ] Test the web application by visiting the FastAPI backend URL.
- [ ] Log in (or view the dashboard) and ensure `user_profiles` data loads successfully.
- [ ] Go to the Scanner, upload a food image, and verify that the request successfully routes through the FastAPI backend -> Gemini -> Flask Volume Estimator -> Database.

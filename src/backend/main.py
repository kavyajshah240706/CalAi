from fastapi import FastAPI, UploadFile, File, Form, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
# Load from root directory
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(root_dir, ".env"), override=True)
# Ensure the Enterprise flag is set for google-genai SDK
os.environ["GOOGLE_GENAI_USE_ENTERPRISE"] = "True"
import requests
import base64
import psycopg2

from src.backend.agents.schema import GraphState
from src.backend.agents.node1_nlp import node1_nlp_parser
from src.backend.agents.node2_data import node2_data_retrieval
from src.backend.agents.node3_math import node3_math_engine
from src.backend.agents.node4_recommender import node4_recommender

app = FastAPI()

# ─────────────────────────────────────────────
# AUTH UTILITIES
# ─────────────────────────────────────────────

# LoginRequest and GoogleLoginRequest are defined below with the auth routes

def check_ui_auth(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/login", status_code=303)
    return None

def get_api_user(request: Request) -> str:
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(db_url)

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

VOLUME_ESTIMATOR_URL = os.environ.get("VOLUME_ESTIMATOR_URL", "http://localhost:5000").rstrip("/")

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ─────────────────────────────────────────────
# UI ROUTES (all require auth)
# ─────────────────────────────────────────────

@app.get("/login")
def serve_login():
    return FileResponse(os.path.join(FRONTEND_DIR, "login", "code.html"))

class GoogleLoginRequest(BaseModel):
    credential: str

@app.post("/api/auth/google")
def google_login(req: GoogleLoginRequest):
    try:
        # Verify the JWT token natively via Google's tokeninfo API
        token_info_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={req.credential}"
        response = requests.get(token_info_url)
        if response.status_code != 200:
            return JSONResponse({"success": False, "error": "Invalid Google token"}, status_code=401)
            
        data = response.json()
        email = data.get("email", "").lower()
        name = data.get("name", "CalAi User")
        
        if not email:
            return JSONResponse({"success": False, "error": "Email not found in token"}, status_code=400)
            
        # Check if user profile exists, if not, create one with their real name!
        conn = get_db_connection()
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM user_profiles WHERE user_id = %s", (email,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO user_profiles (user_id, name, email, age, gender, height_cm, weight_kg, activity_level, daily_calorie_target, protein_goal_g, carbs_goal_g, fats_goal_g)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (email, name, email, 30, 'other', 170.0, 70.0, 'moderate', 2000.0, 150.0, 200.0, 65.0))
        cursor.close()
        conn.close()

        res = JSONResponse({"success": True, "email": email})
        res.set_cookie("session_token", email, httponly=True, max_age=86400*30)
        return res
    except Exception as e:
        print(f"Google auth error: {e}")
        return JSONResponse({"success": False, "error": "Server auth error"}, status_code=500)

class LoginRequest(BaseModel):
    username: str

@app.post("/api/login")
def login(req: LoginRequest):
    username = req.username.strip().lower()
    if not username:
        return JSONResponse({"success": False, "error": "Username required"}, status_code=400)
    
    # Auto-provision profile for demo/new users so dashboard loads properly
    try:
        conn = get_db_connection()
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM user_profiles WHERE user_id = %s", (username,))
        if not cursor.fetchone():
            display_name = "Demo User" if username == "demo_user" else username.title()
            cursor.execute("""
                INSERT INTO user_profiles (user_id, name, email, age, gender, height_cm, weight_kg, activity_level, daily_calorie_target, protein_goal_g, carbs_goal_g, fats_goal_g)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (username, display_name, '', 25, 'other', 170.0, 70.0, 'moderate', 2000.0, 150.0, 200.0, 65.0))
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Auto-provision profile error: {e}")
    
    res = JSONResponse({"success": True})
    res.set_cookie("session_token", username, httponly=True, max_age=86400*30)
    return res

@app.post("/api/logout")
def logout():
    res = JSONResponse({"success": True})
    res.delete_cookie("session_token")
    return res

@app.get("/")
def serve_dashboard(request: Request):
    auth = check_ui_auth(request)
    if auth: return auth
    return FileResponse(os.path.join(FRONTEND_DIR, "nutriflow_dashboard", "code.html"))

@app.get("/scanner")
def serve_scanner(request: Request):
    auth = check_ui_auth(request)
    if auth: return auth
    return FileResponse(os.path.join(FRONTEND_DIR, "ai_nutrition_scanner", "code.html"))

@app.get("/history")
def serve_history(request: Request):
    auth = check_ui_auth(request)
    if auth: return auth
    return FileResponse(os.path.join(FRONTEND_DIR, "meal_history_logs", "code.html"))

@app.get("/profile")
def serve_profile(request: Request):
    auth = check_ui_auth(request)
    if auth: return auth
    return FileResponse(os.path.join(FRONTEND_DIR, "profile_health_goals", "code.html"))

@app.get("/chat")
def serve_chat(request: Request):
    auth = check_ui_auth(request)
    if auth: return auth
    return FileResponse(os.path.join(FRONTEND_DIR, "nutriflow_chat", "code.html"))

# ─────────────────────────────────────────────
# FOOD SCANNING API (Nodes 1-4)
# ─────────────────────────────────────────────

@app.post("/analyze-food")
async def analyze_food(
    request: Request,
    image: UploadFile = File(...),
    mode: str = Form("vlm")
):
    """Step 1: Estimate volume and extract food details (Node 1)"""
    user_id = get_api_user(request)
    image_bytes = await image.read()
    
    if mode == "vlm":
        try:
            img_b64 = base64.b64encode(image_bytes).decode("utf-8")
            user_input = "Look at this image. Identify the food. No depth model estimate is provided, use your visual judgement to estimate a realistic serving volume."
            state = GraphState(user_input=user_input, image_base64=img_b64)
            
            # ONLY RUN NODE 1
            state = node1_nlp_parser(state)
            
            pq = state.parsed_query or {}
            volume_ml = pq.get("quantity", 0)
            
            return {
                "success": True,
                "segments": [{
                    "segment_id": 0,
                    "parsed_query": pq,
                    "volume_ml": volume_ml,
                    "image_url": None,
                    "image_base64": img_b64
                }]
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": f"VLM analysis failed: {str(e)}"}
            )
    
    # Model mode (default external port 5000 service)
    files = {"image": (image.filename, image_bytes, image.content_type)}
    
    try:
        vol_resp = requests.post(f"{VOLUME_ESTIMATOR_URL}/estimate-volume", files=files)
        if vol_resp.status_code != 200:
            return {"error": "Volume estimation failed"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Volume estimation service unavailable: {e}"}
        
    vol_data = vol_resp.json()
    segments = vol_data.get("segments", [])
    final_results = []
    
    for seg in segments:
        volume_ml = seg["volume"]
        img_endpoint = vol_data.get("output_images", [])[seg["segment_id"]]
        
        try:
            img_resp = requests.get(f"{VOLUME_ESTIMATOR_URL}{img_endpoint}")
            img_b64 = base64.b64encode(img_resp.content).decode("utf-8") if img_resp.status_code == 200 else None
        except Exception:
            img_b64 = None
            
        user_input = f"Look at this image. Identify the food. The estimated volume is {volume_ml} ml."
        state = GraphState(user_input=user_input, image_base64=img_b64)
        
        # ONLY RUN NODE 1
        state = node1_nlp_parser(state)
        
        final_results.append({
            "segment_id": seg["segment_id"],
            "parsed_query": state.parsed_query,
            "volume_ml": volume_ml,
            "image_url": f"{VOLUME_ESTIMATOR_URL}{img_endpoint}",
            "image_base64": img_b64
        })
        
    return {
        "success": True,
        "segments": final_results
    }

class ConfirmFoodRequest(BaseModel):
    segment_id: int
    food_name: str
    quantity: float
    unit: str
    state_desc: str
    image_url: Optional[str] = None
    image_base64: Optional[str] = None

@app.post("/confirm-food")
async def confirm_food(request: Request, req: ConfirmFoodRequest):
    """Step 2: Take confirmed details, run Nodes 2,3,4 and save to DB"""
    user_id = get_api_user(request)
    try:
        state = GraphState(
            user_input="", 
            image_base64=req.image_base64,
            parsed_query={
                "food_name": req.food_name,
                "quantity": req.quantity,
                "unit": req.unit,
                "state": req.state_desc
            }
        )
        
        # Run remaining nodes with error tracking
        print(f"[confirm-food] Running Node 2 for: {req.food_name}, qty={req.quantity} {req.unit}")
        state = node2_data_retrieval(state)
        print(f"[confirm-food] Node 2 done. Profile: {state.profile}")
        
        state = node3_math_engine(state)
        print(f"[confirm-food] Node 3 done. Nutrition: {state.calculated_nutrition}")
        
        state = node4_recommender(state)
        print(f"[confirm-food] Node 4 done. Has recommendations: {bool(state.recommendations)}")
        
        calc = state.calculated_nutrition or {}
        
        # Insert into DB
        try:
            conn = get_db_connection()
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO meal_logs (user_id, food_name, weight_g, calories, protein, carbs, fats, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, 
                req.food_name, 
                calc.get("weight_g", 0), 
                calc.get("calories", 0), 
                calc.get("protein", 0), 
                calc.get("carbs", 0), 
                calc.get("fats", 0), 
                req.image_url or ""
            ))
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error logging meal: {e}")

        return {
            "success": True,
            "calculated_nutrition": calc,
            "recommendations": state.recommendations
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ─────────────────────────────────────────────
# PROFILE API
# ─────────────────────────────────────────────

class UserProfileRequest(BaseModel):
    name: str
    email: str
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    activity_level: str
    daily_calorie_target: float
    protein_goal_g: float
    carbs_goal_g: float
    fats_goal_g: float

@app.get("/api/profile")
def get_profile(request: Request):
    user_id = get_api_user(request)
    try:
        conn = get_db_connection()
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s;", (user_id,))
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        
        if not row:
            # Auto-create a default profile for new users
            print(f"[profile] No profile for '{user_id}', creating default...")
            cursor.execute("""
                INSERT INTO user_profiles (user_id, name, email, age, gender, height_cm, weight_kg, 
                    activity_level, daily_calorie_target, protein_goal_g, carbs_goal_g, fats_goal_g)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (user_id, 'New User', '', 25, 'Male', 170, 70, 'Moderately Active', 2000, 150, 250, 65))
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s;", (user_id,))
            row = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
        
        cursor.close()
        conn.close()
        
        profile_data = dict(zip(columns, row))
        return {"success": True, "profile": profile_data}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/profile")
def update_profile(request: Request, req: UserProfileRequest):
    user_id = get_api_user(request)
    try:
        conn = get_db_connection()
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if profile exists
        cursor.execute("SELECT 1 FROM user_profiles WHERE user_id = %s;", (user_id,))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute("""
                UPDATE user_profiles 
                SET name=%s, email=%s, age=%s, gender=%s, height_cm=%s, weight_kg=%s, 
                    activity_level=%s, daily_calorie_target=%s, protein_goal_g=%s, 
                    carbs_goal_g=%s, fats_goal_g=%s
                WHERE user_id=%s;
            """, (
                req.name, req.email, req.age, req.gender, req.height_cm, req.weight_kg,
                req.activity_level, req.daily_calorie_target, req.protein_goal_g,
                req.carbs_goal_g, req.fats_goal_g, user_id
            ))
        else:
            cursor.execute("""
                INSERT INTO user_profiles (user_id, name, email, age, gender, height_cm, weight_kg,
                    activity_level, daily_calorie_target, protein_goal_g, carbs_goal_g, fats_goal_g)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                user_id, req.name, req.email, req.age, req.gender, req.height_cm, req.weight_kg,
                req.activity_level, req.daily_calorie_target, req.protein_goal_g,
                req.carbs_goal_g, req.fats_goal_g
            ))
        
        cursor.close()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ─────────────────────────────────────────────
# MEAL HISTORY & DASHBOARD API
# ─────────────────────────────────────────────

@app.get("/api/history")
def get_history(request: Request):
    user_id = get_api_user(request)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, food_name, weight_g, calories, protein, carbs, fats, image_url, created_at
            FROM meal_logs 
            WHERE user_id = %s
            ORDER BY created_at DESC;
        """, (user_id,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        meals = []
        for row in rows:
            meal = dict(zip(columns, row))
            if meal["created_at"]:
                meal["created_at"] = meal["created_at"].isoformat()
            meals.append(meal)
            
        cursor.close()
        conn.close()
        return {"success": True, "meals": meals}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/dashboard")
def get_dashboard(request: Request):
    user_id = get_api_user(request)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get today's meals
        from datetime import date
        today = date.today()
        
        cursor.execute("""
            SELECT id, food_name, weight_g, calories, protein, carbs, fats, image_url, created_at
            FROM meal_logs 
            WHERE user_id = %s AND DATE(created_at) = %s
            ORDER BY created_at DESC;
        """, (user_id, today))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        today_meals = []
        totals = {"calories": 0, "protein": 0, "carbs": 0, "fats": 0}
        
        for row in rows:
            meal = dict(zip(columns, row))
            if meal["created_at"]:
                meal["created_at"] = meal["created_at"].isoformat()
            today_meals.append(meal)
            
            totals["calories"] += meal["calories"] or 0
            totals["protein"] += meal["protein"] or 0
            totals["carbs"] += meal["carbs"] or 0
            totals["fats"] += meal["fats"] or 0
            
        cursor.close()
        conn.close()
        
        return {
            "success": True, 
            "today_meals": today_meals,
            "totals": totals
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ─────────────────────────────────────────────
# DAILY INSIGHTS API (Gemini-powered)
# ─────────────────────────────────────────────

@app.get("/api/daily-insights")
def get_daily_insights(request: Request):
    user_id = get_api_user(request)
    try:
        import re
        from google import genai
        from google.genai import types
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get Profile
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s;", (user_id,))
        prof_row = cursor.fetchone()
        if not prof_row:
            return {"success": False, "error": "Profile not found. Please set up your profile first."}
        prof_cols = [desc[0] for desc in cursor.description]
        profile = dict(zip(prof_cols, prof_row))
        
        # Get Today's Meals
        from datetime import date
        today = date.today()
        cursor.execute("""
            SELECT food_name, calories, protein, carbs, fats
            FROM meal_logs 
            WHERE user_id = %s AND DATE(created_at) = %s
        """, (user_id, today))
        meal_rows = cursor.fetchall()
        meal_cols = [desc[0] for desc in cursor.description]
        meals = [dict(zip(meal_cols, row)) for row in meal_rows]
        
        cursor.close()
        conn.close()
        
        # Initialize Gemini
        client = genai.Client(vertexai=True, project="gemini-project-2-500616", location="us-central1"),
            http_options=types.HttpOptions(api_version="v1")
        )
        
        prompt = f"""
You are an elite clinical sports nutritionist AI.
Analyze the user's daily meals against their goals.

USER GOALS:
Calories: {profile.get('daily_calorie_target')}
Protein: {profile.get('protein_goal_g')}g
Carbs: {profile.get('carbs_goal_g')}g
Fats: {profile.get('fats_goal_g')}g

TODAY'S MEALS:
{meals}

INSTRUCTIONS:
1. First, think step-by-step in a <thinking> block. Calculate the totals, compare them to the goals, and identify what is missing or excessive. Ensure your math is perfectly accurate to avoid hallucinations.
2. Then, provide your final actionable insight in an <insight> block. Keep the insight under 4 sentences, formatted cleanly with markdown. Be highly specific (e.g. "You need 40g more protein, eat 150g of chicken breast for dinner"). Do not include the thinking block in the insight block.

Output format:
<thinking>
...
</thinking>
<insight>
...
</insight>
"""
        
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}]
            )
        )
        
        text = response.text
        insight_match = re.search(r'<insight>(.*?)</insight>', text, re.DOTALL)
        if insight_match:
            insight = insight_match.group(1).strip()
        else:
            insight = text.strip()
            
        return {"success": True, "insight": insight}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ─────────────────────────────────────────────
# QUICK LOG (text bar meal logging)
# ─────────────────────────────────────────────

class QuickLogRequest(BaseModel):
    text: str

@app.post("/api/quick-log")
async def quick_log(request: Request, req: QuickLogRequest):
    """Quick log a meal from text. Uses a single fast Gemini call instead of the full 4-node pipeline."""
    user_id = get_api_user(request)
    try:
        from google import genai
        from google.genai import types
        import json
        
        client = genai.Client(vertexai=True, project="gemini-project-2-500616", location="us-central1"),
            http_options=types.HttpOptions(api_version="v1")
        )
        
        prompt = f"""Analyze this food description and estimate its nutritional content.
Food: "{req.text}"

Return ONLY a valid JSON object with these exact keys:
{{"food_name": "name of the food", "weight_g": estimated_weight_in_grams, "calories": estimated_kcal, "protein": grams, "carbs": grams, "fats": grams}}

Be accurate. Use standard nutritional databases as reference. Return ONLY the JSON, no markdown, no extra text."""
        
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1)
        )
        
        # Parse the JSON from Gemini's response
        raw = response.text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()
        
        calc = json.loads(raw)
        food_name = calc.get("food_name", req.text)
        
        # Save to DB
        try:
            conn = get_db_connection()
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO meal_logs (user_id, food_name, weight_g, calories, protein, carbs, fats, image_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                food_name,
                calc.get("weight_g", 0),
                calc.get("calories", 0),
                calc.get("protein", 0),
                calc.get("carbs", 0),
                calc.get("fats", 0),
                ""
            ))
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error logging quick meal: {e}")
        
        return {
            "success": True,
            "calculated_nutrition": calc,
            "recommendations": f"Logged {food_name} successfully!"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

# ─────────────────────────────────────────────
# MEAL DELETE
# ─────────────────────────────────────────────

@app.delete("/api/meal/{meal_id}")
def delete_meal(request: Request, meal_id: int):
    """Delete a meal log entry by its ID."""
    user_id = get_api_user(request)
    try:
        conn = get_db_connection()
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("DELETE FROM meal_logs WHERE id = %s AND user_id = %s", (meal_id, user_id))
        deleted = cursor.rowcount
        cursor.close()
        conn.close()
        if deleted > 0:
            return {"success": True, "message": f"Meal {meal_id} deleted."}
        return {"success": False, "error": "Meal not found."}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ─────────────────────────────────────────────
# AGENTIC CHATBOT
# ─────────────────────────────────────────────

@app.get("/api/chat/history")
def get_chat_history(request: Request):
    user_id = get_api_user(request)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role, message, created_at FROM chat_logs WHERE user_id = %s ORDER BY id ASC;", (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        history = [{"role": row[0], "message": row[1], "created_at": row[2].isoformat()} for row in rows]
        return {"success": True, "history": history}
    except Exception as e:
        return {"success": False, "error": str(e)}

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat/message")
def send_chat_message(request: Request, req: ChatRequest):
    user_id = get_api_user(request)
    try:
        from google import genai
        from google.genai import types
        
        user_message = req.message.strip()
        
        conn = get_db_connection()
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Save user message
        cursor.execute("INSERT INTO chat_logs (user_id, role, message) VALUES (%s, %s, %s)", (user_id, 'user', user_message))
        
        # Fetch history
        cursor.execute("SELECT role, message FROM chat_logs WHERE user_id = %s ORDER BY id DESC LIMIT 10;", (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        history = []
        for role, msg in reversed(rows):
            history.append(types.Content(role="model" if role == "assistant" else "user", parts=[types.Part.from_text(text=msg)]))
            
        def get_recent_meals_tool() -> str:
            """Gets the user's logged meals for the day to analyze their intake."""
            conn2 = get_db_connection()
            cursor2 = conn2.cursor()
            cursor2.execute("SELECT food_name, weight_g, calories, protein, carbs, fats, created_at FROM meal_logs WHERE user_id = %s ORDER BY created_at DESC LIMIT 15;", (user_id,))
            meals = cursor2.fetchall()
            cursor2.close()
            conn2.close()
            if not meals: return "No meals logged recently."
            return "\n".join([f"- {m[6].strftime('%Y-%m-%d %H:%M')}: {m[0]} ({m[1]}g) -> {m[2]}kcal (P:{m[3]}g, C:{m[4]}g, F:{m[5]}g)" for m in meals])
            
        def get_user_profile_tool() -> str:
            """Gets the user's specific health goals, including daily calorie, protein, carbs, and fats targets."""
            conn2 = get_db_connection()
            cursor2 = conn2.cursor()
            cursor2.execute("SELECT daily_calorie_target, protein_goal_g, carbs_goal_g, fats_goal_g FROM user_profiles WHERE user_id = %s;", (user_id,))
            prof = cursor2.fetchone()
            cursor2.close()
            conn2.close()
            if not prof: return "No profile found."
            return f"Goals: {prof[0]} kcal, {prof[1]}g Protein, {prof[2]}g Carbs, {prof[3]}g Fats."
        
        client = genai.Client(vertexai=True, project="gemini-project-2-500616", location="us-central1"),
            http_options=types.HttpOptions(api_version="v1")
        )
        
        sys_prompt = "You are CalAi AI, an elite clinical sports nutritionist. You are autonomous. Call get_user_profile_tool to check goals, or get_recent_meals_tool to see what they ate today if they ask about it. You can also use google_search to look up external nutritional facts."
        
        chat = client.chats.create(
            model="gemini-1.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=sys_prompt,
                temperature=0.4,
                tools=[get_recent_meals_tool, get_user_profile_tool, {"google_search": {}}]
            ),
            history=history[:-1] if len(history) > 0 else None
        )
        
        response = chat.send_message(user_message)
        bot_message = response.text or "I'm sorry, I couldn't generate a response."
        
        # Save assistant message
        conn = get_db_connection()
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chat_logs (user_id, role, message) VALUES (%s, %s, %s)", (user_id, 'assistant', bot_message))
        cursor.close()
        conn.close()
        
        return {"success": True, "response": bot_message}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

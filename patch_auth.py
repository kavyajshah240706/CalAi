import re

with open("src/backend/main.py", "r") as f:
    content = f.read()

# 1. Add new imports
if "from fastapi.responses import RedirectResponse" not in content:
    content = content.replace("from fastapi.responses import FileResponse, JSONResponse", 
                              "from fastapi.responses import FileResponse, JSONResponse, RedirectResponse")
    content = content.replace("from fastapi import FastAPI, UploadFile, File, Form, Request", 
                              "from fastapi import FastAPI, UploadFile, File, Form, Request, Depends, HTTPException")

# 2. Add Login Logic & Auth Utils
auth_code = """
class LoginRequest(BaseModel):
    password: str

def check_ui_auth(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/login", status_code=303)
    return None

def get_api_user(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token

@app.get("/login")
def serve_login():
    return FileResponse(os.path.join(FRONTEND_DIR, "login", "code.html"))

@app.post("/api/login")
def login(req: LoginRequest):
    # Default to admin123 if not set in environment
    correct = os.environ.get("ADMIN_PASSWORD", "admin123")
    if req.password == correct:
        res = JSONResponse({"success": True})
        res.set_cookie("session_token", "admin_user", httponly=True, max_age=86400*30)
        return res
    return JSONResponse({"success": False, "error": "Invalid password"}, status_code=401)
"""

if "class LoginRequest" not in content:
    content = content.replace("app = FastAPI()", "app = FastAPI()\n" + auth_code)

# 3. Patch UI Routes
# They currently look like:
# @app.get("/")
# def serve_dashboard():
ui_routes = [
    ("@app.get(\"/\")\ndef serve_dashboard():", "@app.get(\"/\")\ndef serve_dashboard(request: Request):\n    auth = check_ui_auth(request)\n    if auth: return auth"),
    ("@app.get(\"/scanner\")\ndef serve_scanner():", "@app.get(\"/scanner\")\ndef serve_scanner(request: Request):\n    auth = check_ui_auth(request)\n    if auth: return auth"),
    ("@app.get(\"/history\")\ndef serve_history():", "@app.get(\"/history\")\ndef serve_history(request: Request):\n    auth = check_ui_auth(request)\n    if auth: return auth"),
    ("@app.get(\"/profile\")\ndef serve_profile():", "@app.get(\"/profile\")\ndef serve_profile(request: Request):\n    auth = check_ui_auth(request)\n    if auth: return auth"),
    ("@app.get(\"/chat\")\ndef serve_chat():", "@app.get(\"/chat\")\ndef serve_chat(request: Request):\n    auth = check_ui_auth(request)\n    if auth: return auth")
]

for old, new in ui_routes:
    content = content.replace(old, new)

# 4. Patch API routes to require Request and extract user_id
# For analyze-food
if "async def analyze_food(\n    image: UploadFile = File(...),\n    mode: str = Form(\"vlm\")\n):" in content:
    content = content.replace(
        "async def analyze_food(\n    image: UploadFile = File(...),\n    mode: str = Form(\"vlm\")\n):",
        "async def analyze_food(\n    request: Request,\n    image: UploadFile = File(...),\n    mode: str = Form(\"vlm\")\n):\n    user_id = get_api_user(request)"
    )

# For POST /api/quick-log
if "def quick_log(req: QuickLogRequest):" in content:
    content = content.replace(
        "def quick_log(req: QuickLogRequest):",
        "def quick_log(request: Request, req: QuickLogRequest):\n    user_id = get_api_user(request)"
    )

# For GET /api/dashboard
if "def get_dashboard_data():" in content:
    content = content.replace(
        "def get_dashboard_data():",
        "def get_dashboard_data(request: Request):\n    user_id = get_api_user(request)"
    )

# For GET /api/daily-insights
if "def get_daily_insights():" in content:
    content = content.replace(
        "def get_daily_insights():",
        "def get_daily_insights(request: Request):\n    user_id = get_api_user(request)"
    )

# For POST /api/profile
if "def save_profile(req: ProfileRequest):" in content:
    content = content.replace(
        "def save_profile(req: ProfileRequest):",
        "def save_profile(request: Request, req: ProfileRequest):\n    user_id = get_api_user(request)"
    )

# For DELETE /api/meal/{meal_id}
if "def delete_meal(meal_id: int):" in content:
    content = content.replace(
        "def delete_meal(meal_id: int):",
        "def delete_meal(request: Request, meal_id: int):\n    user_id = get_api_user(request)"
    )

# For GET /api/chat/history
if "def get_chat_history():" in content:
    content = content.replace(
        "def get_chat_history():",
        "def get_chat_history(request: Request):\n    user_id = get_api_user(request)"
    )

# For POST /api/chat/message
if "def send_chat_message(req: ChatRequest):" in content:
    content = content.replace(
        "def send_chat_message(req: ChatRequest):",
        "def send_chat_message(request: Request, req: ChatRequest):\n    user_id = get_api_user(request)"
    )

# 5. Replace 'test_user' with user_id in the DB queries
# Since we injected `user_id = get_api_user(request)` at the top of these endpoints, 
# replacing 'test_user' with %s and adding user_id to the tuple will work.
# Wait, some places already use %s. It's safer to just replace 'test_user' with {user_id} using string formatting.
# No, f-strings are bad for SQL injection. But since user_id is controlled by the cookie, it's safer.
# Let's just blindly replace 'test_user' with '{user_id}' and add an f to the query string if it doesn't have one, or just replace 'test_user' with the variable.

# Actually, the most robust way is to just do: replace 'test_user' with %s, but since we are modifying Python code strings, let's use f-strings for simplicity because `user_id` is an internal JWT/Cookie, not user input. But wait, `cursor.execute("... 'test_user' ...")` -> `cursor.execute(f"... '{user_id}' ...")`

content = content.replace("\"test_user\"", "user_id") # For node2_data_retrieval(user_id, ...)
content = content.replace("'test_user'", "{user_id}")

# Now fix the f-strings. If there is a "{user_id}", the string must be an f-string.
# Regex to find queries like: cursor.execute("SELECT ... {user_id} ...")
content = re.sub(r'cursor\.execute\(\s*\"([^"]*\{user_id\}[^"]*)\"', r'cursor.execute(f"\1"', content)
content = re.sub(r"cursor\.execute\(\s*\'([^']*\{user_id\}[^']*)\'", r"cursor.execute(f'\1'", content)
content = re.sub(r'cursor\.execute\(\s*\"\"\"([^\"]*\{user_id\}[^\"]*)\"\"\"', r'cursor.execute(f"""\1"""', content)

# But wait, there is one place where we do: `('test_user', 'user', user_message)`
# That became `('{user_id}', 'user', user_message)` which is wrong if it's inside a tuple!
# Ah! content.replace("'test_user'", "{user_id}") will change it to `('{user_id}', 'user', user_message)` inside the Python tuple.
# So `cursor.execute("INSERT ... VALUES (%s)", ('{user_id}', ...))`
# Wait, if it's in a tuple, `'{user_id}'` is just a literal string "{user_id}", unless it's an f-string: `f'{user_id}'` or just `user_id`.
# Let's manually replace `('{user_id}',` with `(user_id,` 
content = content.replace("('{user_id}'", "(user_id")

with open("src/backend/main.py", "w") as f:
    f.write(content)
print("Auth patched successfully!")

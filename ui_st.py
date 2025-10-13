import streamlit as st
from PIL import Image
import os
import time
from datetime import datetime
import uuid
import threading
import queue
import subprocess
import requests
import json

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="Interactive Nutrition Assistant", page_icon="🍽️", layout="wide")

# -------------------- CUSTOM CSS --------------------
st.markdown("""
<style>
.terminal-output {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    max-height: 60vh;
    overflow-y: auto;
    white-space: pre-wrap;
    line-height: 1.5;
    color: #e2e8f0;
}
.status-running {
    color: #fbbf24;
    font-weight: bold;
}
.status-waiting {
    color: #34d399;
    font-weight: bold;
    animation: blink 1.5s infinite;
}
@keyframes blink {
    0%, 50%, 100% { opacity: 1; }
    25%, 75% { opacity: 0.5; }
}
.input-prompt {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# -------------------- HELPER FUNCTIONS --------------------
def create_new_session():
    """Creates a unique session folder."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"session_{timestamp}_{str(uuid.uuid4())[:8]}"
    session_folder = os.path.join("sessions", session_id)
    os.makedirs(session_folder, exist_ok=True)
    os.makedirs(f"{session_folder}/calorie_outputs", exist_ok=True)
    return session_folder

def check_input_server():
    """Check if input server is running"""
    try:
        response = requests.get('http://localhost:5001/status', timeout=2)
        return response.status_code == 200
    except:
        return False

def submit_user_input(user_input):
    """Submit user input to the input server"""
    try:
        response = requests.post(
            'http://localhost:5001/submit-input',
            json={'input': user_input},
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Failed to submit input: {e}")
        return False

def read_output_thread(pipe, output_queue):
    """Thread to read stdout"""
    try:
        for line in iter(pipe.readline, ''):
            if line:
                output_queue.put(('output', line))
        pipe.close()
    except Exception as e:
        output_queue.put(('error', f"Read error: {e}"))

def run_agent_process(command, output_queue):
    """Run agent process"""
    try:
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        env['PYTHONIOENCODING'] = 'utf-8'
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            env=env,
            text=True,
            encoding='utf-8'
        )
        
        # Start reader thread
        reader_thread = threading.Thread(
            target=read_output_thread,
            args=(process.stdout, output_queue),
            daemon=True
        )
        reader_thread.start()
        
        # Wait for process to complete
        process.wait()
        reader_thread.join(timeout=2)
        
        output_queue.put(('finished', process.returncode))
        
    except Exception as e:
        output_queue.put(('error', str(e)))

# -------------------- SESSION STATE --------------------
if "session_folder" not in st.session_state:
    st.session_state.session_folder = None
if "terminal_output" not in st.session_state:
    st.session_state.terminal_output = []
if "process_running" not in st.session_state:
    st.session_state.process_running = False
if "waiting_for_input" not in st.session_state:
    st.session_state.waiting_for_input = False
if "output_queue" not in st.session_state:
    st.session_state.output_queue = None
if "process_thread" not in st.session_state:
    st.session_state.process_thread = None
if "last_output_line" not in st.session_state:
    st.session_state.last_output_line = ""

# -------------------- UI HEADER --------------------
st.title("🍽️ Interactive Nutrition Assistant")

# Check if input server is running
if not check_input_server():
    st.error("⚠️ Input Server not running! Please start it first:")
    st.code("python input_server.py", language="bash")
    st.stop()

# -------------------- SIDEBAR --------------------
st.sidebar.markdown("### Session Management")
if st.sidebar.button("🆕 New Session", use_container_width=True):
    st.session_state.session_folder = create_new_session()
    st.session_state.terminal_output = []
    st.session_state.process_running = False
    st.session_state.waiting_for_input = False
    st.session_state.output_queue = None
    st.session_state.last_output_line = ""
    st.rerun()

if st.session_state.session_folder:
    st.sidebar.success(f"📁 Active: {os.path.basename(st.session_state.session_folder)}")
else:
    st.sidebar.warning("⚠️ Create a session to start")
    st.stop()

# -------------------- MAIN INTERFACE --------------------
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 📤 Upload Image")
    uploaded_file = st.file_uploader("Food image (optional)", type=["jpg", "jpeg", "png"])
    
    image_path = None
    if uploaded_file:
        image_path = os.path.join(st.session_state.session_folder, "uploaded_image.jpg")
        image = Image.open(uploaded_file)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(image_path, 'JPEG')
        st.image(image_path, caption="Uploaded", width=250)

with col2:
    st.markdown("### 💬 Your Query")
    user_query = st.text_input(
        "What would you like to know?",
        placeholder="e.g., 'Calculate calories', 'Is this healthy?'",
        disabled=st.session_state.process_running,
        key="query_input"
    )
    
    if st.button("▶️ Run Agent", disabled=st.session_state.process_running):
        # Build command
        cmd = [
            "python", "-u",
            "router_agent.py", 
            st.session_state.session_folder,
            user_query if user_query else ""
        ]
        
        if image_path:
            cmd.append(image_path)
        
        # Initialize
        st.session_state.output_queue = queue.Queue()
        st.session_state.terminal_output = ["🚀 Starting agent...\n\n"]
        st.session_state.process_running = True
        st.session_state.waiting_for_input = False
        st.session_state.last_output_line = ""
        
        # Start process
        st.session_state.process_thread = threading.Thread(
            target=run_agent_process,
            args=(cmd, st.session_state.output_queue),
            daemon=True
        )
        st.session_state.process_thread.start()
        st.rerun()

# -------------------- TERMINAL OUTPUT --------------------
if st.session_state.process_running or st.session_state.waiting_for_input:
    st.markdown("### 🖥️ Agent Terminal")
    
    # Process output queue
    messages_processed = 0
    max_messages = 200
    
    while not st.session_state.output_queue.empty() and messages_processed < max_messages:
        try:
            msg_type, msg_data = st.session_state.output_queue.get_nowait()
            messages_processed += 1
            
            if msg_type == 'output':
                st.session_state.terminal_output.append(msg_data)
                st.session_state.last_output_line = msg_data.strip()
                
                # Check if waiting for input
                if '[WAITING_FOR_INPUT]' in msg_data:
                    st.session_state.waiting_for_input = True
            
            elif msg_type == 'finished':
                st.session_state.process_running = False
                st.session_state.waiting_for_input = False
                st.session_state.terminal_output.append(f"\n\n✅ Agent finished (exit code: {msg_data})\n")
            
            elif msg_type == 'error':
                st.session_state.process_running = False
                st.session_state.waiting_for_input = False
                st.session_state.terminal_output.append(f"\n\n❌ Error: {msg_data}\n")
        
        except queue.Empty:
            break
    
    # Display status
    if st.session_state.waiting_for_input:
        st.markdown('<p class="status-waiting">⏳ WAITING FOR YOUR INPUT...</p>', unsafe_allow_html=True)
    elif st.session_state.process_running:
        st.markdown('<p class="status-running">▶️ Agent Running...</p>', unsafe_allow_html=True)
    
    # Display terminal
    terminal_text = "".join(st.session_state.terminal_output)
    st.markdown('<div class="terminal-output">', unsafe_allow_html=True)
    st.code(terminal_text, language='text')
    st.markdown('</div>', unsafe_allow_html=True)
    
    # -------------------- INPUT FORM --------------------
    if st.session_state.waiting_for_input:
        st.markdown("---")
        st.markdown('<div class="input-prompt">📝 Agent is waiting for your response</div>', unsafe_allow_html=True)
        
        # Extract the last meaningful prompt
        last_prompt = st.session_state.last_output_line[:300] if st.session_state.last_output_line else "Provide your input"
        st.info(f"**Prompt:** {last_prompt}")
        
        with st.form(key="user_input_form", clear_on_submit=True):
            user_input = st.text_area(
                "Your answer:",
                height=150,
                placeholder="Type your response here..."
            )
            
            submitted = st.form_submit_button("📤 Submit Response", use_container_width=True)
            
            if submitted:
                if user_input.strip():
                    # Submit to input server
                    if submit_user_input(user_input.strip()):
                        st.session_state.terminal_output.append(f"\n✅ [YOU SUBMITTED]:\n{user_input}\n\n")
                        st.session_state.waiting_for_input = False
                        st.success(f"✅ Sent: {user_input[:50]}...")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Failed to send input. Please try again.")
                else:
                    st.warning("Please enter a response")
    else:
        # Auto-refresh when running
        if st.session_state.process_running:
            time.sleep(0.5)
            st.rerun()

# -------------------- RESULTS --------------------
# -------------------- RESULTS --------------------
if not st.session_state.process_running and not st.session_state.waiting_for_input and len(st.session_state.terminal_output) > 1:
    st.success("✅ Agent finished! You can start a new request.")
    
    # ADD THIS: Reset state to allow new query in same session
    col_a, col_b = st.columns(2)
    
    with col_a:
        if st.button("🔄 New Query (Same Session)", use_container_width=True):
            st.session_state.terminal_output = []
            st.session_state.process_running = False
            st.session_state.waiting_for_input = False
            st.rerun()
    
    with col_b:
        if st.button("🆕 New Session", use_container_width=True):
            st.session_state.session_folder = create_new_session()
            st.session_state.terminal_output = []
            st.session_state.process_running = False
            st.session_state.waiting_for_input = False
            st.rerun()
    
    # Check for results
    output_folder = f"{st.session_state.session_folder}/calorie_outputs"
    if os.path.exists(output_folder):
        output_files = sorted([f for f in os.listdir(output_folder) if f.endswith('.json')])
        if output_files:
            st.markdown("### 📊 Results")
            latest_file = output_files[-1]
            filepath = os.path.join(output_folder, latest_file)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    result_data = f.read()
                
                st.json(result_data)
                
                st.download_button(
                    "💾 Download Results",
                    result_data,
                    file_name=latest_file,
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"Error loading results: {e}")
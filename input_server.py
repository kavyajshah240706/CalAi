"""
Simple Flask server to handle user input for dialogue agent
Run this first: python input_server.py
"""

from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

# Store pending input requests
pending_input = {"data": None, "ready": False}
input_lock = threading.Lock()

@app.route('/get-input', methods=['GET'])
def get_input():
    """Dialogue agent calls this and WAITS for user input"""
    print("[INPUT_SERVER] Agent is waiting for user input...")
    
    # Wait until input is ready (timeout after 5 minutes)
    timeout = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        with input_lock:
            if pending_input["ready"]:
                user_data = pending_input["data"]
                # Reset for next time
                pending_input["data"] = None
                pending_input["ready"] = False
                print(f"[INPUT_SERVER] Serving input to agent: {user_data[:100]}...")
                return jsonify({"input": user_data})
        
        time.sleep(0.5)  # Check every 0.5 seconds
    
    return jsonify({"input": "", "error": "timeout"}), 408

@app.route('/submit-input', methods=['POST'])
def submit_input():
    """Streamlit calls this to submit user input"""
    data = request.json
    user_input = data.get('input', '')
    
    print(f"[INPUT_SERVER] Received input from UI: {user_input[:100]}...")
    
    with input_lock:
        pending_input["data"] = user_input
        pending_input["ready"] = True
    
    return jsonify({"status": "received"})

@app.route('/status', methods=['GET'])
def status():
    """Check if agent is waiting for input"""
    with input_lock:
        return jsonify({"waiting": not pending_input["ready"]})

if __name__ == '__main__':
    print("="*60)
    print("INPUT SERVER STARTING")
    print("="*60)
    print("Run this server FIRST before running Streamlit")
    print("Server running on http://localhost:5001")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
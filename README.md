CalAi
CalAi is an AI-powered calorie estimation and food recommendation system. It can estimate calories from food images, answer general questions about meals, and provide nutritional advice. You can use CalAi in two ways:

Streamlit web interface for interactive browser-based usage.
Terminal commands for direct CLI access.
Prerequisites
Before you use CalAi (via Streamlit or terminal), you must first run the volume estimation model using a Flask API. This must be done inside a Python 3.6 virtual environment.

1. Setup Python 3.6 Virtual Environment
# Create and activate a Python 3.6 virtual environment
python3.6 -m venv calai_env
source calai_env/bin/activate
2. Install Dependencies
# Upgrade pip and install required libraries
pip install --upgrade pip
pip install -r requirements.txt
3. Add Your API Keys
Create a .env file in the project root and add your required API keys:

API_KEY=your_api_key_here
OTHER_SERVICE_KEY=your_other_service_key_here
Note: Refer to the documentation or code comments for which keys are required.

4. Start the Flask API Server
# Run the Flask API for the volume estimation model
python flask_server.py
Note: The Flask API should keep running in one terminal window while you use CalAi.

Usage
After the Flask API server is running, you can use CalAi in either of the following modes:

A. Using Streamlit (Web Interface)
Install Streamlit (if not already installed):

pip install streamlit
Run the Streamlit App:

streamlit run streamlit_app.py
Interact via your browser:

Upload food images
Ask questions
View results and recommendations directly on the web interface
B. Using Terminal Commands
Open a new terminal window (with the same Python 3.6 environment activated), and use the following command formats with router_agent.py:

Calculate calories (with image):
python router_agent.py ./session_001 "Calculate calories" food.jpg
General question (no image):
python router_agent.py ./session_001 "What should I eat for dinner?"
Auto-calculate (image without query):
python router_agent.py ./session_001 "" food.jpg
Question with image context:
python router_agent.py ./session_001 "Is this healthy?" food.jpg
Replace session_001 with your session identifier and food.jpg with the path to your food image.

Project Structure
flask_server.py – Flask API for volume estimation
router_agent.py – Main CLI entry point for calorie estimation and Q&A
ui_st.py – Streamlit web interface
requirementsagent.txt – Python dependencies
.env – Your API keys (not included, create yourself)
Notes
The Flask API must be running before you use any terminal commands or launch the Streamlit app.
All commands should be executed within the Python 3.6 virtual environment.
For image-based queries, ensure your image path is correct.
You must create a .env file and add your API keys for the application to work.
License
MIT

Contributing
Pull requests and issues are welcome! Please open an issue if you encounter any problems or have suggestions for improvement.
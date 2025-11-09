# CalAi

CalAi is an AI-powered calorie estimation and food recommendation system. It can estimate calories from food images, answer general meal-related questions, and provide nutritional advice.

CalAi can be used in two ways:

- **Streamlit web interface** for interactive browser-based usage
- **Terminal commands** for direct CLI access

---

## Prerequisites

Before using CalAi (via Streamlit or terminal), you must run the **volume estimation model** using a Flask API inside a **Python 3.6 virtual environment**.

---

## Setup

### 1. Create and Activate Python 3.6 Virtual Environment

```bash
python3.6 -m venv calai_env
source calai_env/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Add API Keys

Create a `.env` file in the project root:

```
API_KEY=your_api_key_here
OTHER_SERVICE_KEY=your_other_service_key_here
```

Refer to the documentation or code comments for required keys.

---

## Start the Flask API Server

Run the Flask API for the volume estimation model:

```bash
python flask_server.py
```

The Flask API must remain running in one terminal window while using CalAi.

---

## Usage

After starting the Flask API server, you may use CalAi through the **Streamlit interface** or **terminal commands**.

### A. Using Streamlit (Web Interface)

1. Install Streamlit:

```bash
pip install streamlit
```

2. Launch the app:

```bash
streamlit run streamlit_app.py
```

3. Interact via your browser:

- Upload food images
- Ask questions
- View results and recommendations

### B. Using Terminal Commands

In a new terminal window (with Python 3.6 environment activated), run:

#### Calculate calories (with image):

```bash
python router_agent.py ./session_001 "Calculate calories" food.jpg
```

#### General question (no image):

```bash
python router_agent.py ./session_001 "What should I eat for dinner?"
```

#### Auto-calculate (image without query):

```bash
python router_agent.py ./session_001 "" food.jpg
```

#### Question with image context:

```bash
python router_agent.py ./session_001 "Is this healthy?" food.jpg
```

Replace `session_001` with your session identifier and `food.jpg` with your image path.

---

## Project Structure

- **flask\_server.py** – Flask API for volume estimation
- **router\_agent.py** – CLI entry point for calorie estimation and Q&A
- **ui\_st.py** – Streamlit web interface
- **requirementsagent.txt** – Python dependencies
- **.env** – API keys (must be created manually)

---

## Notes

- The Flask API must be running before using any terminal commands or the Streamlit app.
- All operations must be executed inside the Python 3.6 virtual environment.
- Ensure correct paths for image-based queries.
- A `.env` file with required API keys is necessary for proper functionality.

---

## License

© Cal AI\
Give us credits if you are copying.

---

## Contributing

Pull requests and issues are welcome. Open an issue for any problems or suggestions for improvement.


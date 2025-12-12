# CalAi: AI-Powered Calorie Estimation and Food Analysis

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

CalAi is an AI-powered calorie estimation and food recommendation system that combines computer vision and natural language processing. It can estimate calories from food images, analyze nutritional content, answer meal-related questions, and provide personalized nutritional advice.

## Features

- **Food Image Analysis**: Upload food images to get instant calorie estimates
- **Volume Estimation**: Advanced 3D volume estimation using monocular vision
- **Nutritional Breakdown**: Detailed macro and micronutrient analysis
- **Conversational AI**: Ask meal-related questions and get intelligent responses
- **Multi-Modal Interface**: Use via web UI (Streamlit) or CLI (Terminal)
- **Agentic Architecture**: Modular agent-based system for flexible food analysis

## Model Backend Pipeline

The system uses a multi-agent architecture with the following pipeline:

```
User Input (Image + Query)
    ↓
[Router Agent] - Routes requests to appropriate handlers
    ↓
[Decomposer Agent] - Identifies food items in images
    ↓
[Volume Estimator] - Calculates 3D food volume (Flask API)
    ↓
[Mass Calculator] - Estimates food mass/weight
    ↓
[Nutrition Calculator] - Computes calories and macros
    ↓
[Conversational VLM] - Answers food-related questions
    ↓
Final Output (Calories, Nutrition, Recommendations)
```

## Quick Start

### Prerequisites

- Python 3.6+ (3.6 strongly recommended for volume estimation)
- pip (Python package manager)
- Flask
- Streamlit (for web interface)

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/kavyajshah240706/CalAi.git
cd CalAi
```

2. **Create and activate Python 3.6 virtual environment**:
```bash
python3.6 -m venv calai_env
source calai_env/bin/activate  # On Windows: calai_env\\Scripts\\activate
```

3. **Install dependencies**:
```bash
pip install --upgrade pip
pip install -r requirementsagents.txt
```

4. **Configure API keys**:
Create a `.env` file in the project root:
```
API_KEY=your_api_key_here
ANTHROPIC_API_KEY=your_key_here
```

5. **Start the Flask API server** (in one terminal):
```bash
python input_server.py
```

The Flask API for volume estimation must remain running while using CalAi.

## Usage

After starting the Flask API, you have two ways to use CalAi:

### Option A: Web Interface (Streamlit)

```bash
pip install streamlit
streamlit run ui_st.py
```

Then open your browser to `http://localhost:8501` and:
- Upload food images
- Ask nutritional questions
- Get personalized recommendations
- View detailed nutritional breakdowns

### Option B: Terminal/CLI

**Calculate calories from an image**:
```bash
python router_agent.py ./session_001 "Calculate calories" food.jpg
```

**Ask a general question**:
```bash
python router_agent.py ./session_001 "What should I eat for dinner?"
```

**Auto-analyze image (no explicit query)**:
```bash
python router_agent.py ./session_001 "" food.jpg
```

**Ask question about food in image**:
```bash
python router_agent.py ./session_001 "Is this healthy?" food.jpg
```

## Project Structure

```
CalAi/
├── agents/                          # Agent implementations
├── food_volume_estimation/          # 3D volume estimation models
├── models/                          # Pre-trained model weights
├── datasets/                        # Training and calibration data
├── sessions/                        # Saved session outputs
├── router_agent.py                  # CLI entry point
├─┠ agent1_decomposer.py            # Food item decomposition agent
├─┠ agent2_masscalculator.py         # Mass estimation agent
├─┠ agent3_nutritioncalculator.py   # Nutrition calculation agent
├─┠ conversational_vlm.py            # Question-answering module
├─┠ input_server.py                  # Flask API server
├─┠ ui_st.py                        # Streamlit web application
├─┠ calai.py                        # Main orchestration logic
├─┠ config.py                       # Configuration settings
├─┠ volume_verify.py                 # Volume estimation validation
├─┠ requirementsagents.txt           # Python dependencies
├─┠ Dockerfile                      # Docker containerization
├─┠ LICENSE                         # MIT License
├─┠ food_density_database.pdf       # Food density reference data
└── README.md                       # This file
```

## Configuration

### API Keys Required

- **ANTHROPIC_API_KEY**: For Claude AI (meal recommendations, Q&A)
- **Vision Model API**: For image understanding (if using third-party services)

### Environment Variables

Edit `.env` to configure:
- API endpoint URLs
- Model paths
- Temperature and token limits
- Input/output directories

## Technical Details

### Volume Estimation

The volume estimation pipeline uses:
- Monocular vision techniques for 3D reconstruction
- Reference plate scaling for size calibration
- Fine-tuned detection models for food item segmentation

### Architecture

- **Modular Agent System**: Each component (decomposition, mass calculation, nutrition) is independently testable
- **Multi-Modal Input**: Handles both images and text queries
- **Session Management**: Maintains conversation history and results

## Examples

See `sessions/` folder for sample outputs:
- Food decomposition masks
- Volume estimation JSON results
- Calorie and macro calculations

## Troubleshooting

### Flask API Won't Start
- Ensure Python 3.6 is active: `python --version`
- Check if port 5000 is available
- Verify all dependencies installed: `pip list`

### Image Analysis Fails
- Check image format (supports JPEG, PNG, BMP)
- Ensure image file path is correct
- Verify API keys are set in `.env`

### Accuracy Issues
- Place food on a known reference object (plate)
- Use images with good lighting
- Ensure food is clearly visible and not partially cropped

## Performance Notes

- First run may take longer (model loading)
- GPU acceleration recommended for faster volume estimation
- Typical analysis time: 5-15 seconds per image

## Docker Support

Build and run with Docker:
```bash
docker build -t calai .
docker run -p 5000:5000 -p 8501:8501 -e ANTHROPIC_API_KEY=your_key calai
```

## Demo

[Watch demo video](https://drive.google.com/file/d/1dxXk9k26fNdWNCox_TkqL9OqOuhFmO0W/view?usp=drive_link)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Known Limitations

- Works best with single-item meals (complex mixed dishes may be less accurate)
- Requires Python 3.6 for volume estimation module
- API key required for full feature set
- Internet connection needed for model inference

## Future Roadmap

- [ ] Support for recipe parsing
- [ ] Meal planning and dietary restriction management
- [ ] Mobile app integration
- [ ] Real-time video analysis
- [ ] Custom food database support
- [ ] Multi-language support

## Citation

If you use CalAi in your research or projects, please cite:

```bibtex
@software{calai2025,
  title = {CalAi: AI-Powered Calorie Estimation System},
  author = {Shah, Kavya J.},
  year = {2025},
  url = {https://github.com/kavyajshah240706/CalAi}
}
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support & Contact

For issues, questions, or suggestions:
- Open an [issue](https://github.com/kavyajshah240706/CalAi/issues) on GitHub
- Check existing documentation in the repository
- Review the demo video for usage examples

---

**Made with ❤️ by the CalAi Team**

# AI Data Analysis Chatbot

[![Streamlit App](https://img.shields.io/badge/Streamlit-App-brightgreen)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

**AI Data Analysis Chatbot** is a interactive web application built with [Streamlit](https://streamlit.io/) that allows users to upload CSV or Excel files and engage in conversational data analysis powered by the Mistral AI model. It supports both text and voice inputs, generates visualizations on-the-fly, and provides structured insights into your datasets. The chat interface mimics WhatsApp-style bubbles for a modern, intuitive experience.

Whether you're a data analyst, student, or business professional, this tool simplifies querying datasets with natural language—e.g., "What's the average sales by category?" or "Plot a histogram of ages."

### Key Features
- **File Upload & Data Loading**: Securely upload CSV/Excel files (up to 10MB) with automatic preview, summary (rows, columns, missing values, data types), and error handling.
- **Conversational AI**: Chat with your data using the Mistral-7B-Instruct model. Supports follow-up questions with conversation history.
- **Voice Integration**: 
  - Text-to-Speech (TTS) for bot responses (optional).
  - Speech-to-Text (STT) for voice queries via microphone.
- **WhatsApp-Style Chat**: Bubble-based UI with timestamps, auto-scroll, and theme support (Light/Dark).
- **Visualizations**: Auto-generates interactive plots (bar charts, histograms) using Plotly when requested.
- **Advanced Queries**: Basic parsing for operations like group-by aggregations.
- **User-Friendly Controls**: Send queries via Enter key or button, export chat history, clear chat, and provide feedback.
- **Responsive Design**: Wide layout with sidebar for controls, example query suggestions, and help section.

## Demo
![App Screenshot](screenshots/app-screenshot.png) *(Add a screenshot here for visual appeal)*

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <your-repo-url>
   cd ai-data-chatbot
   ```

2. **Create a Virtual Environment** (Recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   **Note**: Ensure you have `model.py` in the root directory, which loads the Mistral pipeline (e.g., via Hugging Face Transformers or a similar setup).

4. **Set Up API Keys** (if using external services):
   - For Mistral: Set your API key as an environment variable (`MISTRAL_API_KEY`).
   - For voice (pyttsx3/speech_recognition): No keys needed, but ensure microphone permissions.

## Usage

1. **Run the App**:
   ```bash
   streamlit run app.py
   ```
   The app will open in your browser at `http://localhost:8501`.

2. **Step-by-Step Workflow**:
   - **Upload Data**: Use the sidebar to upload a CSV/Excel file. View the preview and summary.
   - **Enable Voice** (Optional): Toggle in the sidebar for TTS/STT.
   - **Query Your Data**:
     - Type a question in the input field (e.g., "Show mean of sales").
     - Or click "Speak" for voice input.
     - Press **Enter** or click **Send** to analyze.
   - **Interact**: The bot responds with insights. Request plots (e.g., "Plot bar chart of categories") for visuals.
   - **Manage Chat**: Export history, clear chat, or provide feedback via buttons.

3. **Example Queries**:
   - Descriptive: "What are the top 5 values in column X?"
   - Aggregations: "Group by region and sum revenue."
   - Visual: "Histogram of prices."
   - Follow-ups: "Now filter for values above 100."

4. **Themes & Controls**:
   - Switch Light/Dark theme in the sidebar.
   - Stop speaking with the dedicated button.

## Dependencies

See `requirements.txt` for the full list. Core packages include:
- `streamlit>=1.28.0` – Web framework.
- `pandas` – Data handling.
- `plotly` – Interactive plots.
- `pyttsx3` & `speech_recognition` – Voice features.
- `transformers` or equivalent (via `model.py`) – For Mistral model.
- `openpyxl` – Excel support.

**Hardware/Software Notes**:
- Microphone for STT (tested on desktop; mobile may vary).
- Model loading requires ~8GB RAM for Mistral-7B.

## Project Structure
```
ai-data-chatbot/
├── app.py              # Main Streamlit app
├── model.py            # Mistral model loading (user-provided)
├── requirements.txt    # Dependencies
├── screenshots/        # Optional: App images
└── README.md          # This file
```

## Customization
- **Model Swap**: Edit `model.py` to use another LLM (e.g., Grok via xAI API).
- **Add Formats**: Extend file upload for JSON/SQL in the loading section.
- **Enhance Plots**: Add more Plotly chart types or integrate Altair.
- **Security**: For production, add authentication (e.g., via `streamlit-authenticator`).

## Troubleshooting
- **Model Errors**: Ensure `load_mistral_pipeline()` returns a compatible LLM object with `chat.completions.create()`.
- **Voice Issues**: Check OS audio settings; fallback to text-only by disabling in sidebar.
- **File Upload Fails**: Verify file size (<10MB) and format.
- **Enter Key Not Working**: JS may be blocked; use the Send button as fallback.
- **Session State Errors**: Clear browser cache or restart the app.

If issues persist, check the console for logs or open an issue.

## Contributing
Contributions welcome! Fork the repo, create a feature branch, and submit a PR. Focus areas:
- More query parsers (e.g., SQL-like).
- Multi-file support.
- Mobile optimizations.

1. Fork & Clone.
2. Install dev deps: `pip install -r requirements-dev.txt` *(if added)*.
3. Test: `streamlit run app.py`.
4. Commit & PR.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- [Streamlit](https://streamlit.io/) for the rapid prototyping.
- [Mistral AI](https://mistral.ai/) for the powerful LLM.
- Open-source voice libs: pyttsx3 & SpeechRecognition.

---

*Built with ❤️ for data enthusiasts. Questions? Reach out via issues.*  
*Last Updated: October 29, 2025*

import streamlit as st
from model import load_mistral_pipeline
import pandas as pd
import io
import matplotlib.pyplot as plt
import pyttsx3
import speech_recognition as sr
import threading

# --- Voice engine setup ---
engine = pyttsx3.init()
is_speaking = False

def speak_async(text):
    """Speak text asynchronously (only when enabled)."""
    global is_speaking
    if not st.session_state.get("enable_voice", False):
        return  # Only speak if enabled
    def _speak():
        global is_speaking
        is_speaking = True
        engine.say(text)
        engine.runAndWait()
        is_speaking = False
    threading.Thread(target=_speak).start()

def stop_speaking():
    """Stop current speech."""
    global is_speaking
    if is_speaking:
        engine.stop()
        is_speaking = False

def listen():
    """Listen via microphone and transcribe speech."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening... please speak now.")
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio)
        st.success(f"🗣 You said: {text}")
        return text
    except sr.UnknownValueError:
        st.error("❌ Could not understand audio.")
    except sr.RequestError:
        st.error("⚠️ Speech recognition service unavailable.")
    return None


# --- Streamlit setup ---
st.set_page_config(page_title="AI Data Chatbot", layout="wide")
st.title("🧠 AI Data Analysis Chatbot — Chat with Your CSV (Voice + Text)")

# Cache model
@st.cache_resource
def get_model():
    return load_mistral_pipeline()

llm = get_model()

# Sidebar for voice settings
st.sidebar.header("🎧 Voice Control")
st.sidebar.checkbox("🔈 Enable Voice Response", key="enable_voice")
if st.sidebar.button("⏹ Stop Speaking"):
    stop_speaking()

# File upload
uploaded_file = st.file_uploader("📁 Upload a CSV or Excel file", type=["csv", "xlsx"])

# Input area: text or voice
col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input("💭 Ask a question about your data:")
with col2:
    speak_btn = st.button("🎙 Speak")

# Handle speech input
if speak_btn:
    spoken_query = listen()
    if spoken_query:
        query = spoken_query  # replaces text input with speech


# Load dataset
if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.write("✅ Data Loaded Successfully!")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"Error reading file: {e}")
        df = None
else:
    df = None


# Handle query + model response
if st.button("🔍 Analyze"):
    if df is not None and query:
        prompt = f"""
        You are a data analysis assistant.
        A user uploaded this dataset (preview below):

        {df.head(5).to_string()}

        Question: {query}

        Provide a clear and concise answer, or relevant Python (pandas/numpy/matplotlib)
        code to answer it. Do not assume missing columns.
        """

        with st.spinner("🤖 Thinking..."):
            # Generate model response
            response = llm.chat.completions.create(
                model="mistralai/Mistral-7B-Instruct-v0.3",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7,
            )

            # Extract response
            st.markdown("### 🧩 Response:")
            try:
                message = response.choices[0].message["content"]
            except Exception:
                message = str(response)

            # Display neatly formatted
            st.markdown(f"```\n{message.strip()}\n```")

            # Speak only if enabled
            speak_async(message)

    else:
        st.warning("Please upload a dataset and ask a question first.")
# --- IGNORE ---

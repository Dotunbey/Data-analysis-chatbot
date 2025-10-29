import streamlit as st
from model import load_mistral_pipeline
import pandas as pd
import io
import matplotlib.pyplot as plt
import plotly.express as px
import pyttsx3
import speech_recognition as sr
import threading
import re
import os
from datetime import datetime

# --- Voice setup ---
engine = pyttsx3.init()
is_speaking = False

def speak_async(text):
    """Speak text asynchronously only when enabled."""
    global is_speaking
    if not st.session_state.get("enable_voice", False):
        return
    def _speak():
        global is_speaking
        is_speaking = True
        try:
            engine.say(text)
            engine.runAndWait()
        except RuntimeError:
            pass
        is_speaking = False
    threading.Thread(target=_speak, daemon=True).start()

def stop_speaking():
    """Stop current speech."""
    global is_speaking
    if is_speaking:
        engine.stop()
        is_speaking = False

def listen():
    """Listen via microphone and transcribe speech with timeout."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1)
        st.info("🎤 Listening... please speak within 10 seconds.")
        try:
            audio = r.listen(source, timeout=10, phrase_time_limit=5)
            text = r.recognize_google(audio)
            st.success(f"🗣 You said: {text}")
            return text
        except sr.WaitTimeoutError:
            st.error("❌ No speech detected within 10 seconds.")
        except sr.UnknownValueError:
            st.error("❌ Could not understand audio.")
        except sr.RequestError:
            st.error("⚠️ Speech recognition service unavailable.")
    return None

# --- Streamlit setup ---
st.set_page_config(page_title="AI Data Chatbot", layout="wide")
st.title("🧠 AI Data Analysis Chatbot — Chat with Your CSV (Voice + Text)")

# --- Theme Toggle ---
if "theme" not in st.session_state:
    st.session_state.theme = "Light"
theme_choice = st.sidebar.selectbox("🌙 Theme", ["Light", "Dark"], index=0 if st.session_state.theme == "Light" else 1, key="theme_select")
st.session_state.theme = "Dark" if theme_choice == "Dark" else "Light"

if st.session_state.theme == "Dark":
    st.markdown("""
        <style>
            .stApp { background-color: #0e1117; color: #fafafa; }
            .stTextInput > div > input { background-color: #1e1e1e; color: #fafafa; }
            .stButton > button { background-color: #262730; color: #fafafa; }
            .chat-container { 
                max-height: 500px; 
                overflow-y: auto; 
                padding: 10px; 
                border-radius: 10px; 
                margin-bottom: 20px;
                background-color: #0e1117; 
                color: #fafafa; 
            }
            .user-bubble { 
                background-color: #128c7e; 
                padding: 10px 15px; 
                border-radius: 18px 18px 5px 18px; 
                margin: 5px 50px 5px 10px; 
                float: right; 
                clear: both; 
                max-width: 70%; 
                word-wrap: break-word; 
                color: #ffffff;
            }
            .bot-bubble { 
                background-color: #2a2a2a; 
                padding: 10px 15px; 
                border-radius: 18px 18px 18px 5px; 
                margin: 5px 10px 5px 50px; 
                float: left; 
                clear: both; 
                max-width: 70%; 
                word-wrap: break-word; 
                color: #fafafa;
            }
            .timestamp { font-size: 0.8em; margin-top: 5px; color: #a0a0a0; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
            .chat-container { 
                max-height: 500px; 
                overflow-y: auto; 
                padding: 10px; 
                border-radius: 10px; 
                margin-bottom: 20px;
                background-color: #ffffff; 
                color: #000000; 
            }
            .user-bubble { 
                background-color: #dcf8c6; 
                padding: 10px 15px; 
                border-radius: 18px 18px 5px 18px; 
                margin: 5px 50px 5px 10px; 
                float: right; 
                clear: both; 
                max-width: 70%; 
                word-wrap: break-word; 
                color: #000000;
            }
            .bot-bubble { 
                background-color: #f1f1f1; 
                padding: 10px 15px; 
                border-radius: 18px 18px 18px 5px; 
                margin: 5px 10px 5px 50px; 
                float: left; 
                clear: both; 
                max-width: 70%; 
                word-wrap: break-word; 
                color: #000000;
            }
            .timestamp { font-size: 0.8em; margin-top: 5px; color: #666; }
        </style>
    """, unsafe_allow_html=True)

# --- Load model ---
@st.cache_resource(show_spinner=False)
def get_model():
    return load_mistral_pipeline()

llm = get_model()

# --- Initialize session state ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # [(role, msg, timestamp), ...]
if "last_uploaded" not in st.session_state:
    st.session_state.last_uploaded = None
if "enable_voice" not in st.session_state:
    st.session_state.enable_voice = False
if "query_input" not in st.session_state:
    st.session_state.query_input = ""
if "show_feedback_text" not in st.session_state:
    st.session_state.show_feedback_text = False

# --- Sidebar ---
st.sidebar.header("⚙️ Controls")

with st.sidebar.expander("📁 File Upload", expanded=True):
    uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    if uploaded_file and uploaded_file.size > MAX_FILE_SIZE:
        st.error("❌ File too large. Maximum size is 10MB.")
        uploaded_file = None

with st.sidebar.expander("🎧 Voice Settings"):
    st.session_state.enable_voice = st.checkbox("🔈 Enable Voice Response", value=st.session_state.enable_voice)
    if st.button("⏹ Stop Speaking"):
        stop_speaking()

# --- Upload handling ---
if uploaded_file:
    if st.session_state.last_uploaded != uploaded_file.name:
        st.session_state.chat_history = []
        st.session_state.query_input = ""
        st.success("🆕 New dataset uploaded. Chat cleared for new analysis.")
        st.session_state.last_uploaded = uploaded_file.name

# --- Dataset loading ---
df = None
if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.success("✅ Data Loaded Successfully!")
        st.dataframe(df.head())
        
        with st.expander("📊 Dataset Summary"):
            st.write(f"**Rows:** {df.shape[0]}, **Columns:** {df.shape[1]}")
            st.write("**Missing Values:**")
            st.json(df.isnull().sum().to_dict())
            st.write("**Column Types:**")
            st.json(df.dtypes.to_dict())
    except pd.errors.ParserError:
        st.error("❌ Invalid CSV format. Please ensure the file is properly formatted.")
    except ValueError as e:
        st.error(f"❌ Error reading Excel file: {e}. Try saving as CSV.")
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        df = None

# --- Query suggestions ---
if df is not None:
    st.markdown("### 💡 Example Questions")
    cols_sample = list(df.columns[:3]) if len(df.columns) >= 3 else list(df.columns)
    st.write(f"- What is the mean of {cols_sample[0]}?")
    st.write(f"- Plot a histogram of {cols_sample[1] if len(cols_sample) > 1 else cols_sample[0]}.")
    st.write("- Group by category and sum sales.")

# --- Chat Display ---
st.markdown("### 💬 Conversation")
chat_container = st.container()
with chat_container:
    for role, msg, ts in st.session_state.chat_history:
        if role == "user":
            st.markdown(f"""
                <div class="user-bubble">
                    {msg}
                    <div class="timestamp">{ts}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="bot-bubble">
                    {msg}
                    <div class="timestamp">{ts}</div>
                </div>
            """, unsafe_allow_html=True)

# Auto-scroll to bottom
st.markdown("""
    <script>
        const chatContainers = parent.document.querySelectorAll('.stContainer');
        const lastContainer = chatContainers[chatContainers.length - 1];
        if (lastContainer) {
            lastContainer.scrollTop = lastContainer.scrollHeight;
        }
    </script>
""", unsafe_allow_html=True)

# --- Input area (below chat) ---
query = st.text_input("💭 Ask a question about your data:", value=st.session_state.query_input)
col_send, col_speak = st.columns([1, 1])
send_btn = col_send.button("📤 Send")
speak_btn = col_speak.button("🎙 Speak")

# --- Handle speech input ---
if speak_btn:
    spoken_query = listen()
    if spoken_query:
        st.session_state.query_input = spoken_query
        st.rerun()

# --- Handle send ---
if send_btn:
    if df is None:
        st.warning("⚠️ Please upload a dataset first.")
        st.stop()
    if not query.strip():
        st.warning("⚠️ Please enter a valid question.")
        st.stop()
    
    # Limit history
    MAX_HISTORY = 50
    if len(st.session_state.chat_history) > MAX_HISTORY:
        st.session_state.chat_history = st.session_state.chat_history[-MAX_HISTORY:]
    
    # Add user message with timestamp
    user_ts = datetime.now().strftime("%H:%M")
    st.session_state.chat_history.append(("user", query, user_ts))
    
    # Build improved prompt
    conversation_text = "\n".join([
        f"User: {st.session_state.chat_history[i][1]}\nAssistant: {st.session_state.chat_history[i+1][1]}" 
        for i in range(0, len(st.session_state.chat_history)-1, 2)
    ])
    
    columns_str = ', '.join(df.columns)
    prompt = f"""
    You are an expert data analyst. You have access to a dataset with columns: {columns_str}.
    Preview (first 5 rows):
    {df.head(5).to_string()}

    Previous conversation:
    {conversation_text}

    Current question: {query}

    Instructions:
    - Provide a concise, accurate answer based only on the data.
    - Use pandas syntax for operations (e.g., df.groupby('category')['sales'].sum()).
    - If a visualization is requested, suggest Plotly code to generate it.
    - If unclear, ask for clarification.
    - Do not assume or invent data.
    """
    
    with st.spinner("🤖 Thinking..."):
        try:
            response = llm.chat.completions.create(
                model="mistralai/Mistral-7B-Instruct-v0.3",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7,
            )
            message = response.choices[0].message.content.strip()
        except Exception as e:
            message = f"Error: Unable to process model response. Details: {str(e)}"
            st.error(message)
    
    # Display bot response with timestamp
    bot_ts = datetime.now().strftime("%H:%M")
    st.session_state.chat_history.append(("bot", message, bot_ts))
    
    # Clear query input
    st.session_state.query_input = ""
    
    # Re-render to show new message and scroll
    st.rerun()
    
    # Generate plot if requested
    if any(word in query.lower() for word in ["plot", "chart", "graph", "histogram"]):
        try:
            if "bar" in query.lower() and "of" in query.lower():
                col_match = re.search(r'of\s+(\w+)', query.lower())
                if col_match:
                    col = col_match.group(1).title()
                    if col in df.columns:
                        fig = px.bar(df, x=col, title=f"Bar Chart of {col}")
                        st.plotly_chart(fig, use_container_width=True)
            elif "histogram" in query.lower() and "of" in query.lower():
                col_match = re.search(r'of\s+(\w+)', query.lower())
                if col_match:
                    col = col_match.group(1).title()
                    if col in df.columns:
                        fig = px.histogram(df, x=col, title=f"Histogram of {col}")
                        st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Could not generate plot: {e}")
    
    # Advanced parsing example: simple groupby
    if "group by" in query.lower():
        match = re.search(r'group by\s+(\w+)\s+and\s+(\w+)\s+(\w+)', query.lower())
        if match and df is not None:
            group_col, agg_col, agg_func = match.groups()
            if group_col in df.columns and agg_col in df.columns:
                result = df.groupby(group_col)[agg_col].agg(agg_func).reset_index()
                st.dataframe(result)
    
    # Speak response
    speak_async(message)

# --- Enter key support via JS ---
st.markdown("""
    <script>
        const input = window.parent.document.querySelector('input[placeholder*="Ask a question"]');
        if (input) {
            input.addEventListener('keypress', function(event) {
                if (event.key === 'Enter') {
                    const buttons = window.parent.document.querySelectorAll('button');
                    const sendButton = Array.from(buttons).find(btn => btn.textContent.includes('Send'));
                    if (sendButton) {
                        sendButton.click();
                    }
                }
            });
        }
    </script>
""", unsafe_allow_html=True)

# --- Utility buttons ---
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🧹 Clear Chat"):
        st.session_state.chat_history = []
        st.session_state.query_input = ""
        st.session_state.show_feedback_text = False
        st.success("Chat cleared!")
        st.rerun()
with col2:
    if st.button("💾 Export Chat"):
        chat_text = "\n".join([f"{role.capitalize()}: {msg} ({ts})" for role, msg, ts in st.session_state.chat_history])
        st.download_button("Download Chat", chat_text, "chat_history.txt", "text/plain")
with col3:
    with st.expander("📊 Feedback"):
        col_a, col_b = st.columns(2)
        if col_a.button("👍 Good"):
            st.success("Thanks! 👍")
        if col_b.button("👎 Improve"):
            st.session_state.show_feedback_text = True
            st.rerun()
        if st.session_state.show_feedback_text:
            feedback = st.text_area("Suggestions?")
            if st.button("Submit Feedback"):
                with open("feedback.txt", "a") as f:
                    f.write(f"{datetime.now()}: {feedback}\n")
                st.success("Feedback submitted!")
                st.session_state.show_feedback_text = False
                st.rerun()

# --- Help section ---
with st.expander("❓ How to Use"):
    st.markdown("""
    1. **Upload Data:** Choose a CSV or Excel file (max 10MB).
    2. **Voice Setup:** Enable voice for TTS/STT if desired.
    3. **Ask Questions:** Type or speak queries about your data. Press Enter or click Send.
    4. **Analyze:** Get insights, plots, or summaries automatically.
    5. **Chat Features:** Clear, export, or give feedback as needed.
    """)

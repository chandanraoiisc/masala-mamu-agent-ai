import streamlit as st
from datetime import datetime
import asyncio # Kept for context, even if not directly used in snippet
import re
import logging
from typing import Optional, List, Dict, Any
import json
import os

# LangChain/LangGraph imports (assuming these are from your route_agent.py)
# Make sure run_price_agent_sync is callable from here.
from route_agent import run_price_agent_sync

# Voice Input/Output imports
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO # For handling audio in memory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ------------------------- Streamlit Page Config -------------------------
st.set_page_config(
    page_title="Masala Mamu: Price Comparison AI",
    page_icon="🌶️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------- Custom CSS for Styling -------------------------
st.markdown("""
<style>
    /* Remove default Streamlit padding and margins */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        max-width: 100%;
    }
    
    /* Remove extra spacing from Streamlit elements */
    .stMarkdown {
        margin-bottom: 0.5rem;
    }
    
    /* Reduce spacing between elements */
    .element-container {
        margin-bottom: 0.5rem !important;
    }
    
    /* Remove extra spacing from containers */
    .css-1d391kg {
        padding-top: 0.5rem;
    }
    
    /* Compact the container wrapper */
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.5rem;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 8px 12px;
        margin-bottom: 8px;
        border-radius: 15px;
        display: block;
        font-size: 0.9em;
        line-height: 1.4;
        max-width: 85%;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        word-wrap: break-word;
    }
    
    .chat-message.user {
        background-color: #e3f2fd;
        color: #1565c0;
        margin-left: auto;
        margin-right: 0;
        text-align: right;
        border-bottom-right-radius: 3px;
    }
    
    .chat-message.assistant {
        background-color: #f3e5f5;
        color: #4a148c;
        margin-right: auto;
        margin-left: 0;
        border-bottom-left-radius: 3px;
    }
    
    .message-header {
        font-size: 0.75em;
        opacity: 0.7;
        margin-bottom: 4px;
    }
    
    .message-content {
        margin: 0;
    }
    
    .message-content p {
        margin: 0 0 0.5em 0;
    }
    
    /* Product card styling - more compact */
    .product-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 10px;
        margin: 8px 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        border-left: 3px solid #4caf50;
        font-size: 0.85em;
    }
    
    .product-title {
        font-weight: bold;
        color: #1976d2;
        margin-bottom: 4px;
        font-size: 1em;
    }
    
    .product-offer {
        margin: 2px 0;
        font-size: 0.9em;
    }
    
    .product-cheapest {
        color: #2e7d32;
        font-weight: bold;
    }
    
    .product-expensive {
        color: #f57c00;
    }
    
    .product-savings {
        color: #1976d2;
        font-style: italic;
    }
    
    /* Chat container - dynamic height */
    .chat-container {
        max-height: 60vh;
        overflow-y: auto;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 10px;
        background-color: #fafafa;
        margin-bottom: 1rem;
    }
    
    /* When empty, make it very compact */
    .chat-container.empty {
        min-height: auto;
        padding: 15px;
    }
    
    /* Input section styling */
    .input-section {
        background-color: #f5f5f5;
        border-radius: 8px;
        padding: 10px;
        margin-top: 10px;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #1976d2;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.4rem 0.8rem;
        font-weight: 500;
        transition: all 0.2s;
        width: 100%;
    }
    
    .stButton > button:hover {
        background-color: #1565c0;
        transform: translateY(-1px);
    }
    
    /* Listening indicator */
    .listening-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 8px;
        background-color: #fff3e0;
        border-radius: 6px;
        margin: 8px 0;
        font-size: 0.85em;
        color: #ef6c00;
        animation: pulse 1.5s infinite;
    }
    
    /* Loading animation */
    .loading-dots span {
        display: inline-block;
        width: 4px;
        height: 4px;
        background-color: #ef6c00;
        border-radius: 50%;
        margin: 0 1px;
        animation: bounce 1.4s infinite ease-in-out both;
    }
    
    .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
    .loading-dots span:nth-child(2) { animation-delay: -0.16s; }
    .loading-dots span:nth-child(3) { animation-delay: 0s; }

    @keyframes bounce {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1.0); }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.02); opacity: 0.9; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    /* Audio player styling */
    .stAudio {
        margin: 5px 0;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        padding-top: 1rem;
    }
    
    /* Hide Streamlit default elements that create spacing */
    .css-1y4p8pa {
        padding: 0;
    }
    
    /* Reduce spacing in columns */
    .css-ocqkz7 {
        gap: 0.5rem;
    }
    
    /* Title and header adjustments */
    h1 {
        margin-bottom: 1rem !important;
        color: #d32f2f;
    }
    
    /* Remove extra spacing from containers */
    .block-container {
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------- Session State Initialization -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "listening" not in st.session_state:
    st.session_state.listening = False

if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("GOOGLE_API_KEY", "")

if "enable_tts" not in st.session_state:
    st.session_state.enable_tts = True

if "input_content" not in st.session_state:
    st.session_state.input_content = ""

if "input_key" not in st.session_state:
    st.session_state.input_key = "input_0"

# ------------------------- Speech Engine Setup -------------------------
@st.cache_resource
def init_speech_engines():
    """Initializes speech recognition and sets up TTS availability."""
    try:
        recognizer = sr.Recognizer()
        logger.info("SpeechRecognizer initialized.")
        return recognizer, True
    except Exception as e:
        logger.error(f"Speech engine initialization error: {str(e)}")
        st.error(f"Speech engine initialization error: {str(e)}. Check microphone setup.")
        return None, False

recognizer, tts_available = init_speech_engines()

# ------------------------- Helper Functions -------------------------
def speech_to_text() -> Optional[str]:
    """Convert speech to text using microphone"""
    if not recognizer:
        st.error("Speech recognition not available.")
        return None

    try:
        with sr.Microphone() as source:
            st.info("🎤 Listening... Speak now!")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

        st.info("🔄 Processing speech...")
        return recognizer.recognize_google(audio)
    except sr.WaitTimeoutError:
        st.warning("⏰ No speech detected. Please try again.")
        logger.warning("Speech recognition timed out.")
    except sr.UnknownValueError:
        st.warning("🤷 Could not understand the speech.")
        logger.warning("Speech recognition could not understand audio.")
    except sr.RequestError as e:
        st.error(f"❌ Speech recognition service error: {str(e)}")
        logger.error(f"Speech recognition service error: {e}", exc_info=True)
    except Exception as e:
        st.error(f"❌ Unexpected error during speech recognition: {str(e)}")
        logger.error(f"Unexpected error during speech recognition: {e}", exc_info=True)
    return None

def text_to_speech(text: str) -> Optional[bytes]:
    """Convert text to speech using gTTS and return audio bytes for Streamlit"""
    if not st.session_state.enable_tts or not tts_available:
        logger.info("Text-to-Speech is disabled or not available.")
        return None
    try:
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = re.sub(r'\*\*(.+?)\*\*', r'\1', clean_text)
        clean_text = re.sub(r'\*(.+?)\*', r'\1', clean_text)

        tts = gTTS(text=clean_text, lang='en', slow=False)
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        logger.info("Text converted to speech (gTTS).")
        return audio_fp.read()
    except Exception as e:
        logger.error(f"gTTS Error: {str(e)}", exc_info=True)
        st.error(f"🔊 Text-to-Speech failed: {str(e)}")
        return None

def parse_structured_response(response_str: str) -> Dict[str, Any]:
    """Parse JSON response or return as plain text"""
    logger.info(f"Attempting to parse response: {response_str[:100]}...")
    try:
        data = json.loads(response_str)
        if isinstance(data, dict) and "products" in data and "summary" in data:
            logger.info("Parsed response as structured product data.")
            return data
    except json.JSONDecodeError:
        logger.info("Response is not JSON, treating as plain text.")
        pass
    return {"summary": response_str, "products": []}

def render_message_content(message: Dict[str, Any]):
    """Render chat message with proper styling"""
    role_class = "user" if message["role"] == "user" else "assistant"
    timestamp = message.get("timestamp", datetime.now().strftime("%H:%M:%S"))

    # Create message HTML
    message_html = f'<div class="chat-message {role_class}">'
    
    # Add timestamp header
    if message["role"] == "assistant":
        message_html += f'<div class="message-header">🌶️ Masala Mamu • {timestamp}</div>'
    else:
        message_html += f'<div class="message-header">You • {timestamp}</div>'

    message_html += '<div class="message-content">'

    if message["role"] == "assistant":
        parsed_response = parse_structured_response(message["content"])

        if parsed_response["products"]:
            # Display summary
            message_html += f"<p>{parsed_response['summary']}</p>"
            
            # Display products in a more compact way
            for product in parsed_response["products"]:
                message_html += f'<div class="product-card">'
                message_html += f'<div class="product-title">{product["brand"]} - {product["name"]}</div>'

                if product["offers"]:
                    sorted_offers = sorted(product["offers"], 
                                         key=lambda x: float(re.sub(r'[^\d.]', '', x["price"])) 
                                         if re.sub(r'[^\d.]', '', x["price"]) else float('inf'))
                    
                    cheapest = sorted_offers[0]
                    most_expensive = sorted_offers[-1] if len(sorted_offers) > 1 else None

                    message_html += f'<div class="product-offer product-cheapest">💚 Best: {cheapest["price"]} on {cheapest["platform"]}</div>'

                    if most_expensive and most_expensive != cheapest:
                        message_html += f'<div class="product-offer product-expensive">💸 Highest: {most_expensive["price"]} on {most_expensive["platform"]}</div>'
                        
                        try:
                            savings = (float(re.sub(r'[^\d.]', '', most_expensive["price"])) -
                                     float(re.sub(r'[^\d.]', '', cheapest["price"])))
                            if savings > 0:
                                message_html += f'<div class="product-offer product-savings">💡 Save ₹{savings:.0f} with {cheapest["platform"]}</div>'
                        except ValueError:
                            pass

                    # Show all prices in compact format
                    for offer in sorted_offers:
                        message_html += f'<div class="product-offer">• {offer["platform"]}: {offer["price"]}</div>'
                else:
                    message_html += '<div class="product-offer">❌ No offers found</div>'
                message_html += '</div>'
        else:
            message_html += f"<p>{parsed_response['summary']}</p>"
    else:
        message_html += f"<p>{message['content']}</p>"

    message_html += '</div></div>'
    
    st.markdown(message_html, unsafe_allow_html=True)

    # Add audio if available
    if "audio" in message and message["audio"]:
        st.audio(message["audio"], format='audio/mp3')

def get_chatbot_response(user_question: str) -> str:
    """Gets response from the Masala Mamu agent."""
    if not st.session_state.api_key:
        return "Please enter your Google API Key in the sidebar settings."

    try:
        logger.info(f"Calling Masala Mamu agent with: {user_question}")
        response = run_price_agent_sync(user_question, st.session_state.api_key)
        logger.info(f"Agent response received (first 100 chars): {response[:100]}...")
        return response
    except Exception as e:
        logger.error(f"Error calling agent: {e}", exc_info=True)
        return f"An error occurred while getting a response: {str(e)}"

# ------------------------- Streamlit UI Layout -------------------------

# Sidebar
with st.sidebar:
    st.title("🌶️ Settings")
    st.session_state.api_key = st.text_input(
        "Google API Key",
        value=st.session_state.api_key,
        type="password",
        help="Get your key from Google AI Studio"
    )
    
    st.markdown("---")
    st.checkbox(
        "🔊 Enable Text-to-Speech",
        value=st.session_state.enable_tts,
        key="enable_tts"
    )

# Main interface
st.title("🌶️ Masala Mamu: Price Comparison AI")
st.markdown("*Your personal shopping assistant for comparing grocery prices across India*")

# Chat display - more compact
with st.container():
    # Add dynamic class based on whether there are messages
    container_class = "chat-container empty" if not st.session_state.messages else "chat-container"
    st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.markdown("""
        <div class="chat-message assistant" style="max-width: 100%; margin: 0;">
            <div class="message-header">🌶️ Masala Mamu</div>
            <div class="message-content">
                <p>Hello! I can help you compare prices of groceries and household items across various platforms in India.</p>
                <p>Try asking: <strong>"What is the price of eggs?"</strong> or <strong>"Compare prices for Surf Excel detergent"</strong></p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for message in st.session_state.messages:
            render_message_content(message)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Input section - more compact layout
col1, col2 = st.columns([4, 1])

with col1:
    user_query = st.text_input(
        "Ask Masala Mamu...",
        placeholder="e.g., Price of eggs, Cheapest milk?",
        key=st.session_state.input_key,  # Use dynamic key to force refresh
        label_visibility="collapsed"
    )

with col2:
    ask_clicked = st.button("🔍 Ask", use_container_width=True)

# Voice input in a separate compact section
with st.expander("🎤 Voice Input", expanded=False):
    col_voice1, col_voice2 = st.columns(2)
    
    with col_voice1:
        voice_clicked = st.button("🎙️ Start Voice", use_container_width=True)
    
    with col_voice2:
        if st.session_state.listening:
            st.markdown('<div class="listening-indicator">🎤 Listening... <div class="loading-dots"><span></span><span></span><span></span></div></div>', unsafe_allow_html=True)
        else:
            st.info("💡 Click to use voice input")

# Handle user input
if ask_clicked and user_query:
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.messages.append({
        "role": "user",
        "content": user_query,
        "timestamp": timestamp
    })
    
    # Clear input by changing the key to create a new widget
    current_key_num = int(st.session_state.input_key.split("_")[1])
    st.session_state.input_key = f"input_{current_key_num + 1}"
    
    with st.spinner("🤔 Thinking..."):
        response = get_chatbot_response(user_query)

    if response:
        audio_bytes = text_to_speech(response)
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "audio": audio_bytes
        })
    
    # Force rerun to clear the input and show new messages
    st.rerun()

# Handle voice input
if voice_clicked:
    if not st.session_state.listening:
        st.session_state.listening = True
        recognized_text = speech_to_text()
        st.session_state.listening = False

        if recognized_text:
            st.success(f"✅ Recognized: {recognized_text}")
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.messages.append({
                "role": "user",
                "content": recognized_text,
                "timestamp": timestamp
            })

            # Clear input field for voice input too
            current_key_num = int(st.session_state.input_key.split("_")[1])
            st.session_state.input_key = f"input_{current_key_num + 1}"

            with st.spinner("🤔 Thinking..."):
                response = get_chatbot_response(recognized_text)

            if response:
                audio_bytes = text_to_speech(response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "audio": audio_bytes
                })
            st.rerun()
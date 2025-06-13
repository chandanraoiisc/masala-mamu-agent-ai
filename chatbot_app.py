import streamlit as st
from datetime import datetime
import asyncio
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
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ------------------------- Streamlit Page Config -------------------------
st.set_page_config(
    page_title="Masala Mamu: AI Kitchen Assistant",
    page_icon="🌶️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------- Custom CSS for World-Class UI -------------------------
st.markdown("""
<style>
body, .stApp {
    background: #f7f8fa;
    font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
}
.chat-container {
    max-width: 700px;
    margin: 0 auto;
    padding-bottom: 120px;
}
.chat-message {
    display: flex;
    flex-direction: column;
    margin-bottom: 1.5rem;
    border-radius: 1.2rem;
    padding: 1.1rem 1.4rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    position: relative;
    animation: fadeIn 0.5s;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
.user-message {
    align-self: flex-end;
    background: linear-gradient(90deg, #e3f2fd 60%, #bbdefb 100%);
    border-top-right-radius: 0.2rem;
    border-bottom-right-radius: 1.2rem;
    border-bottom-left-radius: 1.2rem;
    border-top-left-radius: 1.2rem;
    color: #222;
    box-shadow: 0 2px 8px rgba(33,150,243,0.07);
}
.bot-message {
    align-self: flex-start;
    background: linear-gradient(90deg, #fff 60%, #e8f5e9 100%);
    border-top-left-radius: 0.2rem;
    border-bottom-right-radius: 1.2rem;
    border-bottom-left-radius: 1.2rem;
    border-top-right-radius: 1.2rem;
    color: #222;
    box-shadow: 0 2px 8px rgba(76,175,80,0.07);
}
.message-header {
    font-size: 0.95rem;
    color: #888;
    margin-bottom: 0.3rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.message-content {
    font-size: 1.13rem;
    line-height: 1.7;
    word-break: break-word;
}
/* Removed .main-title as we'll use inline styles for the main title/subtitle */
.avatar {
    width: 2.2rem;
    height: 2.2rem;
    border-radius: 50%;
    margin-right: 0.7rem;
    object-fit: cover;
    border: 2px solid #fff;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
.input-bar {
    position: fixed;
    left: 0; right: 0; bottom: 0;
    background: #fff;
    box-shadow: 0 -2px 16px rgba(0,0,0,0.07);
    padding: 1.1rem 0.7rem 1.1rem 0.7rem;
    z-index: 100;
    display: flex;
    justify-content: center;
    align-items: flex-end;
}
.input-inner {
    width: 100%;
    max-width: 700px;
    display: flex;
    gap: 0.7rem;
    align-items: flex-end;
}
.input-textarea {
    width: 100%;
    min-height: 2.5rem;
    max-height: 6rem;
    border-radius: 1.2rem;
    border: 1.5px solid #e0e0e0;
    padding: 0.9rem 1.2rem;
    font-size: 1.1rem;
    resize: none;
    background: #f7f8fa;
    outline: none;
    transition: border 0.2s;
}
.input-textarea:focus {
    border: 1.5px solid #2196f3;
    background: #fff;
}
.ask-btn {
    background: linear-gradient(90deg, #2196f3 60%, #21cbf3 100%);
    color: #fff;
    border: none;
    border-radius: 1.2rem;
    padding: 0.8rem 1.7rem;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(33,150,243,0.09);
    transition: background 0.2s;
}
.ask-btn:hover {
    background: linear-gradient(90deg, #1976d2 60%, #00bcd4 100%);
}
.voice-btn {
    background: #fff3e0;
    color: #ff9800;
    border: none;
    border-radius: 50%;
    width: 3.2rem;
    height: 3.2rem;
    font-size: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(255,152,0,0.09);
    margin-left: 0.3rem;
    transition: background 0.2s, color 0.2s;
}
.voice-btn.listening {
    background: #ff9800;
    color: #fff;
    animation: pulse 1.2s infinite;
}
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(255,152,0,0.3); }
    70% { box-shadow: 0 0 0 10px rgba(255,152,0,0.05); }
    100% { box-shadow: 0 0 0 0 rgba(255,152,0,0.0); }
}
.clear-btn {
    background: #fff;
    color: #e53935;
    border: 1.5px solid #e53935;
    border-radius: 1.2rem;
    padding: 0.5rem 1.2rem;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    margin-left: 0.7rem;
    margin-bottom: 0.5rem;
    transition: background 0.2s, color 0.2s;
}
.clear-btn:hover {
    background: #e53935;
    color: #fff;
}
.scroll-bottom-btn {
    position: fixed;
    right: 2.5rem;
    bottom: 7.5rem;
    background: #2196f3;
    color: #fff;
    border: none;
    border-radius: 50%;
    width: 2.7rem;
    height: 2.7rem;
    font-size: 1.3rem;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(33,150,243,0.13);
    z-index: 200;
    cursor: pointer;
    transition: background 0.2s;
}
.scroll-bottom-btn:hover {
    background: #1976d2;
}
.product-card {
    border: 1px solid #e0e0e0;
    border-radius: 0.8rem;
    padding: 0.8rem;
    margin-top: 0.7rem;
    background-color: #fcfcfc;
    box-shadow: 0 1px 6px rgba(0,0,0,0.03);
}
.product-title {
    font-weight: 600;
    font-size: 1.05rem;
    margin-bottom: 0.5rem;
    color: #333;
}
.product-offer {
    font-size: 0.95rem;
    color: #555;
    margin-bottom: 0.2rem;
    display: flex;
    align-items: center;
}
.product-cheapest {
    font-weight: 600;
    color: #28a745; /* Green for best price */
}
.product-expensive {
    color: #dc3545; /* Red for highest price */
}
.product-savings {
    font-weight: 600;
    color: #17a2b8; /* Info blue for savings */
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
    st.session_state.input_key = "input_1"

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
        # In a real app, you might hide voice features if unavailable
        return None, False

recognizer, tts_available = init_speech_engines()

# ------------------------- Helper Functions -------------------------
def speech_to_text() -> Optional[str]:
    """Convert speech to text using microphone"""
    if not recognizer:
        st.error("Speech recognition not available. Check microphone setup.")
        return None

    try:
        with sr.Microphone() as source:
            st.session_state.listening = True # Set listening state before starting to listen
            st.toast("🎤 Listening... Speak now!")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

        st.toast("🔄 Processing speech...")
        st.session_state.listening = False # Reset listening state after audio capture
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
    finally:
        st.session_state.listening = False # Ensure listening state is reset even on error
    return None

def text_to_speech(text: str) -> Optional[bytes]:
    """Convert text to speech using gTTS and return audio bytes for Streamlit"""
    if not st.session_state.enable_tts or not tts_available:
        logger.info("Text-to-Speech is disabled or not available.")
        return None
    try:
        # Remove markdown formatting for TTS
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
    role_class = "user-message" if message["role"] == "user" else "bot-message"
    timestamp = message.get("timestamp", datetime.now().strftime("%H:%M:%S"))
    avatar = "https://i.imgur.com/8Km9tLL.png" if message["role"] == "user" else "https://i.imgur.com/1X4rC7F.png"

    # Create message HTML
    message_html = f'<div class="chat-message {role_class}">'
    
    # Add timestamp header
    message_html += f'<div class="message-header"><img src="{avatar}" class="avatar">' \
                    f'{"You" if message["role"] == "user" else "🌶️ Masala Mamu"} • {timestamp}</div>'

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

def process_user_input(user_input: str):
    """Processes user input, gets response, and updates session state."""
    if not user_input.strip():
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.messages.append({
        "role": "user",
        "content": user_input.strip(),
        "timestamp": timestamp
    })

    # Clear the input box by changing its key
    current_key_num = int(st.session_state.input_key.split("_")[1])
    st.session_state.input_key = f"input_{current_key_num + 1}"
    st.session_state.input_content = "" # Clear the content as well

    with st.spinner("🤔 Thinking..."):
        response = get_chatbot_response(user_input.strip())
    
    if response:
        audio_bytes = text_to_speech(response)
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "audio": audio_bytes
        })
    st.rerun()

# ------------------------- Streamlit UI Layout -------------------------

# Sidebar
with st.sidebar:
    st.title("🌶️ Masala Mamu Settings")
    st.session_state.api_key = st.text_input(
        "Google API Key",
        value=st.session_state.api_key,
        type="password",
        help="Get your key from Google AI Studio"
    )
    
    st.markdown("---")
    st.session_state.enable_tts = st.checkbox(
        "🔊 Enable Text-to-Speech",
        value=st.session_state.enable_tts
    )
    if st.button("🧹 Clear Chat", key="clear_chat_btn"):
        st.session_state.messages = []
        st.session_state.input_key = "input_1" # Reset input key on clear
        st.session_state.input_content = ""
        st.rerun()

# Main interface
# Using inline style for direct control over text color
st.markdown('<h1 style="color: #212121;">🌶️ Masala Mamu: AI Kitchen Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #212121;"><i>Your personal shopping assistant for comparing grocery prices across India</i></p>', unsafe_allow_html=True)

# Chat display
with st.container():
    # Add dynamic class based on whether there are messages
    container_class = "chat-container empty" if not st.session_state.messages else "chat-container"
    st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.markdown("""
        <div class="chat-message bot-message" style="max-width: 100%; margin: 0;">
            <div class="message-header"><img src="https://i.imgur.com/1X4rC7F.png" class="avatar">🌶️ Masala Mamu</div>
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

# Scroll to bottom button (remains unchanged)
if st.session_state.messages:
    st.markdown('''<script>window.scrollTo(0, document.body.scrollHeight);</script>''', unsafe_allow_html=True)

# Fixed input bar at the bottom
st.markdown('<div class="input-bar">', unsafe_allow_html=True)
col_input, col_voice_btn, col_ask_btn = st.columns([8, 1, 2])

with col_input:
    # Use st.session_state.input_content to manage the text area content
    user_query_input = st.text_area(
        "Type your message...",
        value=st.session_state.input_content,
        key=st.session_state.input_key, # Key changes to reset the input
        label_visibility="collapsed",
        height=70,
        max_chars=500,
        placeholder="Ask about prices, deals, or say hi!"
    )
    # Update input_content state when text area changes
    if user_query_input != st.session_state.input_content:
        st.session_state.input_content = user_query_input

with col_voice_btn:
    # Add a class for visual feedback when listening
    # To apply dynamic class to the button, you'd typically need a custom component or JS.
    # For a simple visual feedback, we can use a text indicator next to the button.
    voice_clicked = st.button("🎤", key="voice_btn_fixed", help="Voice Input", use_container_width=True)

with col_ask_btn:
    ask_clicked = st.button("Ask", key="ask_btn_fixed", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# Add a listening indicator next to the voice button if active
if st.session_state.listening:
    st.markdown("""
    <div style="
        position: fixed;
        bottom: 8.5rem; /* Adjust based on your input bar height */
        right: 15rem; /* Adjust to position next to the voice button */
        background-color: #fff3e0;
        color: #ff9800;
        padding: 0.5rem 1rem;
        border-radius: 1.2rem;
        font-size: 0.9rem;
        box-shadow: 0 2px 8px rgba(255,152,0,0.09);
        z-index: 101;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    ">
        🎤 Listening...
        <div class="loading-dots"><span></span><span></span><span></span></div>
    </div>
    <style>
    .loading-dots {
        display: flex;
        align-items: center;
    }
    .loading-dots span {
        animation: blink 1.4s infinite;
        font-size: 1.5rem;
        line-height: 1;
        opacity: 0;
    }
    .loading-dots span:nth-child(2) {
        animation-delay: 0.2s;
    }
    .loading-dots span:nth-child(3) {
        animation-delay: 0.4s;
    }
    @keyframes blink {
        0% { opacity: 0; }
        50% { opacity: 1; }
        100% { opacity: 0; }
    }
    </style>
    """, unsafe_allow_html=True)


# --- Input Handling Logic (Combined) ---
# This ensures that both text input (Ask button/Enter) and voice input are handled in a single flow.

# Handle text input (Ask button or Enter key)
if (ask_clicked or (user_query_input and st.session_state.get('enter_pressed', False))) and user_query_input.strip():
    # Reset enter_pressed flag immediately to prevent multiple triggers
    if 'enter_pressed' in st.session_state:
        st.session_state.enter_pressed = False
    process_user_input(user_query_input)

# Handle voice input
if voice_clicked and not st.session_state.listening: # Prevent re-triggering if already listening
    # To make the listening effect visible, we need to rerun immediately after setting listening=True
    st.session_state.listening = True
    st.rerun() # Rerun to show the listening state visually
elif voice_clicked and st.session_state.listening:
    # If the button is clicked again while listening, stop listening (optional, depends on UX)
    st.session_state.listening = False
    st.rerun()
elif st.session_state.listening: # This block executes after the rerun triggered above
    recognized_text = speech_to_text()
    if recognized_text:
        process_user_input(recognized_text)


# Enter key triggers Ask (for desktop) - remains the same
st.markdown('''<script>
document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey && document.activeElement.tagName === 'TEXTAREA') {
        window.parent.postMessage({isEnterPressed: true}, '*');
    }
});
window.addEventListener('message', function(event) {
    if (event.data && event.data.isEnterPressed) {
        // Only set the value if it's not already true to avoid unnecessary reruns
        if (!window.parent.streamlitReport.state.getComponentValue('enter_pressed')) {
            window.parent.streamlitSend({type: 'streamlit:setComponentValue', key: 'enter_pressed', value: true});
        }
    }
});
</script>''', unsafe_allow_html=True)

# Initialize enter_pressed in session state if not present to avoid KeyError on first load
if 'enter_pressed' not in st.session_state:
    st.session_state.enter_pressed = False
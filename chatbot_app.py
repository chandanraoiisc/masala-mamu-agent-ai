import streamlit as st
from datetime import datetime
import asyncio
import re
import logging
from typing import Optional, List, Dict, Any
import json
import os

import auto_install_playwright

# LangChain/LangGraph imports
from route_agent import run_price_agent_sync

# Voice Input/Output imports
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO
import base64

# New import for client-side audio recording
from streamlit_audiorecorder import st_audiorecorder

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
/* Adjust voice-btn styling to match st_audiorecorder */
.stAudioRecorder button {
    background: #fff3e0 !important;
    color: #ff9800 !important;
    border: none !important;
    border-radius: 50% !important;
    width: 3.2rem !important;
    height: 3.2rem !important;
    font-size: 1.5rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 2px 8px rgba(255,152,0,0.09) !important;
    margin-left: 0.3rem !important;
    transition: background 0.2s, color 0.2s !important;
}
.stAudioRecorder button:hover {
    background: #ff9800 !important;
    color: #fff !important;
}
.stAudioRecorder button.active { /* Class added by st_audiorecorder when recording */
    background: #ff9800 !important;
    color: #fff !important;
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
    color: #28a745;
}
.product-expensive {
    color: #dc3545;
}
.product-savings {
    font-weight: 600;
    color: #17a2b8;
}

/* Safari-specific audio player styling */
.safari-audio-player {
    width: 100%;
    max-width: 300px;
    margin: 10px 0;
    border-radius: 8px;
    background: #f5f5f5;
}

.play-audio-btn {
    background: linear-gradient(90deg, #4caf50 60%, #66bb6a 100%);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 14px;
    cursor: pointer;
    margin: 5px 0;
    transition: background 0.2s;
}

.play-audio-btn:hover {
    background: linear_gradient(90deg, #388e3c 60%, #4caf50 100%);
}
</style>
""", unsafe_allow_html=True)

# ------------------------- Session State Initialization -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# No longer needed, as st_audiorecorder manages its own state
# if "listening" not in st.session_state:
#     st.session_state.listening = False

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
    """Initializes speech recognition. PyAudio is still needed by speech_recognition for processing audio data, not just live mic."""
    try:
        recognizer = sr.Recognizer()
        logger.info("SpeechRecognizer initialized.")
        return recognizer, True # True indicates gTTS is generally available
    except Exception as e:
        logger.error(f"Speech engine initialization error: {str(e)}")
        return None, False

recognizer, tts_available = init_speech_engines()

# ------------------------- Helper Functions -------------------------
# `speech_to_text` function is now replaced by direct processing of `wav_audio_data`
# from st_audiorecorder. Remove or refactor if you need to use `sr.Microphone` locally.
# def speech_to_text() -> Optional[str]:
#     """Convert speech to text using microphone - NOT FOR STREAMLIT CLOUD"""
#     # ... (original code, but this won't work on cloud)
#     return None


def text_to_speech_safari_compatible(text: str) -> Optional[Dict[str, Any]]:
    """
    Convert text to speech with Safari compatibility.
    Returns both audio bytes and base64 encoded data for different rendering methods.
    """
    if not st.session_state.enable_tts or not tts_available:
        logger.info("Text-to-Speech is disabled or not available.")
        return None
    
    try:
        # First, try to parse the structured response to extract just the summary
        parsed_response = parse_structured_response(text)
        
        # If we have a structured response with a summary, use that
        if parsed_response and "summary" in parsed_response and parsed_response["summary"]:
            clean_text = parsed_response["summary"]
            logger.info(f"Using extracted summary for TTS: {clean_text[:100]}...")
        else:
            # Fallback to cleaning the entire text
            clean_text = text
            logger.info("No structured summary found, using full text for TTS")
        
        # Clean text for TTS (remove markdown, HTML, etc.)
        clean_text = re.sub(r'<[^>]+>', '', clean_text)
        clean_text = re.sub(r'\*\*(.+?)\*\*', r'\1', clean_text)
        clean_text = re.sub(r'\*(.+?)\*', r'\1', clean_text)
        clean_text = re.sub(r'[{}]', '', clean_text)  # Remove JSON formatting
        clean_text = re.sub(r'`json.*?`', '', clean_text, flags=re.DOTALL)  # Remove JSON code blocks
        clean_text = re.sub(r'```.*?```', '', clean_text, flags=re.DOTALL)  # Remove code blocks
        clean_text = clean_text.strip()
        
        # Limit text length for better performance
        if len(clean_text) > 500:
            clean_text = clean_text[:500] + "..."
        
        # Skip TTS if text is too short or empty
        if len(clean_text.strip()) < 10:
            logger.info("Text too short for TTS, skipping")
            return None
        
        tts = gTTS(text=clean_text, lang='en', slow=False)
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        
        audio_bytes = audio_fp.read()
        
        # Create base64 encoded version for Safari compatibility
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        logger.info(f"Text converted to speech with Safari compatibility. Clean text: {clean_text[:100]}...")
        
        return {
            "audio_bytes": audio_bytes,
            "audio_base64": audio_base64,
            "clean_text": clean_text
        }
        
    except Exception as e:
        logger.error(f"gTTS Error: {str(e)}", exc_info=True)
        st.error(f"🔊 Text-to-Speech failed: {str(e)}")
        return None

def create_safari_audio_player(audio_data: Dict[str, Any]) -> str:
    """Create Safari-compatible audio player HTML"""
    audio_base64 = audio_data["audio_base64"]
    clean_text = audio_data["clean_text"]
    
    # Create a unique ID for this audio player
    import uuid
    player_id = f"audio_player_{uuid.uuid4().hex[:8]}"
    
    html = f"""
    <div class="safari-audio-player">
        <audio id="{player_id}" preload="none" controls style="width: 100%; max-width: 300px;">
            <source src="data:audio/mpeg;base64,{audio_base64}" type="audio/mpeg">
            Your browser does not support the audio element.
        </audio>
        <br>
        <button class="play-audio-btn" onclick="playAudioSafari('{player_id}')">
            🔊 Play Audio (Safari Compatible)
        </button>
    </div>
    
    <script>
    function playAudioSafari(playerId) {{
        const audio = document.getElementById(playerId);
        if (audio) {{
            // For Safari: ensure user interaction triggers the play
            audio.load(); // Reload the audio element
            const playPromise = audio.play();
            
            if (playPromise !== undefined) {{
                playPromise.then(() => {{
                    console.log('Audio started playing successfully');
                }}).catch(error => {{
                    console.log('Audio play failed:', error);
                    // Fallback: try to play again after a brief delay
                    setTimeout(() => {{
                        audio.play().catch(e => console.log('Retry failed:', e));
                    }}, 100);
                }});
            }}
        }}
    }}
    
    // Additional Safari-specific initialization
    document.addEventListener('DOMContentLoaded', function() {{
        const audio = document.getElementById('{player_id}');
        if (audio) {{
            // Enable audio playback on Safari by setting volume
            audio.volume = 0.8;
            
            // Add event listeners for debugging
            audio.addEventListener('loadstart', () => console.log('Audio load started'));
            audio.addEventListener('canplay', () => console.log('Audio can play'));
            audio.addEventListener('error', (e) => console.log('Audio error:', e));
        }}
    }});
    </script>
    """
    
    return html

def parse_structured_response(response_str: str) -> dict:
    """Extract and parse JSON from the response string, including additional text."""
    import re, json
    
    # First, remove the JSON code block completely from the response
    # This handles ```json{...}``` patterns
    response_cleaned = re.sub(r'```json\s*\{[\s\S]*?\}\s*```', '', response_str, flags=re.MULTILINE)
    
    # Also remove standalone JSON blocks without markdown
    json_match = re.search(r'\{[\s\S]*?\}', response_str)
    
    structured_data = None
    if json_match:
        json_str = json_match.group(0)
        try:
            data = json.loads(json_str)
            if isinstance(data, dict) and "products" in data and "summary" in data:
                structured_data = data
                # Remove the JSON from the cleaned response as well
                response_cleaned = re.sub(re.escape(json_str), '', response_cleaned)
        except Exception as e:
            print(f"JSON parsing error: {e}")
    
    # Clean up extra whitespace and newlines
    response_cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', response_cleaned)
    response_cleaned = response_cleaned.strip()
    
    if structured_data:
        return {
            "summary": response_cleaned,
            "products": structured_data.get("products", []),
            "has_structured_data": True,
            "json_summary": structured_data.get("summary", "")
        }
    else:
        # If no valid JSON found, return entire cleaned response as summary
        return {
            "summary": response_cleaned, 
            "products": [], 
            "has_structured_data": False
        }

def render_message_content(message: Dict[str, Any]):
    """Render chat message with proper styling and Safari-compatible audio"""
    role_class = "user-message" if message["role"] == "user" else "bot-message"
    timestamp = message.get("timestamp", datetime.now().strftime("%H:%M:%S"))
    avatar = "https://i.imgur.com/8Km9tLL.png" if message["role"] == "user" else "https://i.imgur.com/1X4rC7F.png"

    message_html = f'<div class="chat-message {role_class}">'
    message_html += f'<div class="message-header"><img src="{avatar}" class="avatar">' \
                    f'{"You" if message["role"] == "user" else "🌶️ Masala Mamu"} • {timestamp}</div>'
    message_html += '<div class="message-content">'

    if message["role"] == "assistant":
        parsed = parse_structured_response(message["content"])
        
        if parsed.get("has_structured_data") and parsed.get("products"):
            # Display the complete summary (JSON structure removed, only readable text)
            summary_text = parsed['summary']
            
            # Convert markdown-like formatting to HTML
            summary_text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', summary_text)
            summary_text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', summary_text)
            summary_text = re.sub(r'🔥 \*\*BEST VALUE:\*\*', r'🔥 <strong>BEST VALUE:</strong>', summary_text)
            summary_text = re.sub(r'💡 \*\*Shopping Tips:\*\*', r'💡 <strong>Shopping Tips:</strong>', summary_text)
            
            # Convert bullet points to HTML lists
            lines = summary_text.split('\n')
            processed_lines = []
            in_list = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('* ') or line.startswith('- '):
                    if not in_list:
                        processed_lines.append('<ul>')
                        in_list = True
                    processed_lines.append(f'<li>{line[4:].strip()}</li>')
                else:
                    if in_list:
                        processed_lines.append('</ul>')
                        in_list = False
                    if line:
                        processed_lines.append(f'<p>{line}</p>')
            
            if in_list:
                processed_lines.append('</ul>')
            
            formatted_summary = ''.join(processed_lines)
            message_html += formatted_summary
            
            # Render product tables
            for product in parsed["products"]:
                message_html += f'<div class="product-card">'
                message_html += f'<div class="product-title">{product.get("brand", "")} - {product["name"]}</div>'
                message_html += '<table style="width: 100%; border-collapse: collapse; margin-top: 8px;">'
                message_html += '<tr style="background-color: #f5f5f5;"><th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Retailer</th><th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Price</th></tr>'
                
                for offer in product["offers"]:
                    quantity = offer.get('quantity', '')
                    quantity_text = f" ({quantity})" if quantity else ""
                    message_html += f'<tr><td style="padding: 8px; border: 1px solid #ddd;">{offer["platform"]}</td><td style="padding: 8px; border: 1px solid #ddd;">{offer["price"]}{quantity_text}</td></tr>'
                
                message_html += '</table></div>'
        else:
            # No structured data, render as plain text with basic formatting
            content = parsed['summary']
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
            content = content.replace('\n', '<br>')
            message_html += f"<p>{content}</p>"
    else:
        # User message
        content = message["content"].replace('\n', '<br>')
        message_html += f"<p>{content}</p>"

    message_html += '</div></div>'
    st.markdown(message_html, unsafe_allow_html=True)
    
    # Handle audio with Safari compatibility
    if "audio_data" in message and message["audio_data"]:
        # Use Safari-compatible audio player
        safari_player_html = create_safari_audio_player(message["audio_data"])
        st.markdown(safari_player_html, unsafe_allow_html=True)
    elif "audio" in message and message["audio"]:
        # Fallback to standard Streamlit audio (though audio_data should be preferred)
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
    st.session_state.input_content = ""

    with st.spinner("🤔 Thinking..."):
        response = get_chatbot_response(user_input.strip())
    
    if response:
        audio_data = None
        if st.session_state.enable_tts:
            audio_data = text_to_speech_safari_compatible(response)
        
        logger.info(f"Response received: {response}")
        logger.info(f"Audio data generated: {audio_data is not None}")
        
        message_data = {
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        
        if audio_data:
            message_data["audio_data"] = audio_data
            # Keep legacy audio for backward compatibility
            message_data["audio"] = audio_data["audio_bytes"]
            
        st.session_state.messages.append(message_data)
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
    
    # Add Safari compatibility info
    st.info("💡 **Safari Users**: If audio doesn't auto-play, click the 'Play Audio' button or use the audio controls.")
    
    if st.button("🧹 Clear Chat", key="clear_chat_btn"):
        st.session_state.messages = []
        st.session_state.input_key = "input_1"
        st.session_state.input_content = ""
        st.rerun()

# Main interface
st.markdown('<h1 style="color: #212121;">🌶️ Masala Mamu: AI Kitchen Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #212121;"><i>Your personal shopping assistant for comparing grocery prices across India</i></p>', unsafe_allow_html=True)

# Chat display
with st.container():
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

# Scroll to bottom
if st.session_state.messages:
    st.markdown('''<script>window.scrollTo(0, document.body.scrollHeight);</script>''', unsafe_allow_html=True)

# Fixed input bar at the bottom
st.markdown('<div class="input-bar">', unsafe_allow_html=True)
col_input, col_voice_btn, col_ask_btn = st.columns([8, 1, 2])

with col_input:
    user_query_input = st.text_area(
        "Type your message...",
        value=st.session_state.input_content,
        key=st.session_state.input_key,
        label_visibility="collapsed",
        height=70,
        max_chars=500,
        placeholder="Ask about prices, deals, or say hi!"
    )
    if user_query_input != st.session_state.input_content:
        st.session_state.input_content = user_query_input

with col_voice_btn:
    # Use the st_audiorecorder component here
    # wav_audio_data will be None initially, then bytes when recording stops.
    wav_audio_data = st_audiorecorder(
        start_prompt="", # Text on the button when recording is not active
        stop_prompt="",  # Text on the button when recording is active
        # The key ensures the component persists state correctly
        key="voice_recorder_widget",
        # Pass custom CSS classes to align styling with your existing buttons
        # You'll need to define `.stAudioRecorder button` in your CSS
        # and potentially `.stAudioRecorder button.active` for the pulse effect.
    )

with col_ask_btn:
    ask_clicked = st.button("Ask", key="ask_btn_fixed", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# Removed the custom listening indicator as st_audiorecorder handles it

# Input Handling Logic
# Process text input
if (ask_clicked or (user_query_input and st.session_state.get('enter_pressed', False))) and user_query_input.strip():
    if 'enter_pressed' in st.session_state:
        st.session_state.enter_pressed = False
    process_user_input(user_query_input)

# Process audio input from st_audiorecorder
if wav_audio_data is not None:
    st.toast("🔄 Processing audio...")
    try:
        r = recognizer # Use the cached recognizer
        audio_file = BytesIO(wav_audio_data)
        with sr.AudioFile(audio_file) as source:
            audio = r.record(source) # Read the entire audio file

        recognized_text = r.recognize_google(audio) # Or another recognizer like recognize_whisper
        if recognized_text:
            process_user_input(recognized_text)
        else:
            st.warning("🤷 Could not understand the speech. Please try again.")

    except sr.UnknownValueError:
        st.warning("🤷 Could not understand the speech.")
        logger.warning("Speech recognition could not understand audio from recorded data.")
    except sr.RequestError as e:
        st.error(f"❌ Speech recognition service error: {str(e)}")
        logger.error(f"Speech recognition service error for recorded audio: {e}", exc_info=True)
    except Exception as e:
        st.error(f"❌ Unexpected error during audio processing: {str(e)}")
        logger.error(f"Unexpected error during audio processing from recorder: {e}", exc_info=True)


# Enter key handling
st.markdown('''<script>
document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey && document.activeElement.tagName === 'TEXTAREA') {
        window.parent.postMessage({isEnterPressed: true}, '*');
    }
});
window.addEventListener('message', function(event) {
    if (event.data && event.data.isEnterPressed) {
        if (!window.parent.streamlitReport.state.getComponentValue('enter_pressed')) {
            window.parent.streamlitSend({type: 'streamlit:setComponentValue', key: 'enter_pressed', value: true});
        }
    }
});
</script>''', unsafe_allow_html=True)

if 'enter_pressed' not in st.session_state:
    st.session_state.enter_pressed = False
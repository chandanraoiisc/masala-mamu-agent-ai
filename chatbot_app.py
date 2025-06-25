import streamlit as st
from datetime import datetime
import asyncio
import re
import logging
from typing import Optional, List, Dict, Any
import json
import os
import sys
import requests
import time

# Import nutrition dashboard integration
from nutrition_dashboard import render_nutrition_dashboard_page

# Voice Input/Output imports
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO
import base64

# Configure logging - enhanced for debugging
logging.basicConfig(
    level=logging.INFO,  # Changed to DEBUG level for more detailed logs
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(stream=sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
logger.info("Application starting with enhanced logging")

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
}

/* Better markdown rendering styles */
.stMarkdown {
    line-height: 1.6;
}

.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
    color: #333;
}

.stMarkdown p {
    margin-bottom: 1rem;
}

.stMarkdown ul, .stMarkdown ol {
    margin-left: 1rem;
    margin-bottom: 1rem;
}

.stMarkdown li {
    margin-bottom: 0.25rem;
}

.stMarkdown code {
    background-color: #f1f3f4;
    padding: 0.2rem 0.4rem;
    border-radius: 0.3rem;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
}

.stMarkdown pre {
    background-color: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 0.5rem;
    padding: 1rem;
    overflow-x: auto;
    margin-bottom: 1rem;
}

.stMarkdown blockquote {
    border-left: 4px solid #2196f3;
    padding-left: 1rem;
    margin: 1rem 0;
    color: #666;
    font-style: italic;
}

/* Typing animation */
.typing-indicator {
    display: inline-block;
    animation: blink 1.5s infinite;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}
</style>
""", unsafe_allow_html=True)

def check_api_health():
    """Checks if the API is accessible and returns health status."""
    try:
        # Extract the base URL from the query endpoint
        base_url = st.session_state.api_url.rsplit('/', 1)[0]
        health_url = f"{base_url}/health"

        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            return True, health_data
        else:
            return False, {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        logger.error(f"API health check failed: {str(e)}")
        return False, {"status": "unreachable", "error": str(e)}

# ------------------------- Session State Initialization -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "listening" not in st.session_state:
    st.session_state.listening = False

if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("API_KEY", "")

if "api_url" not in st.session_state:
    st.session_state.api_url = os.getenv("AGENTIC_FLOW_API_URL", "http://localhost:8000/query")

if "enable_tts" not in st.session_state:
    st.session_state.enable_tts = True

if "user_id" not in st.session_state:
    st.session_state.user_id = "anonymous"

if "input_content" not in st.session_state:
    st.session_state.input_content = ""

if "input_key" not in st.session_state:
    st.session_state.input_key = "input_1"

if "streaming_response" not in st.session_state:
    st.session_state.streaming_response = ""

if "is_streaming" not in st.session_state:
    st.session_state.is_streaming = False

if "stream_complete" not in st.session_state:
    st.session_state.stream_complete = False

# ------------------------- Speech Engine Setup -------------------------
@st.cache_resource
def init_speech_engines():
    """Initializes speech recognition and sets up TTS availability."""
    try:
        recognizer = sr.Recognizer()
        tts_available = True
    except Exception as e:
        logger.error(f"Speech engine initialization error: {e}")
        recognizer = None
        tts_available = False
    return recognizer, tts_available

recognizer, tts_available = init_speech_engines()

def recognize_speech():
    """Uses the microphone to capture speech and convert it to text."""
    if not recognizer:
        return "Speech recognition is not available."

    try:
        with sr.Microphone() as source:
            st.session_state.listening = True
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5)
        st.session_state.listening = False

        # Attempt to recognize the speech
        try:
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "I couldn't understand what you said."
        except sr.RequestError as e:
            return f"Speech recognition service error: {e}"

    except Exception as e:
        st.session_state.listening = False
        logger.error(f"Speech recognition error: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"

def text_to_speech_safari_compatible(text: str) -> Optional[Dict[str, Any]]:
    """Converts text to speech, with special handling for Safari browser."""
    if not st.session_state.enable_tts or not tts_available:
        return None

    try:
        # Clean text for TTS
        clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove Markdown bold
        clean_text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', clean_text)  # Remove Markdown links
        clean_text = re.sub(r'```.*?```', '', clean_text, flags=re.DOTALL)  # Remove code blocks
        clean_text = re.sub(r'#+ ', '', clean_text)  # Remove Markdown headings
        clean_text = re.sub(r'\n\s*\n', '\n', clean_text)  # Compress newlines
        clean_text = clean_text.strip()

        # Limit TTS to reasonable length
        if len(clean_text) > 3000:
            logger.info(f"TTS text too long ({len(clean_text)} chars), truncating...")
            clean_text = clean_text[:3000] + "..."

        # Generate audio
        tts = gTTS(text=clean_text, lang='en', slow=False)

        # Save to BytesIO buffer instead of file
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)  # Go to start of the BytesIO buffer

        # Get the audio data as bytes
        audio_bytes = audio_buffer.getvalue()

        # Convert to base64 for Safari compatibility
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

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

    # Log the input received for parsing
    logger.info(f"Parsing response, length: {len(response_str)}")
    logger.debug(f"Response preview for parsing: {response_str[:100]}...")

    # First, remove the JSON code block completely from the response
    # This handles ```json{...}``` patterns
    response_cleaned = re.sub(r'```json\s*\{[\s\S]*?\}\s*```', '', response_str, flags=re.MULTILINE)

    # Also remove standalone JSON blocks without markdown
    json_match = re.search(r'\{[\s\S]*?\}', response_str)

    structured_data = None
    if json_match:
        logger.info("Found potential JSON data in response")
        json_str = json_match.group(0)
        try:
            data = json.loads(json_str)
            if isinstance(data, dict) and "products" in data and "summary" in data:
                structured_data = data
                logger.info(f"Parsed structured data with {len(data.get('products', []))} products")
                # Remove the JSON from the cleaned response as well
                response_cleaned = re.sub(re.escape(json_str), '', response_cleaned)
        except Exception as e:
            logger.error(f"JSON parsing error: {e}")
            print(f"JSON parsing error: {e}")

    # Clean up extra whitespace and newlines
    response_cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', response_cleaned)
    response_cleaned = response_cleaned.strip()

    # Log the cleaned response
    logger.info(f"Cleaned response length: {len(response_cleaned)}")
    logger.debug(f"Cleaned response preview: {response_cleaned[:100]}...")

    if structured_data:
        logger.info("Returning structured data and summary")
        return {
            "summary": response_cleaned,
            "structured_data": structured_data
        }
    else:
        logger.info("Returning only summary without structured data")
        return {
            "summary": response_cleaned,
            "structured_data": None
        }

def render_message_bubble(message: dict, is_streaming: bool = False):
    """Renders a single message bubble with advanced formatting and proper markdown support."""
    # Log the message being rendered
    logger.info(f"Rendering message bubble: role={message.get('role')}, content_length={len(message.get('content', ''))}, streaming={is_streaming}")
    logger.debug(f"Message content preview: {message.get('content', '')[:100]}...")

    is_user = message["role"] == "user"
    bubble_class = "user-message" if is_user else "bot-message"
    avatar_img = "https://avatars.githubusercontent.com/u/151195195?v=4" if is_user else "https://i.ibb.co/9Vz3Ncx/masalamamu.jpg"

    # Header with avatar and timestamp
    header_name = "You" if is_user else "Masala Mamu"
    timestamp = message.get("timestamp", "")

    # Create a container for the message
    with st.container():
        # Message header
        col1, col2 = st.columns([1, 10])
        with col1:
            st.image(avatar_img, width=40)
        with col2:
            st.caption(f"**{header_name}** • {timestamp}")

        # Message content with proper styling
        message_container = st.container()
        with message_container:
            if is_user:
                # User message - simple text with user styling
                st.markdown(f"""
                <div style="
                    background: linear-gradient(90deg, #e3f2fd 60%, #bbdefb 100%);
                    padding: 1rem 1.2rem;
                    border-radius: 1rem 1rem 0.2rem 1rem;
                    margin: 0.5rem 0;
                    box-shadow: 0 2px 8px rgba(33,150,243,0.07);
                ">
                    {message['content'].replace('\n', '<br>')}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Assistant message - render as markdown with bot styling
                content = message["content"]

                # Parse structured data if present
                parsed_data = parse_structured_response(content)
                content_to_render = parsed_data["summary"]

                # Create styled container for bot message
                st.markdown(f"""
                <div style="
                    background: linear-gradient(90deg, #fff 60%, #e8f5e9 100%);
                    padding: 1rem 1.2rem;
                    border-radius: 1rem 1rem 1rem 0.2rem;
                    margin: 0.5rem 0;
                    box-shadow: 0 2px 8px rgba(76,175,80,0.07);
                    border-left: 3px solid #4caf50;
                ">
                """, unsafe_allow_html=True)

                # Render content as proper markdown
                if is_streaming or message.get("is_placeholder"):
                    # Show streaming indicator with HTML for placeholder
                    if message.get("is_placeholder"):
                        st.markdown(content_to_render, unsafe_allow_html=True)
                    else:
                        st.markdown(content_to_render + " <span class='typing-indicator'>⏳</span>", unsafe_allow_html=True)
                else:
                    st.markdown(content_to_render, unsafe_allow_html=False)

                st.markdown("</div>", unsafe_allow_html=True)

                # Handle structured data if present
                if parsed_data["structured_data"] and "products" in parsed_data["structured_data"]:
                    products = parsed_data["structured_data"]["products"]
                    st.info(f"Found {len(products)} products in comparison")

    # Handle audio with Safari compatibility
    if not is_streaming and "audio_data" in message and message["audio_data"]:
        # Use Safari-compatible audio player
        safari_player_html = create_safari_audio_player(message["audio_data"])
        st.markdown(safari_player_html, unsafe_allow_html=True)
    elif not is_streaming and "audio" in message and message["audio"]:
        # Fallback to standard Streamlit audio
        st.audio(message["audio"], format='audio/mp3')

def get_chatbot_response(user_question: str) -> str:
    """Gets response from the Masala Mamu agent through the API."""
    if not st.session_state.api_key:
        return "Please enter your API Key in the sidebar settings."

    try:
        logger.info(f"Calling Masala Mamu agent API with: {user_question}")

        # Get the API URL from session state
        api_url = st.session_state.api_url

        # Prepare the request payload
        payload = {
            "query": user_question
        }

        # Add API key to headers if needed
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {st.session_state.api_key}"
        }

        # Make the API request
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=3600  # Adjust timeout as needed
        )

        # Check if the request was successful
        response.raise_for_status()

        # Parse the JSON response
        result = response.json()

        # Extract the relevant response content from the result
        if "response" in result:
            response_text = result["response"]
        else:
            # In case the API returns a different structure
            response_text = str(result)

        logger.info(f"Agent API response received (first 100 chars): {response_text[:100]}...")
        return response_text
    except requests.RequestException as e:
        logger.error(f"API request error: {e}", exc_info=True)
        return f"An error occurred while connecting to the agent API: {str(e)}"
    except Exception as e:
        logger.error(f"Error processing agent response: {e}", exc_info=True)
        return f"An error occurred while processing the response: {str(e)}"

def process_user_input(user_input: str):
    """Processes user input, gets response, and updates session state with streaming."""
    logger.info(f"Processing user input: '{user_input[:50]}...'")

    if not user_input.strip():
        logger.info("Empty input, returning without processing")
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    user_message = {
        "role": "user",
        "content": user_input.strip(),
        "timestamp": timestamp
    }
    logger.info(f"Adding user message to session state, content length: {len(user_input.strip())}")
    st.session_state.messages.append(user_message)
    logger.info(f"Session state now has {len(st.session_state.messages)} messages")

    # Clear the input box by changing its key
    current_key_num = int(st.session_state.input_key.split("_")[1])
    st.session_state.input_key = f"input_{current_key_num + 1}"
    st.session_state.input_content = ""
    logger.info("Input box cleared")

    # Initialize streaming state
    st.session_state.is_streaming = True
    st.session_state.streaming_response = ""
    st.session_state.stream_complete = False

    # Add placeholder message for streaming
    placeholder_message = {
        "role": "assistant",
        "content": "🤔 Masala Mamu is thinking<span class='typing-indicator'>...</span>",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "is_placeholder": True
    }
    st.session_state.messages.append(placeholder_message)

    # Force rerun to show placeholder
    st.rerun()

def stream_response():
    """Handle streaming response from API"""
    if not st.session_state.is_streaming:
        return

    # Get the last user message
    user_messages = [msg for msg in st.session_state.messages if msg["role"] == "user"]
    if not user_messages:
        return

    last_user_input = user_messages[-1]["content"]

    logger.info("Calling chatbot API for response...")

    # Show spinner while getting response
    with st.spinner("🤔 Masala Mamu is thinking..."):
        response = get_chatbot_response(last_user_input)

    if response:
        logger.info(f"Response received from API, length: {len(response)}")

        # Remove placeholder message
        st.session_state.messages = [msg for msg in st.session_state.messages if not msg.get("is_placeholder")]

        # Add the complete response
        audio_data = None
        if st.session_state.enable_tts:
            logger.info("TTS enabled, generating audio")
            with st.spinner("🔊 Generating audio..."):
                audio_data = text_to_speech_safari_compatible(response)

        message_data = {
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }

        if audio_data:
            logger.info("Adding audio data to message")
            message_data["audio_data"] = audio_data
            message_data["audio"] = audio_data["audio_bytes"]

        st.session_state.messages.append(message_data)

        # Complete streaming
        st.session_state.is_streaming = False
        st.session_state.stream_complete = True

        logger.info("Response processing complete")

        # Force a rerun to show the complete response
        st.rerun()
    else:
        logger.warning("No response received from API")
        # Remove placeholder and add error message
        st.session_state.messages = [msg for msg in st.session_state.messages if not msg.get("is_placeholder")]
        error_message = {
            "role": "assistant",
            "content": "Sorry, I couldn't get a response. Please try again.",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        st.session_state.messages.append(error_message)
        st.session_state.is_streaming = False
        st.rerun()

def handle_image_upload(uploaded_file):
    """Process the uploaded image with OCR using the backend inventory service."""
    try:
        # Save uploaded file to a temp location
        file_path = f"temp_uploads/{uploaded_file.name}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.sidebar.success(f"Received image: {uploaded_file.name}")

        # Process the image using the backend OCR API
        ocr_api_url = st.session_state.api_url.replace("/query", "/bill")

        # Prepare the file for upload
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}

        # Show processing status
        with st.sidebar:
            with st.spinner("Processing image with OCR..."):
                try:
                    response = requests.post(ocr_api_url, files=files, timeout=30)

                    if response.status_code == 200:
                        result = response.json()
                        items = result.get("items", [])

                        if items:
                            st.success(f"✅ Successfully processed {len(items)} items from the image!")

                            # Display processed items
                            st.markdown("**Processed Items:**")
                            for item in items:
                                st.markdown(f"• {item}")

                            # Add a message to the chat about the processed image
                            image_message = {
                                "role": "assistant",
                                "content": f"I've successfully processed your image and found {len(items)} items:\n\n" +
                                          "\n".join([f"• {item}" for item in items]) +
                                          "\n\nThese items have been added to your inventory. You can now ask me about recipes, nutrition information, or shopping suggestions based on these items!",
                                "timestamp": datetime.now().strftime("%H:%M:%S")
                            }
                            st.session_state.messages.append(image_message)
                        else:
                            st.warning("No items were detected in the image. Please try with a clearer image of grocery items or receipts.")
                    else:
                        st.error(f"Failed to process image: {response.status_code} - {response.text}")

                except requests.exceptions.Timeout:
                    st.error("Request timeout. The OCR processing took too long. Please try again.")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the backend API. Please ensure the backend is running.")
                except Exception as api_error:
                    st.error(f"API error: {str(api_error)}")

    except Exception as e:
        st.sidebar.error(f"Error processing image: {str(e)}")
        logger.error(f"Image upload error: {str(e)}", exc_info=True)

# Sidebar
with st.sidebar:
    st.title("🌶️ Masala Mamu Settings")

    # Add page navigation
    st.markdown("### Navigation")
    page = st.radio("Go to:", ["Chat Assistant", "Nutrition Dashboard"])

    st.markdown("---")
    st.markdown("### Settings")
    st.session_state.api_key = st.text_input(
        "API Key",
        value=st.session_state.api_key,
        type="password",
        help="API Key for authentication"
    )

    # Add API URL configuration
    if "api_url" not in st.session_state:
        st.session_state.api_url = "http://localhost:8000/query"

    st.session_state.api_url = st.text_input(
        "Agentic Flow API URL",
        value=st.session_state.api_url,
        help="URL for the agentic-flow API endpoint (e.g., http://localhost:8000/query)"
    )

    # Add API health check button
    if st.button("Check API Connection"):
        with st.spinner("Checking API connection..."):
            is_healthy, health_data = check_api_health()

        if is_healthy:
            st.success(f"✅ API is healthy: {health_data.get('status', 'connected')}")
            if 'azure_openai' in health_data:
                st.info(f"LLM Status: {health_data['azure_openai']}")
        else:
            st.error(f"❌ API is not accessible: {health_data.get('error', 'Unknown error')}")
            st.info("Make sure the agentic-flow app is running and the URL is correct.")

    st.markdown("---")
    st.markdown("### Receipt/Grocery Upload")
    uploaded_file = st.file_uploader("Upload receipt or grocery image", type=["jpg", "jpeg", "png"])
    if st.button("Process Image"):
        if uploaded_file is not None:
            handle_image_upload(uploaded_file)
        else:
            st.sidebar.warning("Please upload an image first.")

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

# Page routing
if page == "Nutrition Dashboard":
    render_nutrition_dashboard_page()
else:
    # Main chat interface
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; margin-bottom: 1.5rem;'>🌶️ Masala Mamu: AI Kitchen Assistant</h1>", unsafe_allow_html=True)

    # Welcome message if no messages
    logger.info(f"Starting UI render with {len(st.session_state.messages)} messages in session state")

    if len(st.session_state.messages) == 0:
        logger.info("No messages in session state, adding welcome message")
        welcome_msg = {
            "role": "assistant",
            "content": "👋 Hello! I'm Masala Mamu, your AI kitchen assistant. How can I help you today? Ask me about:\n\n"
                      "🍽️ Recipe ideas\n"
                      "🛒 Grocery prices & comparisons\n"
                      "🥗 Nutrition advice\n"
                      "🧾 Receipt analysis\n\n"
                      "Try saying: *'What's a good quick dinner I can make with chicken and vegetables?'* or *'Where can I find the best price for organic milk?'*",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }

        # Add audio to welcome message if TTS is enabled
        if st.session_state.enable_tts:
            logger.info("TTS enabled, generating audio for welcome message")
            audio_data = text_to_speech_safari_compatible(welcome_msg["content"])
            if audio_data:
                welcome_msg["audio_data"] = audio_data
                welcome_msg["audio"] = audio_data["audio_bytes"]
                logger.info("Audio added to welcome message")

        logger.info("Adding welcome message to session state")
        st.session_state.messages.append(welcome_msg)
        logger.info("Welcome message added")

    # Display chat messages
    logger.info(f"Rendering {len(st.session_state.messages)} messages from session state")

    # Handle streaming response if needed
    if st.session_state.is_streaming and not st.session_state.stream_complete:
        stream_response()

    for i, message in enumerate(st.session_state.messages):
        logger.info(f"Rendering message {i+1}/{len(st.session_state.messages)}, role: {message.get('role')}")
        is_streaming = message.get("is_placeholder", False) or (st.session_state.is_streaming and i == len(st.session_state.messages) - 1)
        render_message_bubble(message, is_streaming=is_streaming)

    logger.info("All messages rendered")

    # Add a div for auto-scrolling
    st.markdown('<div id="chat_end"></div>', unsafe_allow_html=True)

    # Input area - fixed at bottom using custom CSS
    st.markdown('<div class="input-bar">', unsafe_allow_html=True)
    st.markdown('<div class="input-inner">', unsafe_allow_html=True)

    # Add JavaScript for handling Enter key press and Cmd+Enter
    st.markdown('''<script>
document.addEventListener('DOMContentLoaded', function() {
    let retryCount = 0;
    const maxRetries = 10;

    function setupEnterKeyHandler() {
        const textareas = document.querySelectorAll('textarea[placeholder*="Ask about prices"]');

        if (textareas.length === 0 && retryCount < maxRetries) {
            retryCount++;
            setTimeout(setupEnterKeyHandler, 200);
            return;
        }

        textareas.forEach(function(textarea) {
            textarea.removeEventListener('keydown', handleKeyDown);
            textarea.addEventListener('keydown', handleKeyDown);
        });
    }

    function handleKeyDown(e) {
        if ((e.key === 'Enter' && !e.shiftKey) || (e.key === 'Enter' && (e.metaKey || e.ctrlKey))) {
            e.preventDefault();

            const buttons = document.querySelectorAll('button');
            let askButton = null;

            for (let button of buttons) {
                if (button.innerText.includes('Ask') ||
                    button.getAttribute('data-testid')?.includes('ask') ||
                    button.className?.includes('ask')) {
                    askButton = button;
                    break;
                }
            }

            if (askButton) {
                askButton.click();
            } else {
                const submitButtons = Array.from(buttons).filter(btn =>
                    btn.innerText.trim() === 'Ask' ||
                    btn.type === 'submit' ||
                    btn.getAttribute('kind') === 'primary'
                );
                if (submitButtons.length > 0) {
                    submitButtons[0].click();
                }
            }
        }
    }

    setupEnterKeyHandler();

    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length > 0) {
                setTimeout(setupEnterKeyHandler, 100);
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});
</script>''', unsafe_allow_html=True)

    if 'enter_pressed' not in st.session_state:
        st.session_state.enter_pressed = False

    # Create columns for input layout
    cols = st.columns([10, 1, 2])

    # Input in first column
    user_query_input = cols[0].text_area(
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

    # Voice button in second column
    voice_clicked = cols[1].button("🎤", key="voice_btn_fixed", help="Voice Input", use_container_width=True)

    # Ask button in third column
    ask_clicked = cols[2].button("Ask", key="ask_btn_fixed", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Listening indicator
    if st.session_state.listening:
        st.markdown("""
        <div style="
            position: fixed;
            bottom: 8.5rem;
            right: 15rem;
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
            height: 5px;
            width: 5px;
            margin: 0 2px;
            border-radius: 50%;
            background-color: #ff9800;
            display: inline-block;
            opacity: 0.6;
        }
        .loading-dots span:nth-child(2) {
            animation-delay: 0.2s;
        }
        .loading-dots span:nth-child(3) {
            animation-delay: 0.4s;
        }
        @keyframes blink {
            0% { transform: scale(0.8); opacity: 0.3; }
            50% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(0.8); opacity: 0.3; }
        }
        </style>
        """, unsafe_allow_html=True)

    # Handle voice input button click
    if voice_clicked:
        if recognizer:
            with st.spinner("🎤 Listening..."):
                speech_text = recognize_speech()
            if speech_text and speech_text != "I couldn't understand what you said." and not speech_text.startswith("Error:"):
                st.session_state.input_content = speech_text
                process_user_input(speech_text)
            elif speech_text:  # Show any error or couldn't understand messages
                st.info(f"🎤 {speech_text}")
        else:
            st.error("🎤 Speech recognition is not available. Check console for details.")

    # Handle submit button click
    if ask_clicked:
        logger.info("Ask button clicked")
        if st.session_state.input_content.strip():
            logger.info(f"Processing input: '{st.session_state.input_content[:50]}...'")
            process_user_input(st.session_state.input_content)
        else:
            logger.warning("Ask button clicked but input is empty")

    # Add JavaScript for auto-scroll
    st.markdown("""
    <script>
        function scrollToBottom() {
            const chatEnd = document.getElementById('chat_end');
            if (chatEnd) {
                chatEnd.scrollIntoView();
            }
        }

        // Set a timeout to ensure this runs after the page is fully loaded
        setTimeout(function() {
            scrollToBottom();
        }, 500);
    </script>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

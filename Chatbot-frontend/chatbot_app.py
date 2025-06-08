import streamlit as st
import speech_recognition as sr
import pyttsx3
from io import BytesIO
import tempfile
import os
import time
from datetime import datetime

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "listening" not in st.session_state:
    st.session_state.listening = False

# Configure page
st.set_page_config(
    page_title="Masala Mamu Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
    .timestamp {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.5rem;
    }
    .stButton > button {
        width: 100%;
    }
    .listening-indicator {
        background-color: #ff5722;
        color: white;
        padding: 0.5rem;
        border-radius: 0.25rem;
        text-align: center;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("🤖 Masala Mamu : Agentic AI Kitchen Assistant")
st.markdown("Chat with the AI using text or speech input!")

# Initialize speech recognition and text-to-speech
@st.cache_resource
def init_speech_engines():
    recognizer = sr.Recognizer()
    tts_engine = pyttsx3.init()
    
    # Configure TTS settings
    voices = tts_engine.getProperty('voices')
    if voices:
        tts_engine.setProperty('voice', voices[0].id)
    tts_engine.setProperty('rate', 150)
    tts_engine.setProperty('volume', 0.8)
    
    return recognizer, tts_engine

recognizer, tts_engine = init_speech_engines()

# Sidebar for settings
st.sidebar.header("⚙️ Settings")

# Voice settings
st.sidebar.subheader("🔊 Voice Settings")
enable_tts = st.sidebar.checkbox("Enable Text-to-Speech", value=True)
speech_rate = st.sidebar.slider("Speech Rate", 50, 300, 150)
speech_volume = st.sidebar.slider("Speech Volume", 0.0, 1.0, 0.8)

# Update TTS settings
tts_engine.setProperty('rate', speech_rate)
tts_engine.setProperty('volume', speech_volume)

# Chat history toggle
show_timestamps = st.sidebar.checkbox("Show Timestamps", value=True)

# Clear chat button
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

# Function to simulate chatbot response 
# This is a placeholder for actual chatbot logic. 
# We can replace this with a call to an AI model or API.
# We need to revisit this once we have a proper AI model or API to integrate.
def get_chatbot_response(user_input):

    responses = [
        f"I understand you said: '{user_input}'. How can I help you further?",
        f"That's interesting! You mentioned: '{user_input}'. Tell me more.",
        f"Thanks for sharing: '{user_input}'. What else would you like to discuss?",
        "I'm here to help! What specific information are you looking for?",
        "That's a great question! Let me think about that.",
    ]
    
    import random
    time.sleep(1)  # Simulate processing time
    return random.choice(responses)

# Function to convert text to speech
def text_to_speech(text):
    if enable_tts:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tts_engine.save_to_file(text, tmp_file.name)
                tts_engine.runAndWait()
                
                with open(tmp_file.name, 'rb') as audio_file:
                    audio_bytes = audio_file.read()
                
                os.unlink(tmp_file.name)
                return audio_bytes
        except Exception as e:
            st.error(f"TTS Error: {str(e)}")
    return None

# Function to recognize speech from microphone
def speech_to_text():
    try:
        with sr.Microphone() as source:
            st.info("🎤 Listening... Speak now!")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
        st.info("🔄 Processing speech...")
        text = recognizer.recognize_google(audio)
        return text
    except sr.WaitTimeoutError:
        st.warning("⏰ No speech detected. Please try again.")
        return None
    except sr.UnknownValueError:
        st.warning("🤷 Could not understand the speech. Please try again.")
        return None
    except sr.RequestError as e:
        st.error(f"❌ Error with speech recognition service: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None

# Main chat interface
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("💬 Chat")
    
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        for i, message in enumerate(st.session_state.messages):
            timestamp = message.get('timestamp', '')
            
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 You:</strong> {message["content"]}
                    {f'<div class="timestamp">{timestamp}</div>' if show_timestamps and timestamp else ''}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message bot-message">
                    <strong>🤖 Bot:</strong> {message["content"]}
                    {f'<div class="timestamp">{timestamp}</div>' if show_timestamps and timestamp else ''}
                </div>
                """, unsafe_allow_html=True)
                
                # Add audio player for bot responses if TTS is enabled
                if enable_tts and 'audio' in message:
                    st.audio(message['audio'], format='audio/wav')

with col2:
    st.subheader("🎤 Voice Input")
    
    # Speech to text button
    if st.button("🎙️ Start Voice Input", key="voice_input"):
        if not st.session_state.listening:
            st.session_state.listening = True
            
            with st.spinner("Listening..."):
                recognized_text = speech_to_text()
            
            st.session_state.listening = False
            
            if recognized_text:
                st.success(f"Recognized: {recognized_text}")
                
                # Add user message
                timestamp = datetime.now().strftime("%H:%M:%S")
                st.session_state.messages.append({
                    "role": "user", 
                    "content": recognized_text,
                    "timestamp": timestamp
                })
                
                # Get bot response
                with st.spinner("Thinking..."):
                    response = get_chatbot_response(recognized_text)
                
                # Generate audio for response
                audio_bytes = text_to_speech(response)
                
                # Add bot message
                bot_message = {
                    "role": "assistant", 
                    "content": response,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                }
                
                if audio_bytes:
                    bot_message["audio"] = audio_bytes
                
                st.session_state.messages.append(bot_message)
                st.rerun()
    
    # Show listening indicator
    if st.session_state.listening:
        st.markdown('<div class="listening-indicator">🎤 Listening...</div>', unsafe_allow_html=True)
    
    # Microphone status
    st.info("💡 Click the button above to start voice input")

# Text input at the bottom
st.subheader("⌨️ Text Input")
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_area("Type your message here...", height=100, key="text_input")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        submit_button = st.form_submit_button("📤 Send")
    
    with col2:
        if st.form_submit_button("🔊 Send & Speak"):
            submit_button = True
    
    if submit_button and user_input.strip():
        # Add user message
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.messages.append({
            "role": "user", 
            "content": user_input,
            "timestamp": timestamp
        })
        
        # Get bot response
        with st.spinner("Thinking..."):
            response = get_chatbot_response(user_input)
        
        # Generate audio for response
        audio_bytes = text_to_speech(response)
        
        # Add bot message
        bot_message = {
            "role": "assistant", 
            "content": response,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        
        if audio_bytes:
            bot_message["audio"] = audio_bytes
        
        st.session_state.messages.append(bot_message)
        st.rerun()

# Instructions
with st.expander("📋 Instructions"):
    st.markdown("""
    ### How to use this chatbot:
    
    **Text Input:**
    - Type your message in the text area at the bottom
    - Click "📤 Send" to send the message
    - Click "🔊 Send & Speak" to send and hear the response
    
    **Voice Input:**
    - Click "🎙️ Start Voice Input" button
    - Speak clearly when prompted
    - The system will convert your speech to text and send it
    
    **Settings:**
    - Use the sidebar to adjust voice settings
    - Enable/disable text-to-speech
    - Adjust speech rate and volume
    - Toggle timestamps on messages
    - Clear chat history
    
    **Requirements:**
    **Note:** Make sure your microphone is working and you have an internet connection for speech recognition.
    """)

# Footer
st.markdown("---")
st.markdown("🤖 **Masala Mamu : Agentic AI Kitchen Assistant** - Built with Streamlit | Speech Recognition & Text-to-Speech Enabled")
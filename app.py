import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
import io
from pydub import AudioSegment

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Personality prompts
PERSONALITIES = {
    "General Assistant": {
        "name": "General Assistant",
        "emoji": "🤖",
        "system_prompt": "You are a helpful and friendly AI assistant. Provide clear, accurate, and helpful responses to user questions.",
        "description": "A versatile assistant ready to help with any topic"
    },
    "Study Buddy": {
        "name": "Study Buddy",
        "emoji": "📚",
        "system_prompt": "You are a supportive study buddy. Help users learn by explaining concepts clearly, asking thoughtful questions, and encouraging understanding. Break down complex topics into digestible pieces.",
        "description": "Your learning companion for academic success"
    },
    "Fitness Coach": {
        "name": "Fitness Coach",
        "emoji": "💪",
        "system_prompt": "You are an enthusiastic fitness coach. Provide motivating advice on workouts, nutrition, and healthy lifestyle choices. Be encouraging and supportive while promoting safe exercise practices.",
        "description": "Motivational coach for health and fitness goals"
    },
    "Gaming Helper": {
        "name": "Gaming Helper",
        "emoji": "🎮",
        "system_prompt": "You are a knowledgeable gaming companion. Help with game strategies, tips, walkthroughs, and gaming-related questions. Be enthusiastic and use gaming terminology appropriately.",
        "description": "Your guide to gaming strategies and tips"
    }
}

# Page configuration
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="💬",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "personality" not in st.session_state:
    st.session_state.personality = "General Assistant"

if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

if "audio_processed" not in st.session_state:
    st.session_state.audio_processed = False

if "is_recording" not in st.session_state:
    st.session_state.is_recording = False

if "transcription_status" not in st.session_state:
    st.session_state.transcription_status = ""

if "error_message" not in st.session_state:
    st.session_state.error_message = ""

if "language" not in st.session_state:
    st.session_state.language = "en-US"

if "command_executed" not in st.session_state:
    st.session_state.command_executed = False

# Language configurations
LANGUAGES = {
    "English": "en-US",
    "Spanish": "es-ES",
    "French": "fr-FR",
    "German": "de-DE",
    "Chinese (Mandarin)": "zh-CN",
    "Japanese": "ja-JP",
    "Korean": "ko-KR",
    "Italian": "it-IT",
    "Portuguese": "pt-BR",
    "Russian": "ru-RU"
}

def process_voice_command(text):
    """Process voice commands and return command type and parameters"""
    text_lower = text.lower().strip()

    # Clear chat command
    if "clear chat" in text_lower or "clear history" in text_lower or "clear conversation" in text_lower:
        return "clear_chat", None

    # Personality change command
    personality_keywords = {
        "general": "General Assistant",
        "study": "Study Buddy",
        "fitness": "Fitness Coach",
        "gaming": "Gaming Helper",
        "game": "Gaming Helper"
    }

    if "change personality" in text_lower or "switch personality" in text_lower or "change to" in text_lower or "switch to" in text_lower:
        for keyword, personality in personality_keywords.items():
            if keyword in text_lower:
                return "change_personality", personality

    return None, None

# Function to generate AI response
def generate_response(prompt):
    """Generate AI response for the given prompt"""
    try:
        # Initialize the model
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Build conversation history with system prompt
        system_prompt = PERSONALITIES[st.session_state.personality]["system_prompt"]

        # Create chat history for context (convert roles for Gemini API)
        chat_history = []
        for msg in st.session_state.messages[:-1]:  # Exclude the latest user message
            # Gemini uses "user" and "model" roles, not "assistant"
            role = "model" if msg["role"] == "assistant" else msg["role"]
            chat_history.append({
                "role": role,
                "parts": [msg["content"]]
            })

        # Start chat with history
        chat = model.start_chat(history=chat_history)

        # Send message with system prompt context
        full_prompt = f"{system_prompt}\n\nUser: {prompt}"
        if len(st.session_state.messages) == 1:  # First message
            response = chat.send_message(full_prompt)
        else:
            response = chat.send_message(prompt)

        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# Sidebar
with st.sidebar:
    st.title("AI Chatbot Settings")

    # Personality selector
    selected_personality = st.selectbox(
        "Choose Assistant Personality",
        options=list(PERSONALITIES.keys()),
        index=list(PERSONALITIES.keys()).index(st.session_state.personality)
    )

    # Update personality if changed
    if selected_personality != st.session_state.personality:
        st.session_state.personality = selected_personality
        st.session_state.messages = []  # Clear chat history when personality changes
        st.rerun()

    # Display personality info
    personality_info = PERSONALITIES[st.session_state.personality]
    st.markdown(f"### {personality_info['emoji']} {personality_info['name']}")
    st.markdown(f"*{personality_info['description']}*")

    st.markdown("---")
    st.markdown("### 🌍 Voice Language")

    # Language selector
    selected_language = st.selectbox(
        "Select Voice Input Language",
        options=list(LANGUAGES.keys()),
        index=list(LANGUAGES.values()).index(st.session_state.language)
    )

    # Update language if changed
    if LANGUAGES[selected_language] != st.session_state.language:
        st.session_state.language = LANGUAGES[selected_language]

    st.markdown("---")
    st.markdown("### 🎤 Voice Input Tips")
    st.info("**For best results:**\n- Speak clearly and slowly\n- Use a quiet environment\n- Keep device close to mic\n- Click once to start, once to stop")

    st.markdown("---")
    st.markdown("### 🎯 Voice Commands")
    st.success("**Try these commands:**\n- 'Clear chat' - Clear history\n- 'Change to study' - Switch personality\n- 'Switch to fitness' - Change mode")

    st.markdown("---")
    st.markdown("### About")
    st.markdown("This chatbot uses Google's Gemini AI to provide intelligent responses.")
    st.markdown("**Model:** gemini-2.5-flash")

    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Main chat interface
st.title(f"{PERSONALITIES[st.session_state.personality]['emoji']} AI Chatbot")
st.markdown(f"*Currently: {st.session_state.personality}*")

# Display chat messages
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Input section (always visible at bottom)
st.markdown("---")
st.markdown("### 🎤 Voice Input")

# Create columns for better layout
col_recorder, col_status = st.columns([1, 3])
with col_recorder:
    # Audio recorder
    audio_bytes = audio_recorder(
        text="",
        recording_color="#e74c3c",
        neutral_color="#3498db",
        icon_name="microphone",
        icon_size="2x",
        key="audio_recorder"
    )

with col_status:
    # Status display
    if st.session_state.transcription_status == "processing":
        st.warning("⏳ **Processing your speech...**")
    elif st.session_state.transcription_status == "ready":
        st.success("✅ **Ready!** Transcription complete.")
    elif st.session_state.transcription_status == "error":
        st.error(f"❌ {st.session_state.error_message}")
        if st.button("🔄 Try Again", key="retry_voice"):
            st.session_state.transcription_status = ""
            st.session_state.error_message = ""
            st.rerun()
    elif st.session_state.transcription_status == "permission_denied":
        st.error("🔒 **Microphone access denied**")
        st.info("Please allow microphone access in your browser settings and click 'Try Again'")
        if st.button("🔄 Try Again", key="retry_permission"):
            st.session_state.transcription_status = ""
            st.rerun()
    elif st.session_state.transcription_status == "no_speech":
        st.warning("🔇 **No speech detected**")
        st.info("Please speak clearly after clicking the microphone")
        if st.button("🔄 Try Again", key="retry_no_speech"):
            st.session_state.transcription_status = ""
            st.rerun()
    else:
        st.info("💡 **Click microphone, then speak clearly**")

# Process audio if new recording is available
if audio_bytes:
    # Check if this is a new recording by comparing with previous
    if "last_audio_len" not in st.session_state:
        st.session_state.last_audio_len = 0

    current_len = len(audio_bytes)
    if current_len != st.session_state.last_audio_len:
        st.session_state.last_audio_len = current_len
        st.session_state.transcription_status = "processing"
        st.rerun()

# Handle transcription after rerun
if st.session_state.transcription_status == "processing" and audio_bytes:
    with st.spinner("🎧 Transcribing your speech..."):
        try:
            # Check if audio is too short (likely silence)
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")

            # If audio is very short (less than 0.5 seconds), it's likely just noise
            if len(audio) < 500:  # milliseconds
                st.session_state.transcription_status = "no_speech"
                st.warning("🔇 Recording too short. Please speak clearly after clicking the microphone.")
            else:
                # Export as WAV for speech recognition
                wav_io = io.BytesIO()
                audio.export(wav_io, format="wav")
                wav_io.seek(0)

                # Use speech recognition
                recognizer = sr.Recognizer()
                # Adjust for ambient noise
                with sr.AudioFile(wav_io) as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    audio_data = recognizer.record(source)

                    try:
                        # Use the selected language for recognition
                        text = recognizer.recognize_google(audio_data, language=st.session_state.language)
                        if text and text.strip():
                            # Check for voice commands
                            command_type, command_param = process_voice_command(text)

                            if command_type == "clear_chat":
                                st.session_state.messages = []
                                st.session_state.transcription_status = "ready"
                                st.session_state.command_executed = True
                                st.success(f"🎤 **Voice Command:** Cleared chat history!")
                                st.balloons()
                            elif command_type == "change_personality":
                                if command_param:
                                    st.session_state.personality = command_param
                                    st.session_state.messages = []
                                    st.session_state.transcription_status = "ready"
                                    st.session_state.command_executed = True
                                    st.success(f"🎤 **Voice Command:** Switched to {command_param}!")
                                    st.balloons()
                                else:
                                    st.session_state.voice_text = text
                                    st.session_state.transcription_status = "ready"
                                    st.success(f"✅ **Transcribed:** {text}")
                            else:
                                # Normal transcription
                                st.session_state.voice_text = text
                                st.session_state.transcription_status = "ready"
                                st.success(f"✅ **Transcribed:** {text}")
                        else:
                            st.session_state.transcription_status = "no_speech"
                    except sr.UnknownValueError:
                        # Speech was unintelligible
                        st.session_state.transcription_status = "no_speech"
                        st.warning("🔇 No clear speech detected. Please try again and speak more clearly.")
                    except sr.RequestError as e:
                        # API request failed
                        if "permission" in str(e).lower() or "denied" in str(e).lower():
                            st.session_state.transcription_status = "permission_denied"
                        else:
                            st.session_state.transcription_status = "error"
                            st.session_state.error_message = "**Connection error** - Please check your internet and try again"
                            st.error(f"❌ {st.session_state.error_message}")

        except PermissionError:
            st.session_state.transcription_status = "permission_denied"
        except Exception as e:
            # Generic error handling
            error_msg = str(e).lower()
            if "permission" in error_msg or "access" in error_msg:
                st.session_state.transcription_status = "permission_denied"
            else:
                st.session_state.transcription_status = "error"
                st.session_state.error_message = "**Something went wrong** - Please try again"
                st.error(f"❌ {st.session_state.error_message}")

st.markdown("---")

# Display transcribed text if available
if st.session_state.voice_text:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.success(f"📝 **Ready to send:** {st.session_state.voice_text}")
    with col2:
        if st.button("🗑️ Clear", key="clear_voice"):
            st.session_state.voice_text = ""
            st.session_state.transcription_status = ""
            st.rerun()

st.markdown("### 💬 Text Input")

# Chat input - use voice text if available, otherwise allow typing
if st.session_state.voice_text:
    # Show a button to send the voice transcription
    col1, col2 = st.columns([1, 5])
    with col1:
        send_voice = st.button("📤 Send Voice Text", type="primary")
    with col2:
        st.markdown("*Or type your own message below*")

    if send_voice:
        prompt = st.session_state.voice_text
        st.session_state.voice_text = ""
        st.session_state.transcription_status = ""

        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate and add assistant response
        with st.spinner("Thinking..."):
            response_text = generate_response(prompt)
            st.session_state.messages.append({"role": "assistant", "content": response_text})

        st.rerun()

# Regular chat input
if prompt := st.chat_input("Type your message here or send voice text above..."):
    # Clear voice text when user types their own message
    st.session_state.voice_text = ""
    st.session_state.transcription_status = ""
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text = generate_response(prompt)
            st.markdown(response_text)

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response_text})

# Footer
st.markdown("---")
st.markdown("*Powered by Google Gemini 2.5 Flash*")

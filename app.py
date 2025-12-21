import streamlit as st
import os
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
import io
from pydub import AudioSegment
import pyttsx3
import tempfile
import requests

# Load environment variables
load_dotenv()

# Hugging Face API configuration
HF_API_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"

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

if "tts_audio" not in st.session_state:
    st.session_state.tts_audio = {}

if "processing" not in st.session_state:
    st.session_state.processing = False

if "last_audio_bytes" not in st.session_state:
    st.session_state.last_audio_bytes = None

if "quick_response_mode" not in st.session_state:
    st.session_state.quick_response_mode = False

if "conversation_turn_count" not in st.session_state:
    st.session_state.conversation_turn_count = 0

if "tts_speed" not in st.session_state:
    st.session_state.tts_speed = 180  # Default speaking rate (words per minute)

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

# Language display names with flags
LANGUAGE_FLAGS = {
    "English": "🇺🇸",
    "Spanish": "🇪🇸",
    "French": "🇫🇷",
    "German": "🇩🇪",
    "Chinese (Mandarin)": "🇨🇳",
    "Japanese": "🇯🇵",
    "Korean": "🇰🇷",
    "Italian": "🇮🇹",
    "Portuguese": "🇧🇷",
    "Russian": "🇷🇺"
}

def process_voice_command(text):
    """Process voice commands and return command type and parameters"""
    text_lower = text.lower().strip()

    # Remove wake words if present
    wake_words = ["hey assistant", "hey chatbot", "ok assistant"]
    for wake in wake_words:
        if text_lower.startswith(wake):
            text_lower = text_lower[len(wake):].strip()

    # Help command
    if any(cmd in text_lower for cmd in ["help", "commands", "what can you do", "show commands"]):
        return "help", None

    # Clear chat command
    if any(cmd in text_lower for cmd in ["clear chat", "clear history", "clear conversation", "reset chat", "new conversation"]):
        return "clear_chat", None

    # Stop audio command
    if any(cmd in text_lower for cmd in ["stop talking", "stop speaking", "stop audio", "be quiet", "silence"]):
        return "stop_audio", None

    # TTS speed commands
    if any(cmd in text_lower for cmd in ["speak faster", "talk faster", "speed up"]):
        return "speed_up", None

    if any(cmd in text_lower for cmd in ["speak slower", "talk slower", "slow down"]):
        return "slow_down", None

    if any(cmd in text_lower for cmd in ["normal speed", "reset speed", "default speed"]):
        return "normal_speed", None

    # Personality change command
    personality_keywords = {
        "general": "General Assistant",
        "study": "Study Buddy",
        "fitness": "Fitness Coach",
        "gaming": "Gaming Helper",
        "game": "Gaming Helper"
    }

    if any(cmd in text_lower for cmd in ["change personality", "switch personality", "change to", "switch to", "change mode"]):
        for keyword, personality in personality_keywords.items():
            if keyword in text_lower:
                return "change_personality", personality

    return None, None

def get_command_help_text():
    """Return formatted help text for available voice commands"""
    help_text = """**🎤 Available Voice Commands:**

**Chat Control:**
• "Clear chat" / "Reset chat" - Clear conversation history
• "Help" / "Show commands" - Display this help

**Personality:**
• "Change to study" - Switch to Study Buddy
• "Change to fitness" - Switch to Fitness Coach
• "Change to gaming" - Switch to Gaming Helper
• "Change to general" - Switch to General Assistant

**Audio Control:**
• "Speak faster" - Increase speaking speed
• "Speak slower" - Decrease speaking speed
• "Normal speed" - Reset to default speed
• "Stop talking" - Stop current audio

**Tips:**
• Start commands with "Hey Assistant" (optional)
• Commands work in any language!
• If not a command, your speech goes to the AI"""
    return help_text

def generate_tts_audio(text, message_index, show_spinner=True):
    """Generate TTS audio for a message and store in session state using gTTS"""
    if message_index not in st.session_state.tts_audio:
        try:
            from gtts import gTTS
            import platform

            # Limit text length to avoid very long audio (max 1000 chars)
            if len(text) > 1000:
                text_to_speak = text[:1000]
            else:
                text_to_speak = text

            # Get the appropriate language code for gTTS
            current_lang = st.session_state.language
            # Map language codes to gTTS language codes
            gtts_lang_map = {
                "en-US": "en",
                "es-ES": "es",
                "fr-FR": "fr",
                "de-DE": "de",
                "zh-CN": "zh-CN",
                "ja-JP": "ja",
                "ko-KR": "ko",
                "it-IT": "it",
                "pt-BR": "pt",
                "ru-RU": "ru"
            }
            lang_code = gtts_lang_map.get(current_lang, "en")

            # Create temporary file for MP3
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio:
                temp_mp3 = temp_audio.name

            # Generate TTS audio using gTTS
            tts = gTTS(text=text_to_speak, lang=lang_code, slow=False)
            tts.save(temp_mp3)

            # Read the generated audio file
            with open(temp_mp3, 'rb') as audio_file:
                audio_bytes = audio_file.read()

            # Clean up temporary file
            try:
                if os.path.exists(temp_mp3):
                    os.unlink(temp_mp3)
            except Exception:
                pass

            if len(audio_bytes) > 1000:  # Should be larger than just a header
                st.session_state.tts_audio[message_index] = (audio_bytes, 'mp3')
            else:
                st.session_state.tts_audio[message_index] = None

        except Exception as e:
            st.session_state.tts_audio[message_index] = None

    return st.session_state.tts_audio.get(message_index)

# Function to generate AI response
def generate_response(prompt):
    """Generate AI response for the given prompt using Hugging Face API"""
    try:
        # Build conversation history with system prompt
        system_prompt = PERSONALITIES[st.session_state.personality]["system_prompt"]

        # Add language instruction to system prompt
        current_lang = st.session_state.language
        language_names = {
            "en-US": "English",
            "es-ES": "Spanish",
            "fr-FR": "French",
            "de-DE": "German",
            "zh-CN": "Chinese (Mandarin)",
            "ja-JP": "Japanese",
            "ko-KR": "Korean",
            "it-IT": "Italian",
            "pt-BR": "Portuguese",
            "ru-RU": "Russian"
        }
        language_instruction = f"\n\nIMPORTANT: Please respond in {language_names.get(current_lang, 'English')}."
        system_prompt_with_lang = system_prompt + language_instruction

        # Create conversation messages for HuggingFace API
        messages = []

        # Add system prompt as first message
        messages.append({
            "role": "system",
            "content": system_prompt_with_lang
        })

        # Add conversation history
        for msg in st.session_state.messages[:-1]:  # Exclude the latest user message
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Add current user message
        messages.append({
            "role": "user",
            "content": prompt
        })

        # Call Hugging Face Inference API
        headers = {
            "Authorization": f"Bearer {HF_API_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": messages,
            "parameters": {
                "max_new_tokens": 500,
                "temperature": 0.7,
                "top_p": 0.9,
                "return_full_text": False
            }
        }

        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "Sorry, I couldn't generate a response.")
            elif isinstance(result, dict):
                return result.get("generated_text", "Sorry, I couldn't generate a response.")
            else:
                return "Sorry, I couldn't generate a response."
        else:
            return f"Error: {response.status_code} - {response.text}"

    except Exception as e:
        return f"Error: {str(e)}"

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Settings")

    # Personality selector
    selected_personality = st.selectbox(
        "🎭 AI Personality",
        options=list(PERSONALITIES.keys()),
        index=list(PERSONALITIES.keys()).index(st.session_state.personality),
        help="Select the AI's personality and response style"
    )

    # Update personality if changed
    if selected_personality != st.session_state.personality:
        st.session_state.personality = selected_personality
        st.session_state.messages = []  # Clear chat history when personality changes
        st.rerun()

    # Display personality info in compact format
    personality_info = PERSONALITIES[st.session_state.personality]
    st.caption(f"*{personality_info['description']}*")

    st.markdown("---")

    # Language settings - more prominent
    st.markdown("### 🌍 Language")

    # Create language options with flags
    language_options = [f"{LANGUAGE_FLAGS[lang]} {lang}" for lang in LANGUAGES.keys()]
    current_lang_name = next(k for k, v in LANGUAGES.items() if v == st.session_state.language)
    current_index = list(LANGUAGES.keys()).index(current_lang_name)

    selected_language_display = st.selectbox(
        "Select Language",
        options=language_options,
        index=current_index,
        help="Language for AI responses, voice input, and voice output"
    )

    # Extract language name from display string (remove flag emoji)
    selected_language = selected_language_display.split(" ", 1)[1]

    # Update language if changed
    if LANGUAGES[selected_language] != st.session_state.language:
        st.session_state.language = LANGUAGES[selected_language]
        # Clear TTS cache when language changes
        st.session_state.tts_audio = {}
        st.rerun()

    # Show current language info
    current_lang_code = st.session_state.language
    st.caption(f"**Current:** {LANGUAGE_FLAGS[selected_language]} {selected_language} ({current_lang_code})")
    st.caption("💬 AI will respond in this language")
    st.caption("🎤 Voice input recognizes this language")
    st.caption("🔊 Voice output uses native speaker")

    st.markdown("---")

    # Voice settings in expander
    with st.expander("🎤 Voice Tips & Commands", expanded=False):
        st.markdown("##### 💡 Tips for Best Results")
        st.caption("• Speak clearly and slowly")
        st.caption("• Use a quiet environment")
        st.caption("• Keep device close to mic")

        st.markdown("##### 🎯 Voice Commands")
        st.caption("• 'Clear chat' - Clear history")
        st.caption("• 'Change to study' - Switch personality")

    st.markdown("---")

    # Quick Response Mode
    st.markdown("### 🎙️ Voice Mode")

    quick_mode = st.checkbox(
        "Quick Response Mode",
        value=st.session_state.quick_response_mode,
        help="Automatically clear voice input after sending, making multi-turn conversations faster"
    )

    if quick_mode != st.session_state.quick_response_mode:
        st.session_state.quick_response_mode = quick_mode
        st.rerun()

    if st.session_state.quick_response_mode:
        st.caption("✅ Voice input will auto-clear after each message")
        st.caption("🔄 Just click mic and speak for each turn")
    else:
        st.caption("ℹ️ Normal mode - manual workflow")

    st.markdown("---")

    # Action buttons
    st.markdown("### Actions")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear\nChat", use_container_width=True, help="Clear conversation history"):
            st.session_state.messages = []
            st.session_state.tts_audio = {}
            st.rerun()

    with col2:
        if st.button("🔄 Reload\nAudio", use_container_width=True, help="Regenerate all audio"):
            st.session_state.tts_audio = {}
            st.rerun()

    st.markdown("---")
    st.markdown("### About")
    st.caption("**AI Model:** Gemini 2.5 Flash")
    st.caption("**Features:** Voice chat • TTS • Multi-language")

# Main chat interface
current_lang_name = next(k for k, v in LANGUAGES.items() if v == st.session_state.language)
st.title(f"{PERSONALITIES[st.session_state.personality]['emoji']} AI Chatbot")

# Show mode indicator
mode_indicator = "🎙️ Quick Response" if st.session_state.quick_response_mode else "💬 Normal"
st.markdown(f"*Personality: {st.session_state.personality}* • {LANGUAGE_FLAGS[current_lang_name]} *Language: {current_lang_name}* • *{mode_indicator}*")

# Show language info for non-English users
if st.session_state.language != "en-US" and len(st.session_state.messages) == 0:
    language_greetings = {
        "es-ES": "¡Hola! Puedes hablar conmigo en español. 🇪🇸",
        "fr-FR": "Bonjour! Vous pouvez me parler en français. 🇫🇷",
        "de-DE": "Hallo! Du kannst mit mir auf Deutsch sprechen. 🇩🇪",
        "zh-CN": "你好！你可以用中文和我聊天。🇨🇳",
        "ja-JP": "こんにちは！日本語で話せます。🇯🇵",
        "ko-KR": "안녕하세요! 한국어로 대화할 수 있습니다. 🇰🇷",
        "it-IT": "Ciao! Puoi parlare con me in italiano. 🇮🇹",
        "pt-BR": "Olá! Você pode falar comigo em português. 🇧🇷",
        "ru-RU": "Привет! Вы можете говорить со мной по-русски. 🇷🇺"
    }
    greeting = language_greetings.get(st.session_state.language, "")
    if greeting:
        st.info(f"**{greeting}**\n\nThe AI will respond in {current_lang_name}, and voice output will use a native {current_lang_name} speaker.")

# Display chat messages
chat_container = st.container()
with chat_container:
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

        # Display audio player for assistant messages (OUTSIDE chat_message)
        if message["role"] == "assistant":
            # Add visual separation
            st.markdown("---")

            # Check if message is very long
            is_long_message = len(message["content"]) > 500

            # Show warning for long messages
            if is_long_message and idx not in st.session_state.tts_audio:
                with st.spinner("🎵 Generating audio for long message..."):
                    audio_result = generate_tts_audio(message["content"], idx, show_spinner=False)
            else:
                audio_result = generate_tts_audio(message["content"], idx, show_spinner=False)

            # Create responsive layout for audio player
            audio_col1, audio_col2 = st.columns([3, 1])

            with audio_col1:
                if audio_result:
                    audio_bytes, audio_format = audio_result
                    st.markdown("**🔊 Audio Response**")

                    # Use HTML audio with autoplay for automatic playback
                    import base64
                    audio_b64 = base64.b64encode(audio_bytes).decode()
                    audio_html = f"""
                    <audio controls autoplay style="width: 100%;">
                        <source src="data:audio/{audio_format};base64,{audio_b64}" type="audio/{audio_format}">
                    </audio>
                    """
                    st.markdown(audio_html, unsafe_allow_html=True)

                    # Show format info in smaller text
                    file_size_kb = len(audio_bytes) / 1024
                    st.caption(f"*{audio_format.upper()} • {file_size_kb:.1f}KB*")

                    # Show truncation warning if applicable
                    if len(message["content"]) > 1000:
                        st.caption("⚠️ *Long message truncated to 1000 characters for audio*")

                elif idx in st.session_state.tts_audio:
                    st.error("❌ Audio generation failed")
                    if st.button(f"🔄 Retry Audio", key=f"retry_{idx}", help="Click to retry audio generation"):
                        del st.session_state.tts_audio[idx]
                        st.rerun()

            st.markdown("")  # Add spacing

# Input section (always visible at bottom)
st.markdown("---")

# Add helpful tip at the top for first-time users
if len(st.session_state.messages) == 0:
    if st.session_state.quick_response_mode:
        st.info("🎙️ **Quick Response Mode Active!**\n\nClick microphone → Speak → Send → Repeat. Voice input auto-clears after each turn for faster conversations!")
    else:
        st.info("💬 **Get Started:** Type a message below or use voice input to chat with the AI assistant!")

st.markdown("### 🎤 Voice Input")

# Show quick response mode status
if st.session_state.quick_response_mode and len(st.session_state.messages) > 0:
    turns = st.session_state.conversation_turn_count
    st.caption(f"🎙️ Quick Response Mode | Turn: {turns}")

# Create responsive columns for better layout
col_recorder, col_status = st.columns([1, 2])
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
    # Status display with better formatting
    if st.session_state.transcription_status == "processing":
        st.warning("⏳ **Processing your speech...**")
    elif st.session_state.transcription_status == "ready":
        st.success("✅ **Ready!** Transcription complete.")
    elif st.session_state.transcription_status == "error":
        st.error(f"❌ **Error**\n\n{st.session_state.error_message}")
        col_retry1, col_retry2 = st.columns([1, 1])
        with col_retry1:
            if st.button("🔄 Retry", key="retry_voice", use_container_width=True):
                st.session_state.transcription_status = ""
                st.session_state.error_message = ""
                st.rerun()
        with col_retry2:
            if st.button("✖️ Dismiss", key="dismiss_voice", use_container_width=True):
                st.session_state.transcription_status = ""
                st.session_state.error_message = ""
                st.rerun()
    elif st.session_state.transcription_status == "permission_denied":
        st.error("🔒 **Microphone access denied**")
        st.info("Allow microphone access in browser settings")
        if st.button("🔄 Try Again", key="retry_permission", use_container_width=True):
            st.session_state.transcription_status = ""
            st.rerun()
    elif st.session_state.transcription_status == "no_speech":
        st.warning("🔇 **No speech detected**")
        st.caption("Speak clearly after clicking microphone")
        if st.button("🔄 Try Again", key="retry_no_speech", use_container_width=True):
            st.session_state.transcription_status = ""
            st.rerun()
    else:
        st.info("💡 **Click microphone, then speak**")
        st.caption("Try voice commands like 'clear chat'")

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
                            elif command_type == "help":
                                st.session_state.transcription_status = "ready"
                                st.session_state.command_executed = True
                                st.info(get_command_help_text())
                            elif command_type == "speed_up":
                                st.session_state.tts_speed = min(st.session_state.tts_speed + 25, 300)
                                st.session_state.tts_audio = {}  # Clear cache to regenerate with new speed
                                st.session_state.transcription_status = "ready"
                                st.session_state.command_executed = True
                                st.success(f"🎤 **Voice Command:** Speaking speed increased to {st.session_state.tts_speed} wpm!")
                            elif command_type == "slow_down":
                                st.session_state.tts_speed = max(st.session_state.tts_speed - 25, 100)
                                st.session_state.tts_audio = {}  # Clear cache
                                st.session_state.transcription_status = "ready"
                                st.session_state.command_executed = True
                                st.success(f"🎤 **Voice Command:** Speaking speed decreased to {st.session_state.tts_speed} wpm!")
                            elif command_type == "normal_speed":
                                st.session_state.tts_speed = 180
                                st.session_state.tts_audio = {}  # Clear cache
                                st.session_state.transcription_status = "ready"
                                st.session_state.command_executed = True
                                st.success(f"🎤 **Voice Command:** Speaking speed reset to normal (180 wpm)!")
                            elif command_type == "stop_audio":
                                st.session_state.transcription_status = "ready"
                                st.session_state.command_executed = True
                                st.warning("🎤 **Voice Command:** Audio playback cannot be stopped (browser limitation)")
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

# Chat input - use voice text if available, otherwise allow typing
if st.session_state.voice_text:
    # Show a button to send the voice transcription
    send_voice = st.button("📤 Send Voice Text", type="primary", use_container_width=True)
    st.caption("*Or type your own message below ↓*")

    if send_voice:
        prompt = st.session_state.voice_text
        st.session_state.voice_text = ""
        st.session_state.transcription_status = ""
        st.session_state.conversation_turn_count += 1

        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate and add assistant response
        response_text = generate_response(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response_text})

        # Generate TTS audio for the new message
        message_index = len(st.session_state.messages) - 1
        generate_tts_audio(response_text, message_index)

        # In Quick Response Mode, show reminder to continue
        if st.session_state.quick_response_mode:
            st.toast("🎤 Quick Response Mode: Click mic for next turn!", icon="🔄")

        st.rerun()

# Regular chat input
st.markdown("### 💬 Text Input")
if prompt := st.chat_input("Type your message here... or use voice input above 👆"):
    # Clear voice text when user types their own message
    st.session_state.voice_text = ""
    st.session_state.transcription_status = ""
    st.session_state.error_message = ""

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate AI response
    with st.spinner("🤔 Thinking..."):
        response_text = generate_response(prompt)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response_text})

        # Generate TTS audio for the new message
        message_index = len(st.session_state.messages) - 1
        with st.spinner("🎵 Generating audio..."):
            generate_tts_audio(response_text, message_index, show_spinner=False)

    st.rerun()

# Footer
st.markdown("---")
st.markdown("*Powered by Google Gemini 2.5 Flash*")

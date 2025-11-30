---
title: AI Voice Chatbot
emoji: 🎤
colorFrom: blue
colorTo: purple
sdk: streamlit
sdk_version: "1.31.0"
app_file: app.py
pinned: false
---

# AI Voice Chatbot with Streamlit and Google Gemini

A powerful AI chatbot web application built with Streamlit and Google Gemini 2.5 Flash, featuring voice input capabilities, multi-language support, and customizable AI personalities.

## 🚀 Live Deployments

Try the app online without any installation:

- **Hugging Face Spaces**: [https://huggingface.co/spaces/Leo-codecub/voice-ai-assistant](https://huggingface.co/spaces/Leo-codecub/voice-ai-assistant)
- **GitHub Repository**: [https://github.com/CodeCubCA/voice-ai-assistant-Leo-CodeCub](https://github.com/CodeCubCA/voice-ai-assistant-Leo-CodeCub)

> **Note**: The app is deployed on Hugging Face Spaces for easy access. Simply click the link above to start chatting with AI using voice or text!

## Features

### Core Functionality
- **AI-Powered Conversations**: Leverages Google Gemini 2.5 Flash for intelligent, context-aware responses
- **Voice Input**: Speak to the chatbot using your microphone with real-time speech-to-text transcription
- **Voice Output (TTS)**: Multi-language text-to-speech with native speaker voices and automatic playback
- **Multi-Language Support**: Voice recognition in 10 languages including English, Spanish, French, German, Chinese, Japanese, Korean, Italian, Portuguese, and Russian
- **Voice Commands**: Hands-free control with commands like "clear chat", "switch personality", and TTS speed control
- **Multiple AI Personalities**: Choose from 4 distinct personalities tailored for different use cases

### AI Personalities

1. **General Assistant** - A versatile assistant ready to help with any topic
2. **Study Buddy** - Your learning companion for academic success
3. **Fitness Coach** - Motivational coach for health and fitness goals
4. **Gaming Helper** - Your guide to gaming strategies and tips

### User Experience
- **Visual Feedback**: Real-time status indicators for voice processing, transcription, and errors
- **Error Handling**: Comprehensive error messages with retry options for microphone permissions, silent recordings, and connection issues
- **Responsive Design**: Clean, intuitive interface with clear organization
- **Chat History**: Maintains conversation context throughout your session
- **Quick Response Mode**: Streamlined voice conversation workflow for faster interactions

## Installation

### Prerequisites
- Python 3.8 or higher
- A Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- FFmpeg (required for audio processing)

### FFmpeg Installation

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from [FFmpeg official website](https://ffmpeg.org/download.html) and add to PATH

**Linux:**
```bash
sudo apt-get install ffmpeg
```

### Setup Steps

1. **Clone the repository:**
```bash
git clone https://github.com/CodeCubCA/voice-ai-assistant-Leo-CodeCub.git
cd voice-ai-assistant
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up your API key:**
   - Create a `.env` file in the project root
   - Add your Gemini API key:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

## Usage

1. **Start the application:**
```bash
streamlit run app.py
```

2. **Access the chatbot:**
   - The app will automatically open in your default browser
   - If not, navigate to `http://localhost:8501`

3. **Interact with the chatbot:**
   - **Text Input**: Type your message in the text box at the bottom
   - **Voice Input**: Click the microphone icon, speak clearly, then click again to stop recording
   - **Voice Output**: Audio responses play automatically after each AI message
   - **Change Personality**: Use the sidebar dropdown or voice command "switch to [personality]"

## Voice Commands

Use these voice commands for hands-free control:

### Chat Control
- **"Clear chat"** or **"clear history"** - Clears the conversation history
- **"Help"** or **"show commands"** - Display all available voice commands

### Personality Switching
- **"Change to study"** or **"switch to study"** - Switches to Study Buddy personality
- **"Change to fitness"** or **"switch to fitness"** - Switches to Fitness Coach personality
- **"Change to gaming"** or **"switch to gaming"** - Switches to Gaming Helper personality
- **"Change to general"** or **"switch to general"** - Switches to General Assistant personality

### Audio Control
- **"Speak faster"** or **"speed up"** - Increase TTS speaking speed
- **"Speak slower"** or **"slow down"** - Decrease TTS speaking speed
- **"Normal speed"** - Reset to default speaking speed
- **"Stop talking"** - Stop current audio (note: browser limitations apply)

### Wake Word Support
All commands can optionally start with **"Hey Assistant"**, **"Hey Chatbot"**, or **"OK Assistant"**

## Supported Languages

Voice input supports the following languages:

- English (en-US)
- Spanish (es-ES)
- French (fr-FR)
- German (de-DE)
- Chinese/Mandarin (zh-CN)
- Japanese (ja-JP)
- Korean (ko-KR)
- Italian (it-IT)
- Portuguese (pt-BR)
- Russian (ru-RU)

Select your preferred language from the sidebar dropdown.

## Technical Stack

- **Frontend Framework**: Streamlit
- **AI Model**: Google Gemini 2.5 Flash
- **Speech Recognition**: Google Speech Recognition API
- **Audio Processing**: PyDub
- **Voice Recording**: audio-recorder-streamlit
- **Environment Management**: python-dotenv

## Project Structure

```
voice-ai-assistant/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── .env                  # API key (not committed to Git)
├── .env.example          # Template for API key
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## Tips for Best Voice Recognition

- Speak clearly and at a moderate pace
- Use a quiet environment to minimize background noise
- Keep your device close to the microphone
- Click the microphone once to start recording, once to stop
- Allow microphone permissions when prompted by your browser

## Troubleshooting

### Microphone Not Working
- Ensure browser has microphone permissions
- Check system microphone settings
- Try the "Try Again" button after granting permissions

### No Speech Detected
- Speak louder and more clearly
- Check that your microphone is working properly
- Ensure you're speaking after clicking the microphone button

### Connection Errors
- Verify your internet connection
- Check that your Gemini API key is valid
- Ensure the API key is properly set in the `.env` file

### API Key Issues
- Make sure you've created a `.env` file (not `.env.example`)
- Verify the API key is correct and active
- Check that there are no extra spaces in the `.env` file

## Security Notes

- The `.env` file containing your API key is excluded from version control
- Never commit your actual API key to the repository
- Use `.env.example` as a template for other users

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available for educational and personal use.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [Google Gemini AI](https://deepmind.google/technologies/gemini/)
- Speech recognition by [SpeechRecognition](https://github.com/Uberi/speech_recognition)

---

*Powered by Google Gemini 2.5 Flash*

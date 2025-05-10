# 🎙️ Voice Desktop Assistant

A powerful voice-controlled desktop assistant that helps you manage your calendar, search files, and control your computer using natural language commands. Built with modern web technologies and powered by OpenAI's GPT-4.

## 🛠️ Tech Stack

### Frontend
- **Electron.js** - Cross-platform desktop application framework
- **WebSocket** - Real-time bidirectional communication
- **Web Audio API** - High-quality audio capture and processing
- **Modern CSS** - Clean, responsive UI with smooth animations

### Backend
- **FastAPI** - High-performance async web framework
- **Python 3.12** - Core programming language
- **OpenAI GPT-4** - Natural language understanding
- **Google Cloud Speech-to-Text** - Accurate speech recognition
- **Google Calendar API** - Calendar management
- **WebSocket** - Real-time audio streaming

## ✨ Features

- **🎯 Voice Command Recognition**
  - Real-time audio streaming via WebSocket
  - High-quality audio capture (44.1kHz, 16-bit)
  - Noise suppression and echo cancellation
  - Accent-friendly speech recognition

- **📅 Calendar Management**
  - Schedule meetings with natural language
  - Check upcoming events
  - Smart date/time parsing
  - Timezone-aware scheduling
  - Real-time calendar updates

- **🔍 File Search**
  - Fast and efficient file searching
  - Prioritizes most recent files
  - Supports partial matches
  - Searches across multiple directories

- **🤖 AI-Powered Understanding**
  - GPT-4 powered command processing
  - Natural language understanding
  - Context-aware responses
  - Structured command output
  - Real-time response formatting

- **🎨 Modern UI**
  - Dynamic status orb with color states
  - Real-time transcription display
  - Instant response feedback
  - Clean, minimalist design
  - Smooth animations and transitions

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher
- Node.js 18 or higher
- Google Cloud account (for Speech-to-Text)
- OpenAI API key
- Google Calendar API credentials

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/voice-desktop-assistant.git
   cd voice-desktop-assistant
   ```

2. Set up the backend:
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install Python dependencies
   pip install -r server/requirements.txt
   ```

3. Set up the frontend:
   ```bash
   # Install Node.js dependencies
   cd client
   npm install
   ```

4. Configure environment variables in `.env`:
   ```
   OPENAI_API_KEY=your_openai_api_key
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
   TARGET_CALENDAR_EMAIL=your_calendar_email
   ```

### Running the Application

1. Start the backend server:
   ```bash
   # From the server directory
   python start_server.py
   ```

2. Start the desktop application:
   ```bash
   # From the client directory
   npm start
   ```

3. Use the application:
   - Click the orb to start/stop recording
   - Speak your commands naturally
   - Watch the orb change colors based on system state
   - View real-time transcription and responses

## 🎮 Usage Examples

### Calendar Commands
- "What's on my calendar today?"
- "Schedule a meeting with John next Friday at 5:30 PM"
- "Add a team meeting tomorrow at 2 PM"
- "Check my calendar for next week"

### File Search Commands
- "Find files containing 'project'"
- "Search for my resume"
- "Show me recent PDF files"
- "Find documents from last week"

## 🔧 Configuration

### Audio Settings
- Sample rate: 44.1kHz
- Bit depth: 16-bit
- Channel count: Mono
- Noise suppression: Enabled
- Echo cancellation: Enabled

### UI Settings
- Orb states:
  - Gray: Idle
  - Red: Recording
  - Blue: Processing
  - Green: Speaking/Response

### Response Formatting
- Natural language responses
- Concise and clear output
- Context-aware formatting
- Error handling with user-friendly messages

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4
- Google Cloud for Speech-to-Text
- Electron.js team
- FastAPI framework
- All contributors and users

## 📞 Support

For support, please:
1. Check the [Issues](https://github.com/yourusername/voice-desktop-assistant/issues) page
2. Open a new issue if your problem isn't already listed
3. Contact the maintainers for urgent matters
# 🎙️ Voice Desktop Assistant

Hey there! 👋 This is my personal voice assistant that helps me manage my emails, calendar, and files using natural language. It's like having a friendly AI buddy that understands what I say and helps me stay organized. Built with modern tech and powered by GPT-4, it's pretty smart!

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
- **Gmail API** - Email management
- **WebSocket** - Real-time audio streaming

## ✨ Features

- **📧 Smart Email Management**
  - Check recent and important emails
  - Send emails with natural language
  - Create email drafts for review
  - Search through your inbox
  - Get concise email summaries
  - OAuth2 secure authentication

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
- Google Cloud account (for Speech-to-Text and Gmail)
- OpenAI API key
- Google Calendar API credentials
- Gmail API credentials (OAuth2)

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

5. Set up Gmail API:
   - Go to Google Cloud Console
   - Enable Gmail API
   - Create OAuth2 credentials
   - Download credentials and save as `credentials.json` in the server directory
   - Add your email as a test user in the OAuth consent screen

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

### Email Commands
- "Check my recent important emails"
- "Send an email to john@example.com about the meeting"
- "Draft an email to sarah@example.com about the project update"
- "Search my emails for messages about the job application"
- "What important emails did I get in the last 3 days?"

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

### Email Settings
- OAuth2 authentication
- Secure token storage
- Automatic token refresh
- Test mode for personal use
- Concise email summaries

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

Need help? I'm here! You can:
1. Check the [Issues](https://github.com/yourusername/voice-desktop-assistant/issues) page
2. Open a new issue if you can't find what you're looking for
3. Drop me a message for urgent stuff

Remember, this is a personal project, so I'm always happy to help make it better! 😊
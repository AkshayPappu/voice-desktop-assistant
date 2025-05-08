# 🎙️ Voice Desktop Assistant

A powerful voice-controlled desktop assistant that helps you manage your calendar, search files, and control your computer using natural language commands. Built with Python and powered by OpenAI's GPT-4.

## ✨ Features

- **🎯 Voice Command Recognition**
  - Natural language processing
  - Accent-friendly speech recognition
  - Real-time command processing

- **📅 Calendar Management**
  - Schedule meetings with natural language
  - Check upcoming events
  - Smart date/time parsing
  - Timezone-aware scheduling

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

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Google Cloud account (for Speech-to-Text)
- OpenAI API key
- Google Calendar API credentials

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/voice-desktop-assistant.git
   cd voice-desktop-assistant
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables in `.env`:
   ```
   OPENAI_API_KEY=your_openai_api_key
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
   TARGET_CALENDAR_EMAIL=your_calendar_email
   ```

### Usage

1. Start the assistant:
   ```bash
   python server/main.py
   ```

2. Speak your commands naturally:
   - "Schedule a meeting with John next Friday at 5:30 PM"
   - "Find my resume file"
   - "What's on my calendar tomorrow?"
   - "Search for files containing 'project'"

## 🛠️ Command Types

### Calendar Commands
- Schedule meetings: "Schedule a meeting with [person] on [date] at [time]"
- Check calendar: "What's on my calendar [timeframe]?"
- Add events: "Add [event] to my calendar"

### File Search Commands
- Search files: "Find files containing [keyword]"
- Recent files: "Show me my recent [file type]"

## 🔧 Configuration

### Speech Recognition
- Adjustable energy threshold
- Dynamic noise adjustment
- Customizable command words
- Accent-friendly settings

### Calendar Settings
- Timezone configuration
- Default meeting duration
- Calendar sharing preferences

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4
- Google Cloud for Speech-to-Text
- Python SpeechRecognition library
- All contributors and users

## 📞 Support

For support, please open an issue in the GitHub repository or contact the maintainers.
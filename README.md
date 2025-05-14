# 🎙️ Voice Desktop Assistant

A sophisticated voice-controlled desktop assistant leveraging GPT-4 and modern AI technologies for natural language interaction with your digital workspace.

## 🛠️ Tech Stack

### Core Technologies
- **Backend**: FastAPI, Python 3.12, OpenAI GPT-4, Pinecone Vector DB
- **Frontend**: Electron.js, WebSocket, Web Audio API
- **Cloud Services**: Google Speech-to-Text, Google Text-to-Speech, Calendar API, Gmail API
- **AI/ML**: GPT-4, OpenAI Embeddings, RAG Architecture

## ✨ Key Features

### 🧠 AI & Memory
- GPT-4 powered natural language understanding
- Pinecone vector database for semantic memory
- RAG-based context retrieval and response generation
- Persistent conversation history with semantic search

### 🎯 Core Capabilities
- **Voice Processing**: Real-time audio streaming, noise suppression, 44.1kHz/16-bit capture
- **Email Management**: Send, draft, and search emails with natural language
- **Calendar Control**: Schedule meetings, check events, smart date parsing
- **File Search**: Fast semantic search across local files
- **Memory System**: Long-term conversation storage with vector embeddings

## 🔧 Architecture

```
├── Server
│   ├── API Layer (FastAPI + WebSocket)
│   ├── LLM Layer (GPT-4 + Embeddings)
│   ├── Memory Layer (Pinecone)
│   ├── Tools Layer (Calendar, Email, Files)
│   └── Context Layer
└── Client
    ├── Audio Processing
    ├── WebSocket Communication
    └── UI Components
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+, Node.js 18+
- API Keys: OpenAI, Google Cloud, Pinecone
- OAuth2 credentials for Google services

### Installation
```bash
# Clone and setup
git clone https://github.com/yourusername/voice-desktop-assistant.git
cd voice-desktop-assistant

# Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r server/requirements.txt

# Frontend
cd client && npm install

# Configure .env with API keys
```

### Running
```bash
# Start backend
python start_server.py

# Start frontend
npm start
```

## 🎮 Example Commands

### Email
- "Check my recent important emails"
- "Send an email to john@example.com about the meeting"
- "Draft an email about the project update"

### Calendar
- "What's on my calendar today?"
- "Schedule a meeting tomorrow at 2 PM"
- "Check my calendar for next week"

### Files
- "Find files containing 'project'"
- "Search for my resume"
- "Show me recent PDF files"

## 🔧 Technical Details

### Memory System
- Vector dimension: 1536 (OpenAI embeddings)
- Similarity metric: Cosine similarity
- Index: Pinecone vector database
- Context: Dynamic retrieval based on relevance

### Audio Processing
- Sample rate: 44.1kHz
- Bit depth: 16-bit
- Channels: Mono
- Features: Noise suppression, echo cancellation

### UI States
- Gray: Idle
- Red: Recording
- Blue: Processing
- Green: Speaking

## 📝 License

MIT License - see [LICENSE](LICENSE)

## 🤝 Contributing

PRs welcome! For major changes, please open an issue first.

## 📞 Support

- Check [Issues](https://github.com/yourusername/voice-desktop-assistant/issues)
- Open a new issue for bugs/features
- Contact for urgent matters
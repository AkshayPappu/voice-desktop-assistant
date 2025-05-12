import os
from pinecone import Pinecone
from datetime import datetime
import json
import uuid
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

class ConversationManager:
    def __init__(self):
        """Initialize the conversation manager with Pinecone"""
        self.api_key = os.getenv('PINECONE_API_KEY')
        self.environment = os.getenv('PINECONE_ENVIRONMENT')
        self.index_name = os.getenv('PINECONE_INDEX_NAME', 'jarvis-conversations')
        
        if not all([self.api_key, self.environment]):
            raise Exception("Pinecone API key and environment must be set in .env file")
            
        # Initialize Pinecone with new API
        self.pc = Pinecone(api_key=self.api_key)
        
        # Create index if it doesn't exist
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,  # OpenAI embedding dimension
                metric="cosine"
            )
            
        self.index = self.pc.Index(self.index_name)
        
        # Initialize OpenAI client for embeddings and chat
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def _generate_chat_title(self, message):
        """Generate a meaningful title for a chat based on the first message"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Generate a short, descriptive title (max 5 words) for a chat based on the first message. The title should capture the main topic or intent."},
                    {"role": "user", "content": f"Generate a title for a chat that starts with: {message}"}
                ],
                max_tokens=20,
                temperature=0.7
            )
            title = response.choices[0].message.content.strip()
            # Clean up the title (remove quotes, etc.)
            title = title.strip('"\'')
            return title
        except Exception as e:
            print(f"Error generating chat title: {str(e)}")
            return f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    def create_chat_session(self, user_id, title=None):
        """
        Create a new chat session
        
        Args:
            user_id (str): User identifier
            title (str, optional): Title for the chat session. If None, will use timestamp
            
        Returns:
            str: Chat session ID
        """
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        if not title:
            title = f"New Chat {timestamp}"
            
        # Create a special vector to represent the chat session
        metadata = {
            "type": "chat_session",
            "user_id": user_id,
            "chat_id": chat_id,
            "title": title,
            "created_at": timestamp,
            "last_updated": timestamp,
            "message_count": 0  # Track number of messages
        }
        
        # Use a generic embedding for chat sessions
        embedding = self._get_embedding("chat session")
        
        # Store the chat session
        self.index.upsert(
            vectors=[(f"session_{chat_id}", embedding, metadata)]
        )
        
        return chat_id

    def store_message(self, chat_id, user_id, query, response, requires_followup=False, followup_context=None):
        """
        Store a message in a chat session
        
        Args:
            chat_id (str): Chat session identifier
            user_id (str): User identifier
            query (str): User's query
            response (str): Assistant's response
            requires_followup (bool): Whether this conversation requires follow-up
            followup_context (dict): Additional context for follow-up questions
        """
        timestamp = datetime.now().isoformat()
        
        # Ensure query and response are strings
        query = str(query) if query is not None else ""
        response = str(response) if response is not None else ""
        
        # Get the chat session to check message count
        chat_results = self.index.query(
            vector=self._get_embedding("chat session"),
            filter={"chat_id": chat_id, "type": "chat_session"},
            top_k=1,
            include_metadata=True
        )
        
        if not chat_results.matches:
            raise Exception("Chat session not found")
            
        chat_metadata = chat_results.matches[0].metadata
        message_count = chat_metadata.get("message_count", 0)
        
        # If this is the first message, generate a title
        if message_count == 0 and query:
            new_title = self._generate_chat_title(query)
            chat_metadata["title"] = new_title
            # Update chat session with new title
            self.index.upsert(
                vectors=[(f"session_{chat_id}", self._get_embedding("chat session"), chat_metadata)]
            )
        
        # Create metadata with proper type handling
        metadata = {
            "type": "message",
            "chat_id": chat_id,
            "user_id": user_id,
            "timestamp": timestamp,
            "query": query,
            "response": response,
            "requires_followup": str(requires_followup),
            "followup_context": json.dumps(followup_context) if followup_context else "{}",
            "message_index": message_count  # Add message index for ordering
        }
        
        # Generate a unique ID for this message
        message_id = f"msg_{chat_id}_{timestamp}"
        
        # Get embedding for the query or response, whichever is not empty
        text_for_embedding = query if query else response
        if not text_for_embedding:
            text_for_embedding = "empty message"
            
        embedding = self._get_embedding(text_for_embedding)
        
        # Store the message
        self.index.upsert(
            vectors=[(message_id, embedding, metadata)]
        )
        
        # Update the chat session's last_updated timestamp and message count
        chat_metadata["last_updated"] = timestamp
        chat_metadata["message_count"] = message_count + 1
        self.index.upsert(
            vectors=[(f"session_{chat_id}", self._get_embedding("chat session"), chat_metadata)]
        )

    def get_chat_messages(self, chat_id, limit=100):
        """
        Get all messages in a chat session
        
        Args:
            chat_id (str): Chat session identifier
            limit (int): Maximum number of messages to retrieve
            
        Returns:
            list: Messages in chronological order
        """
        # Query for messages in this chat session
        results = self.index.query(
            vector=self._get_embedding("message"),
            filter={"chat_id": chat_id, "type": "message"},
            top_k=limit,
            include_metadata=True
        )
        
        # Format and sort messages
        messages = []
        for match in results.matches:
            metadata = match.metadata
            try:
                metadata["followup_context"] = json.loads(metadata["followup_context"])
            except json.JSONDecodeError:
                metadata["followup_context"] = {}
            metadata["requires_followup"] = metadata["requires_followup"] == "True"
            messages.append(metadata)
            
        # Sort by message_index to ensure proper order
        messages.sort(key=lambda x: x.get("message_index", 0))
        return messages

    def list_chat_sessions(self, user_id, limit=50):
        """
        List all chat sessions for a user
        
        Args:
            user_id (str): User identifier
            limit (int): Maximum number of chat sessions to retrieve
            
        Returns:
            list: Chat sessions sorted by last_updated
        """
        # Query for chat sessions
        results = self.index.query(
            vector=self._get_embedding("chat session"),
            filter={"user_id": user_id, "type": "chat_session"},
            top_k=limit,
            include_metadata=True
        )
        
        # Format and sort sessions
        sessions = []
        for match in results.matches:
            metadata = match.metadata
            # Ensure title is not "New Chat" if there are messages
            if metadata.get("message_count", 0) > 0 and metadata.get("title", "").startswith("New Chat"):
                # Generate a title based on the first message
                first_message = self.get_chat_messages(metadata["chat_id"], limit=1)
                if first_message and first_message[0].get("query"):
                    metadata["title"] = self._generate_chat_title(first_message[0]["query"])
            sessions.append(metadata)
            
        # Sort by last_updated in reverse order (newest first)
        sessions.sort(key=lambda x: x["last_updated"], reverse=True)
        return sessions

    def delete_chat_session(self, chat_id):
        """
        Delete a chat session and all its messages
        
        Args:
            chat_id (str): Chat session identifier
        """
        # Delete all vectors associated with this chat session
        self.index.delete(filter={"chat_id": chat_id})

    def _get_embedding(self, text):
        """
        Get embedding for text using OpenAI's text-embedding-3-small model
        
        Args:
            text (str): Text to get embedding for
            
        Returns:
            list: Embedding vector
        """
        # Ensure text is not empty
        if not text or not isinstance(text, str):
            text = "empty message"  # Use a default value for empty or invalid text
            
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
        
    def store_conversation(self, user_id, query, response, requires_followup=False, followup_context=None):
        """
        Store a conversation turn in Pinecone
        
        Args:
            user_id (str): Unique identifier for the user
            query (str): User's query
            response (str): Assistant's response
            requires_followup (bool): Whether this conversation requires follow-up
            followup_context (dict): Additional context for follow-up questions
        """
        timestamp = datetime.now().isoformat()
        
        # Create metadata with proper type handling
        metadata = {
            "user_id": user_id,
            "timestamp": timestamp,
            "query": query,
            "response": response,
            "requires_followup": str(requires_followup),  # Convert to string
            "followup_context": json.dumps(followup_context) if followup_context else "{}"  # Always store as string
        }
        
        # Generate a unique ID for this conversation turn
        vector_id = f"{user_id}_{timestamp}"
        
        # Get embedding for the query
        embedding = self._get_embedding(query)
        
        # Store in Pinecone with the actual embedding
        self.index.upsert(
            vectors=[(vector_id, embedding, metadata)]
        )
        
    def get_recent_context(self, user_id, limit=5):
        """
        Get recent conversation context for a user
        
        Args:
            user_id (str): User identifier
            limit (int): Number of recent conversations to retrieve
            
        Returns:
            list: Recent conversation turns
        """
        # Get embedding for a generic query to find recent conversations
        # We use a simple query to get the most recent conversations
        embedding = self._get_embedding("recent conversation")
        
        # Query Pinecone for recent conversations
        results = self.index.query(
            vector=embedding,
            filter={"user_id": user_id},
            top_k=limit,
            include_metadata=True
        )
        
        # Format and return the results
        conversations = []
        for match in results.matches:
            metadata = match.metadata
            # Parse followup_context from string back to dict
            try:
                metadata["followup_context"] = json.loads(metadata["followup_context"])
            except json.JSONDecodeError:
                metadata["followup_context"] = {}
            # Convert requires_followup back to boolean
            metadata["requires_followup"] = metadata["requires_followup"] == "True"
            conversations.append(metadata)
            
        return conversations
        
    def clear_context(self, user_id):
        """
        Clear conversation context for a user
        
        Args:
            user_id (str): User identifier
        """
        # Delete all vectors for this user
        self.index.delete(filter={"user_id": user_id}) 
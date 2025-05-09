import os
from pinecone import Pinecone
from datetime import datetime
import json
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
        
        # Initialize OpenAI client for embeddings
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def _get_embedding(self, text):
        """
        Get embedding for text using OpenAI's text-embedding-3-small model
        
        Args:
            text (str): Text to get embedding for
            
        Returns:
            list: Embedding vector
        """
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
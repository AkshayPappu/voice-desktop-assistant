import os
import sys
from pathlib import Path
import uuid
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import speech_recognition as sr
import json
import asyncio
from google.cloud import speech
import io
from datetime import datetime

# Add the server directory to Python path
server_dir = Path(__file__).parent
os.chdir(server_dir)  # Change to server directory
sys.path.append(str(server_dir))

from llm.llm_handler import process_with_llm
from tools.command_executor import execute_command
from tools.followup_handler import handle_followup
from context.conversation_manager import ConversationManager
from tools.email_handler import EmailHandler
from voice.tts_speaker import speak_text

app = FastAPI()

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for WebSocket
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
recognizer = sr.Recognizer()
client = speech.SpeechClient()
conversation_manager = ConversationManager()
email_handler = EmailHandler()

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}
active_text_connections: Dict[str, WebSocket] = {}  # New dict for text connections

# Models
class ChatSession(BaseModel):
    user_id: str
    title: Optional[str] = None

class Message(BaseModel):
    chat_id: str
    user_id: str
    content: str
    type: str  # 'user' or 'assistant'

class CommandRequest(BaseModel):
    text: str
    user_id: Optional[str] = None

class CommandResponse(BaseModel):
    command_type: str
    parameters: Dict[str, Any]
    requires_followup: bool
    followup_context: Optional[Dict[str, Any]] = None
    response: Optional[str] = None

# Store active user sessions
active_sessions = {}

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    print("New WebSocket connection request")
    await websocket.accept()
    client_id = str(uuid.uuid4())
    active_connections[client_id] = websocket
    print(f"WebSocket connection accepted for client {client_id}")
    
    try:
        while True:
            try:
                # Receive complete audio data
                print("Waiting for audio data...")
                audio_data = await websocket.receive_bytes()
                print(f"Received complete audio data: {len(audio_data)} bytes")
                
                if len(audio_data) == 0:
                    print("Received empty audio data")
                    await websocket.send_json({
                        "type": "error",
                        "error": "No audio data received"
                    })
                    continue
                
                # The audio data is already in LINEAR16 format (16-bit PCM)
                audio = speech.RecognitionAudio(content=audio_data)
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=44100,
                    language_code="en-US",
                    enable_automatic_punctuation=True,
                    model="default",
                    use_enhanced=True,
                    audio_channel_count=1,
                )
                
                try:
                    # Perform the transcription
                    print("Sending audio to Google Speech-to-Text...")
                    response = client.recognize(config=config, audio=audio)
                    print("Received response from Google Speech-to-Text")
                    
                    if response.results:
                        transcript = response.results[0].alternatives[0].transcript
                        print(f"Transcription: {transcript}")
                        
                        # Immediately send the transcription
                        transcription_response = {
                            "type": "transcription",
                            "transcription": transcript
                        }
                        print(f"Sending transcription response: {transcription_response}")
                        await websocket.send_json(transcription_response)
                        
                        # Process the transcribed text with LLM
                        print("Processing with LLM...")
                        command_data = process_with_llm(transcript, client_id)
                        
                        if command_data:
                            print("Command processed successfully")
                            # Execute the command and get the formatted response
                            formatted_response = execute_command(command_data)
                            
                            # Update command_data with the formatted response
                            command_data["response"] = formatted_response
                            
                            # Send the JARVIS response
                            jarvis_response = {
                                "type": "jarvis",
                                "command_data": command_data,
                                "response": formatted_response  # Add response at the top level as well
                            }
                            print(f"Sending JARVIS response to client: {jarvis_response}")
                            await websocket.send_json(jarvis_response)
                        else:
                            print("Failed to process command")
                            error_response = {
                                "type": "jarvis",
                                "error": "Could not process command"
                            }
                            print(f"Sending error response: {error_response}")
                            await websocket.send_json(error_response)
                    else:
                        print("No speech detected in audio")
                        await websocket.send_json({
                            "type": "transcription",
                            "transcription": "",
                            "error": "No speech detected"
                        })
                        
                except Exception as e:
                    print(f"Error processing audio: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "error": f"Error processing audio: {str(e)}"
                    })
                    
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for client {client_id}")
                break
            except Exception as e:
                print(f"Error in WebSocket connection: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "error": f"Server error: {str(e)}"
                })
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for client {client_id}")
    except Exception as e:
        print(f"Error in WebSocket connection: {str(e)}")
    finally:
        if client_id in active_connections:
            del active_connections[client_id]
            print(f"Cleaned up connection for client {client_id}")

@app.websocket("/ws/text")
async def text_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for handling text-based follow-up responses."""
    await websocket.accept()
    print("New text WebSocket connection request")
    client_id = str(uuid.uuid4())
    print(f"Text WebSocket connection accepted for client {client_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received text data: {data}")
            
            try:
                message = json.loads(data)
                if message.get("type") != "followup_response":
                    await websocket.send_json({
                        "type": "error",
                        "error": "Invalid message type. Expected followup_response."
                    })
                    continue
                
                # Get context from the client message
                current_context = message.get("context")
                print(f"Received context from client: {current_context}")
                
                if not current_context:
                    await websocket.send_json({
                        "type": "error",
                        "error": "No context provided. Please try the command again."
                    })
                    continue
                
                # Validate command type
                if current_context.get("command_type") not in ["email_send", "email_draft"]:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Invalid command type for text follow-up."
                    })
                    continue
                
                # Process email address
                email_address = message.get("response", "").strip()
                if message.get("cancelled", False):
                    print("Email cancelled by user")
                    await websocket.send_json({
                        "type": "jarvis",
                        "response": "Email cancelled.",
                        "command_data": current_context
                    })
                    continue
                
                print(f"Processing email address: {email_address}")
                
                # Basic email validation
                if not email_address or "@" not in email_address:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Invalid email address format. Please provide a valid email address."
                    })
                    continue
                
                # Update the context with the email address
                current_context["parameters"]["to"] = email_address
                
                try:
                    # Execute the email command using the global email_handler
                    if current_context["command_type"] == "email_send":
                        result = email_handler.send_email(
                            to=email_address,
                            subject=current_context["parameters"]["subject"],
                            body=current_context["parameters"]["body"]
                        )
                        if result:
                            print(f"Email sent successfully to {email_address}")
                            response_text = f"I've sent your email to {email_address} with the subject '{current_context['parameters']['subject']}'. The email has been delivered successfully."
                            # Speak the response
                            speak_text(response_text)
                            await websocket.send_json({
                                "type": "jarvis",
                                "response": response_text,
                                "command_data": {
                                    **current_context,
                                    "response": response_text
                                }
                            })
                        else:
                            print(f"Failed to send email to {email_address}")
                            error_text = "I apologize, but I couldn't send the email. Please check your Gmail authentication and try again."
                            # Speak the error
                            speak_text(error_text)
                            await websocket.send_json({
                                "type": "error",
                                "error": error_text,
                                "command_data": {
                                    **current_context,
                                    "response": error_text
                                }
                            })
                    else:  # email_draft
                        result = email_handler.draft_email(
                            to=email_address,
                            subject=current_context["parameters"]["subject"],
                            body=current_context["parameters"]["body"]
                        )
                        if result:
                            print(f"Email draft created successfully for {email_address}")
                            response_text = f"I've created a draft email to {email_address} with the subject '{current_context['parameters']['subject']}'. You can find it in your Gmail drafts folder."
                            # Speak the response
                            speak_text(response_text)
                            await websocket.send_json({
                                "type": "jarvis",
                                "response": response_text,
                                "command_data": {
                                    **current_context,
                                    "response": response_text
                                }
                            })
                        else:
                            print(f"Failed to create email draft for {email_address}")
                            error_text = "I apologize, but I couldn't create the email draft. Please check your Gmail authentication and try again."
                            # Speak the error
                            speak_text(error_text)
                            await websocket.send_json({
                                "type": "error",
                                "error": error_text,
                                "command_data": {
                                    **current_context,
                                    "response": error_text
                                }
                            })
                
                except Exception as e:
                    print(f"Error executing email command: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "error": f"Error processing email: {str(e)}"
                    })
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "error": "Invalid JSON message format."
                })
            except Exception as e:
                print(f"Error processing message: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "error": f"Error processing message: {str(e)}"
                })
                
    except WebSocketDisconnect:
        print(f"Text WebSocket disconnected for client {client_id}")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        try:
            await websocket.close()
        except:
            pass

@app.post("/api/process-command", response_model=CommandResponse)
async def process_command(request: CommandRequest):
    if not request.user_id:
        request.user_id = str(uuid.uuid4())
    
    # Process the command using existing LLM handler
    command_data = process_with_llm(request.text, request.user_id)
    if not command_data:
        raise HTTPException(status_code=400, detail="Could not process command")
    
    # Execute the command
    response = execute_command(command_data)
    command_data["response"] = response
    
    # Store session data if follow-up is required
    if command_data.get("requires_followup"):
        active_sessions[request.user_id] = command_data
    
    return command_data

@app.post("/api/handle-followup", response_model=CommandResponse)
async def handle_command_followup(request: CommandRequest):
    if not request.user_id or request.user_id not in active_sessions:
        raise HTTPException(status_code=400, detail="No active session found")
    
    command_data = active_sessions[request.user_id]
    success = handle_followup(command_data, request.user_id, request.text)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to handle follow-up")
    
    # Clean up session if no more follow-up is needed
    if not command_data.get("requires_followup"):
        del active_sessions[request.user_id]
    
    return command_data

@app.post("/api/create-chat")
async def create_chat(chat: ChatSession):
    """Create a new chat session"""
    try:
        chat_id = conversation_manager.create_chat_session(
            user_id=chat.user_id,
            title=chat.title
        )
        return {"chat_id": chat_id, "title": chat.title or f"Chat {datetime.now().isoformat()}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/list-chats")
async def list_chats(user_id: str):
    """List all chat sessions for a user"""
    try:
        chats = conversation_manager.list_chat_sessions(user_id)
        return chats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get-chat/{chat_id}")
async def get_chat(chat_id: str):
    """Get chat session details"""
    try:
        # Query for the chat session
        results = conversation_manager.index.query(
            vector=conversation_manager._get_embedding("chat session"),
            filter={"chat_id": chat_id, "type": "chat_session"},
            top_k=1,
            include_metadata=True
        )
        
        if not results.matches:
            raise HTTPException(status_code=404, detail="Chat not found")
            
        return results.matches[0].metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get-chat-messages/{chat_id}")
async def get_chat_messages(chat_id: str):
    """Get all messages in a chat session"""
    try:
        messages = conversation_manager.get_chat_messages(chat_id)
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/store-message")
async def store_message(message: Message):
    """Store a new message in a chat session"""
    try:
        # Validate chat session exists
        chat_results = conversation_manager.index.query(
            vector=conversation_manager._get_embedding("chat session"),
            filter={"chat_id": message.chat_id, "type": "chat_session"},
            top_k=1,
            include_metadata=True
        )
        
        if not chat_results.matches:
            raise HTTPException(status_code=404, detail="Chat session not found")

        # Store the message with proper content handling
        if message.type == 'user':
            # For user messages, store as query
            conversation_manager.store_message(
                chat_id=message.chat_id,
                user_id=message.user_id,
                query=message.content,
                response="",  # Use empty string instead of None
                requires_followup=False
            )
        else:
            # For assistant messages, store as response
            conversation_manager.store_message(
                chat_id=message.chat_id,
                user_id=message.user_id,
                query="",  # Use empty string instead of None
                response=message.content,
                requires_followup=False
            )
        
        return {"status": "success", "message": "Message stored successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error storing message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store message: {str(e)}")

@app.delete("/api/delete-chat/{chat_id}")
async def delete_chat(chat_id: str):
    """Delete a chat session and all its messages"""
    try:
        # First verify the chat exists
        chat_results = conversation_manager.index.query(
            vector=conversation_manager._get_embedding("chat session"),
            filter={"chat_id": chat_id, "type": "chat_session"},
            top_k=1,
            include_metadata=True
        )
        
        if not chat_results.matches:
            raise HTTPException(status_code=404, detail="Chat session not found")
            
        # Delete all vectors associated with this chat session
        conversation_manager.delete_chat_session(chat_id)
        
        return {"status": "success", "message": "Chat deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error deleting chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete chat: {str(e)}") 
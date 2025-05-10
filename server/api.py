import os
import sys
from pathlib import Path
import uuid
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import speech_recognition as sr
import json
import asyncio
from google.cloud import speech
import io

# Add the server directory to Python path
server_dir = Path(__file__).parent
os.chdir(server_dir)  # Change to server directory
sys.path.append(str(server_dir))

from llm.llm_handler import process_with_llm
from tools.command_executor import execute_command
from tools.followup_handler import handle_followup

app = FastAPI()

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for WebSocket
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize speech recognition
recognizer = sr.Recognizer()
client = speech.SpeechClient()

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

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
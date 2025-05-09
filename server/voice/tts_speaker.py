from google.cloud import texttospeech
import os
from dotenv import load_dotenv
import tempfile
import pygame
import time

# Load environment variables
load_dotenv()

def validate_credentials():
    """Validate that Google Cloud credentials are properly set up"""
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path:
        raise Exception("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
    
    if not os.path.exists(credentials_path):
        raise Exception(f"Credentials file not found at: {credentials_path}")

# Validate credentials when module is imported
validate_credentials()

def speak_text(text):
    """
    Convert text to speech using Google Cloud TTS and play it
    
    Args:
        text (str): Text to be spoken
    """
    try:
        # Initialize the TTS client
        client = texttospeech.TextToSpeechClient()
        
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-F",  # Using a neural voice for better quality
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        
        # Select the type of audio file
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,  # Normal speed
            pitch=0.0  # Normal pitch
        )
        
        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_filename = temp_file.name
            temp_file.write(response.audio_content)
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Load and play the audio file
        pygame.mixer.music.load(temp_filename)
        pygame.mixer.music.play()
        
        # Wait for the audio to finish playing
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        # Clean up
        pygame.mixer.quit()
        os.unlink(temp_filename)
        
    except Exception as e:
        print(f"Error in text-to-speech: {str(e)}")
        # Fallback to just printing the text if TTS fails
        print(text) 
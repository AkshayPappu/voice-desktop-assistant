import speech_recognition as sr
import os
from dotenv import load_dotenv
from google.cloud import speech
from google.oauth2 import service_account

# Load environment variables
load_dotenv()

def validate_credentials():
    """Validate that Google Cloud credentials are properly set up"""
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path:
        raise Exception("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
    
    if not os.path.exists(credentials_path):
        raise Exception(f"Credentials file not found at: {credentials_path}")
    
    try:
        # Try to load credentials to validate them
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        return credentials
    except Exception as e:
        raise Exception(f"Failed to load Google Cloud credentials: {e}")

# Validate credentials when module is imported
validate_credentials()

def listen_for_speech():
    """Listen to microphone input and return the recognized text"""
    recognizer = sr.Recognizer()
    
    # Adjust these values based on your needs
    recognizer.energy_threshold = 1000  # Increased threshold to reduce false positives
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.dynamic_energy_ratio = 1.5
    recognizer.pause_threshold = 0.8
    
    with sr.Microphone() as source:
        print("Listening... (Speak now)")
        # Adjust for ambient noise with longer duration
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        print(f"Energy threshold set to: {recognizer.energy_threshold}")
        
        try:
            print("Waiting for speech...")
            # This will wait until speech is detected and then continue until there's a pause
            audio = recognizer.listen(source, 
                                    timeout=None,  # No timeout for initial speech detection
                                    phrase_time_limit=None)  # No limit on phrase length
            print("Speech detected! Processing...")
            
            # Convert audio data to the format expected by Google Cloud Speech
            audio_data = audio.get_raw_data()
            
            # Create a Speech client
            client = speech.SpeechClient()
            
            # Configure the audio and recognition settings
            audio = speech.RecognitionAudio(content=audio_data)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",
                enable_automatic_punctuation=True,
            )
            
            # Perform the transcription
            response = client.recognize(config=config, audio=audio)
            
            # Get the transcription
            if response.results:
                return response.results[0].alternatives[0].transcript
            return None
            
        except sr.WaitTimeoutError:
            print("No speech detected within timeout period")
            return None
        except Exception as e:
            print(f"Error during speech recognition: {e}")
            return None 
from voice.mic_listener import listen_for_speech
from llm.llm_handler import process_with_llm
from tools.command_executor import execute_command
from tools.followup_handler import handle_followup
# We'll add more imports as we create the other components
# from tools.file_search import search_file
import json
import uuid


def main():
    print("Jarvis Desktop Assistant")
    print("----------------------")
    print("Listening for commands...")
    print("Press Ctrl+C to exit")
    
    # Generate a unique user ID for this session
    user_id = str(uuid.uuid4())
    
    try:
        while True:
            # Get voice input
            text = listen_for_speech()
            if text:                
                # Process with LLM
                command_data = process_with_llm(text, user_id)
                if command_data:
                    print(f"\nCommand type: {command_data['command_type']}")
                    print(f"Parameters: {command_data['parameters']}")
                    
                    # Execute the command
                    response = execute_command(command_data)
                    
                    # If follow-up is required, handle it
                    if command_data.get("requires_followup"):
                        handle_followup(command_data, user_id)
                else:
                    print("Could not process command")
                
                print("----------------------")
                
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main() 
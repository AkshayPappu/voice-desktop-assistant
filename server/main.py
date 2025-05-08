from voice.mic_listener import listen_for_speech
from llm.llm_handler import process_with_llm
from tools.command_executor import execute_command
# We'll add more imports as we create the other components
# from tools.file_search import search_file


def main():
    print("Jarvis Desktop Assistant")
    print("----------------------")
    print("Listening for commands...")
    print("Press Ctrl+C to exit")
    
    try:
        while True:
            # Get voice input
            text = listen_for_speech()
            if text:                
                # Process with LLM
                command_data = process_with_llm(text)
                if command_data:
                    print(f"\nCommand type: {command_data['command_type']}")
                    print(f"Parameters: {command_data['parameters']}")
                    
                    # Execute the command
                    execute_command(command_data)
                else:
                    print("Could not process command")
                
                print("----------------------")
                
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main() 
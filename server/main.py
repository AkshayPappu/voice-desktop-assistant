from voice.mic_listener import listen_for_speech
# We'll add more imports as we create the other components
# from llm.llm_handler import process_with_llm
# from tools.command_executor import execute_command

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
                print(f"Command received: {text}")
                
                # TODO: Add LLM processing
                # processed_command = process_with_llm(text)
                
                # TODO: Add command execution
                # execute_command(processed_command)
                
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main() 
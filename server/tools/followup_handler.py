from voice.mic_listener import listen_for_speech
from llm.llm_handler import process_with_llm
from tools.command_executor import execute_command
from llm.response_formatter import format_response
from voice.tts_speaker import speak_text

def handle_followup(command_data, user_id, simulated_response=None):
    """
    Handle follow-up questions based on the context provided by the LLM
    
    Args:
        command_data (dict): The original command data with follow-up context
        user_id (str): User identifier
        simulated_response (str, optional): Simulated user response for testing
        
    Returns:
        bool: True if follow-up was handled successfully, False otherwise
    """
    followup_context = command_data.get("followup_context", {})
    
    # Get the follow-up question from the context
    followup_question = followup_context.get("question", "Please provide more information.")
    print(f"\n{followup_question}")
    
    # Speak the follow-up question
    speak_text(followup_question)
    
    # Get user's response (either simulated or real)
    response_text = simulated_response if simulated_response is not None else listen_for_speech()
    if response_text:
        # For simple responses, directly update the parameter
        if "parameter_to_update" in followup_context:
            param_name = followup_context["parameter_to_update"]
            command_data["parameters"][param_name] = response_text
            
            # Execute the updated command
            execute_command(command_data)
            return True
            
        # For more complex responses, process with LLM
        followup_data = process_with_llm(response_text, user_id)
        if followup_data:
            # Update the original command with the new information
            if "parameter_to_update" in followup_context:
                param_name = followup_context["parameter_to_update"]
                command_data["parameters"][param_name] = followup_data.get("value")
            
            # Execute the updated command
            execute_command(command_data)
            return True
    return False 
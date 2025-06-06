import os
from dotenv import load_dotenv
from openai import OpenAI
import json
from context.conversation_manager import ConversationManager
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize conversation manager
conversation_manager = ConversationManager()

def process_with_llm(text, user_id="default_user"):
    """
    Process the recognized speech text with OpenAI to understand the command
    and determine the appropriate action.
    
    Args:
        text (str): The recognized speech text
        user_id (str): Unique identifier for the user
        
    Returns:
        dict: A dictionary containing the command type, parameters, and follow-up information
    """
    print(f"\nProcessing command: {text}")
    
    # Get recent conversation context
    recent_context = conversation_manager.get_recent_context(user_id)
    print(f"Recent context: {recent_context}")
    
    # Define the system message that sets up the context and expected output format
    system_message = """You are a command processor for a desktop assistant. 
    Your job is to understand user commands and output them in a structured format.
    For email commands (email_send or email_draft), you MUST include both subject and body in the parameters.
    If the user doesn't specify a subject or body, use appropriate defaults:
    - For subject: "No Subject" or generate a subject based on the context
    - For body: "" (empty string) or generate a brief body based on the context
    
    The output should be a JSON object with the following structure:
    {
        "command_type": one of ["search_store", "calendar_check", "calendar_add", "open_app", "search_file", "general_question", "email_check", "email_send", "email_draft"],
        "parameters": {
            // For specific command types:
            // search_store: {"query": "search term"}
            // calendar_check: {
            //     "date": "YYYY-MM-DD" for specific dates, or
            //     "timeframe": "today/tomorrow/this_week" for common timeframes, or
            //     "start_date": "YYYY-MM-DD",
            //     "end_date": "YYYY-MM-DD" for custom date ranges
            // }
            // calendar_add: {
            //     "title": "event title",
            //     "date": "natural language date (e.g., 'next Friday', 'tomorrow', 'next week')",
            //     "time": "time in 24h format (e.g., '17:30') or 12h format (e.g., '5:30 PM')"
            // }
            // open_app: {"app_name": "application name"}
            // search_file: {"filename": "file name to search"}
            // email_check: {"days_back": number, "important_only": boolean, "max_results": number}
            // email_send: {"to": "email", "subject": "subject", "body": "content"}
            // email_draft: {"to": "email", "subject": "subject", "body": "content"}
            
            // For general_question:
            // {
            //     "response": "The direct response to the user's question",
            //     "requires_followup": boolean,
            //     "followup_context": {
            //         "question": "Follow-up question if needed",
            //         "context": "Additional context for follow-up"
            //     }
            // }
        },
        "requires_followup": boolean,
        "followup_context": {
            // When requires_followup is true, include:
            "question": "The specific question to ask the user",
            "parameter_to_update": "The parameter name that will be updated with the user's response",
            // Optional additional context that might be needed for the follow-up
            "context": {
                // Any additional information needed for processing the follow-up
            }
        }
    }
    
    For general questions that don't fit into specific command types, use the "general_question" command type.
    In this case, you should:
    1. Analyze if the user's input is a general question or requires a specific tool
    2. If it's a general question, use "general_question" command type and provide a direct response
    3. If it requires a specific tool, use the appropriate command type
    
    Examples:
    1. For a general question:
       {
         "command_type": "general_question",
         "parameters": {
           "response": "The capital of France is Paris. It's known for landmarks like the Eiffel Tower and the Louvre Museum."
         },
         "requires_followup": false
       }
    
    2. For a question that needs follow-up:
       {
         "command_type": "general_question",
         "parameters": {
           "response": "I can help you learn about that topic. Would you like to know about its history, current state, or future developments?",
           "requires_followup": true,
           "followup_context": {
             "question": "Which aspect would you like to explore further?",
             "context": {
               "options": ["history", "current state", "future developments"]
             }
           }
         },
         "requires_followup": true,
         "followup_context": {
           "question": "Which aspect would you like to explore further?",
           "parameter_to_update": "aspect",
           "context": {
             "options": ["history", "current state", "future developments"]
           }
         }
       }
    
    // ... existing examples for other command types ...
    
    Only output valid JSON, no other text."""
    
    # Prepare conversation history for context
    conversation_history = []
    for turn in recent_context:
        conversation_history.append({
            "role": "user",
            "content": turn["query"]
        })
        conversation_history.append({
            "role": "assistant",
            "content": turn["response"]
        })
    
    try:
        # Call OpenAI API with GPT-4
        response = client.chat.completions.create(
            model="gpt-4o",  # Changed from gpt-4-turbo-preview to gpt-4
            messages=[
                {"role": "system", "content": system_message},
                *conversation_history,
                {"role": "user", "content": text}
            ],
            temperature=0.2,  # Slightly lowered temperature for more consistent outputs with GPT-4
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        command_data = json.loads(response.choices[0].message.content)
        print(f"Parsed command data: {command_data}")
        
        # Validate the command structure
        valid_commands = ["search_store", "calendar_check", "calendar_add", "open_app", "search_file", "general_question", "email_check", "email_send", "email_draft"]
        if command_data.get("command_type") not in valid_commands:
            raise ValueError(f"Invalid command type: {command_data.get('command_type')}")
        
        # For email commands, ensure parameters are properly set
        if command_data["command_type"] in ["email_send", "email_draft"]:
            print("Processing email command, validating parameters")
            if "parameters" not in command_data:
                command_data["parameters"] = {}
            
            # Ensure subject and body are present
            if "subject" not in command_data["parameters"]:
                command_data["parameters"]["subject"] = "No Subject"
            if "body" not in command_data["parameters"]:
                command_data["parameters"]["body"] = ""
                
            print(f"Email command parameters after validation: {command_data['parameters']}")
            
            # Set up follow-up context
            command_data["requires_followup"] = True
            command_data["followup_context"] = {
                "question": "What email address should I send this to?",
                "parameter_to_update": "to",
                "context": {
                    "type": "email_input",
                    "current_draft": {
                        "subject": command_data["parameters"]["subject"],
                        "body": command_data["parameters"]["body"]
                    }
                }
            }
            print(f"Set up email follow-up context: {command_data['followup_context']}")
        
        # For general questions, extract the response from parameters
        if command_data["command_type"] == "general_question":
            command_data["response"] = command_data["parameters"].get("response", "")
        
        # Store the conversation turn
        conversation_manager.store_conversation(
            user_id=user_id,
            query=text,
            response=json.dumps(command_data),
            requires_followup=command_data.get("requires_followup", False),
            followup_context=command_data.get("followup_context")
        )
        
        # If the command requires follow-up, store the context
        if command_data.get("requires_followup"):
            print(f"Setting current context for follow-up: {command_data}")
            conversation_manager.set_current_context(command_data)
            # Verify context was set
            current_context = conversation_manager.get_current_context()
            print(f"Verified current context: {current_context}")
        else:
            print("No follow-up required, clearing context")
            conversation_manager.clear_current_context()
            
        return command_data
        
    except Exception as e:
        print(f"Error processing command: {str(e)}")
        conversation_manager.clear_current_context()  # Clear context on error
        return None
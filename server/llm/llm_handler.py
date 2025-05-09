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
    # Get recent conversation context
    recent_context = conversation_manager.get_recent_context(user_id)
    
    # Define the system message that sets up the context and expected output format
    system_message = """You are a command processor for a desktop assistant. 
    Your job is to understand user commands and output them in a structured format.
    The output should be a JSON object with the following structure:
    {
        "command_type": one of ["search_store", "calendar_check", "calendar_add", "open_app", "search_file"],
        "parameters": {
            // Parameters specific to each command type
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
        },
        "requires_followup": boolean,
        "followup_context": {
            // When requires_followup is true, include:
            "question": "The specific question to ask the user",
            "parameter_to_update": "The parameter name that will be updated with the user's response",
            // Optional additional context that might be needed for the follow-up
            "context": {
                // Any additional information needed for processing the follow-up
                // For example, available times, suggested options, etc.
            }
        }
    }
    
    Examples:
    1. When checking calendar events:
       a. For specific date:
       {
         "command_type": "calendar_check",
         "parameters": {
           "date": "2024-03-20"
         },
         "requires_followup": false
       }
       
       b. For common timeframe:
       {
         "command_type": "calendar_check",
         "parameters": {
           "timeframe": "today"
         },
         "requires_followup": false
       }
       
       c. For custom date range:
       {
         "command_type": "calendar_check",
         "parameters": {
           "start_date": "2024-03-20",
           "end_date": "2024-04-20"
         },
         "requires_followup": false
       }
    
    2. When scheduling a meeting without a specific time:
       {
         "command_type": "calendar_add",
         "parameters": {
           "title": "Team Meeting",
           "date": "next Friday"
         },
         "requires_followup": true,
         "followup_context": {
           "question": "I found these available times for next Friday: 9:00 AM, 10:30 AM, and 2:00 PM. Which time works best for you?",
           "parameter_to_update": "time",
           "context": {
             "available_times": ["9:00 AM", "10:30 AM", "2:00 PM"]
           }
         }
       }
    
    3. When searching for a file without a specific name:
       {
         "command_type": "search_file",
         "parameters": {},
         "requires_followup": true,
         "followup_context": {
           "question": "What type of file are you looking for? (e.g., document, spreadsheet, image)",
           "parameter_to_update": "file_type",
           "context": {
             "suggested_types": ["document", "spreadsheet", "image", "presentation"]
           }
         }
       }
    
    For calendar_check, you should:
    1. Use "date" for specific dates (e.g., "March 20th", "next Friday")
    2. Use "timeframe" for common timeframes (today, tomorrow, this week)
    3. Use "start_date" and "end_date" for custom ranges (e.g., "next 30 days", "next month")
    
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
            model="gpt-4-turbo-preview",  # Using GPT-4
            messages=[
                {"role": "system", "content": system_message},
                *conversation_history,
                {"role": "user", "content": text}
            ],
            temperature=0.3,  # Lower temperature for more consistent outputs
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        command_data = json.loads(response.choices[0].message.content)
        
        # Validate the command structure
        valid_commands = ["search_store", "calendar_check", "calendar_add", "open_app", "search_file"]
        if command_data.get("command_type") not in valid_commands:
            raise ValueError(f"Invalid command type: {command_data.get('command_type')}")
        
        # Store the conversation turn
        conversation_manager.store_conversation(
            user_id=user_id,
            query=text,
            response=json.dumps(command_data),
            requires_followup=command_data.get("requires_followup", False),
            followup_context=command_data.get("followup_context")
        )
            
        return command_data
        
    except Exception as e:
        print(f"Error processing command: {str(e)}")
        return None
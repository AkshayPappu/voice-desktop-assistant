import os
from dotenv import load_dotenv
from openai import OpenAI
import json

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def process_with_llm(text):
    """
    Process the recognized speech text with OpenAI to understand the command
    and determine the appropriate action.
    
    Args:
        text (str): The recognized speech text
        
    Returns:
        dict: A dictionary containing the command type and parameters
    """
    # Define the system message that sets up the context and expected output format
    system_message = """You are a command processor for a desktop assistant. 
    Your job is to understand user commands and output them in a structured format.
    The output should be a JSON object with the following structure:
    {
        "command_type": one of ["search_store", "calendar_check", "calendar_add", "open_app", "search_file"],
        "parameters": {
            // Parameters specific to each command type
            // search_store: {"query": "search term"}
            // calendar_check: {"date": "YYYY-MM-DD"} or {"timeframe": "today/tomorrow/this_week"}
            // calendar_add: {
            //     "title": "event title",
            //     "date": "natural language date (e.g., 'next Friday', 'tomorrow', 'next week')",
            //     "time": "time in 24h format (e.g., '17:30') or 12h format (e.g., '5:30 PM')"
            // }
            // open_app: {"app_name": "application name"}
            // search_file: {"filename": "file name to search"}
        }
    }
    For calendar_add, always use natural language for dates and separate time parameter.
    Examples:
    - "Schedule a meeting with John next Friday at 5:30 PM" should output:
      {
        "command_type": "calendar_add",
        "parameters": {
          "title": "Meeting with John",
          "date": "next Friday",
          "time": "17:30"
        }
      }
    - "Add a team sync tomorrow at 2 PM" should output:
      {
        "command_type": "calendar_add",
        "parameters": {
          "title": "Team Sync",
          "date": "tomorrow",
          "time": "14:00"
        }
      }
    Only output valid JSON, no other text."""

    try:
        # Call OpenAI API with GPT-4
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",  # Using GPT-4
            messages=[
                {"role": "system", "content": system_message},
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
            
        return command_data
        
    except Exception as e:
        print(f"Error processing command: {str(e)}")
        return None
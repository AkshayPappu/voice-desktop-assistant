from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def format_response(command_type, raw_output):
    """
    Format raw command output into natural language response
    
    Args:
        command_type (str): Type of command that was executed
        raw_output (dict): Raw output from command execution
        
    Returns:
        str: Natural language response
    """
    system_message = """You are a helpful voice assistant. Your job is to convert raw command outputs into natural, conversational responses.
    The response should be:
    1. Concise and to the point
    2. Easy to say out loud
    3. Focus only on the most relevant information
    4. Use natural, conversational language
    5. Avoid technical details unless specifically requested
    
    For example:
    - Instead of "Found 2 files: File1.pdf (2MB, modified 2024-03-20) and File2.pdf (1MB, modified 2024-03-19)"
    - Say "I found two PDF files: File1 and File2"
    
    - Instead of "Event: Team Meeting, Start: 2024-03-20T14:00:00Z, End: 2024-03-20T15:00:00Z, Location: Conference Room A"
    - Say "You have a Team Meeting at 2 PM in Conference Room A"
    """
    
    # Format the raw output into a string for the LLM
    output_str = str(raw_output)
    
    # Add context based on command type
    if command_type == "calendar_check":
        context = "The user asked about their calendar events. Focus on event names, times, and locations only. "
    elif command_type == "search_file":
        context = "The user searched for files. Focus on file names and types only, ignore technical details like size and modification dates. "
    elif command_type == "calendar_add":
        context = "The user added a calendar event. Confirm the event details in a natural way. "
    else:
        context = ""
    
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"{context}Convert this output into a natural, concise response: {output_str}"}
            ],
            temperature=0.7  # Slightly higher temperature for more natural responses
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error formatting response: {str(e)}")
        return "I've processed your request, but I'm having trouble formatting the response." 
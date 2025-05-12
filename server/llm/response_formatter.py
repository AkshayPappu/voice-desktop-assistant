from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def format_response(command_type, raw_output):
    """
    Format the raw command output into a natural language response
    
    Args:
        command_type (str): Type of command that was executed
        raw_output (dict): Raw output from command execution
        
    Returns:
        str: Formatted natural language response
    """
    if isinstance(raw_output, dict) and raw_output.get('error'):
        return raw_output['error']

    if command_type == "email_check":
        emails = raw_output.get("emails", [])
        if not emails:
            return "No emails found in that time period."
            
        count = len(emails)
        days = raw_output.get('days_back', 7)
        important = raw_output.get('important_only', False)
        
        # Start with a conversational summary
        summary = f"Found {count} {'important ' if important else ''}emails from the last {days} days:\n\n"
        
        # Add brief summaries of each email
        for email in emails:
            # Extract just the name from the sender field (remove email address)
            sender = email['sender'].split('<')[0].strip()
            # Clean up the subject and snippet
            subject = email['subject'].replace('\n', ' ').strip()
            snippet = email['snippet'].replace('\n', ' ').strip()
            # Format date nicely
            date = email['date'].split('+')[0].strip()  # Remove timezone
            
            summary += f"• {sender} sent '{subject}'\n"
            
        return summary
        
    elif command_type == "email_send":
        if raw_output and raw_output.get('id'):
            return f"Email sent successfully to {raw_output['message']['to']}!"
        return "Failed to send email. Please try again."
        
    elif command_type == "email_draft":
        if raw_output and raw_output.get('id'):
            return f"Email draft created for {raw_output['message']['to']}. You can review and send it from your Gmail drafts."
        return "Failed to create email draft. Please try again."
        
    elif command_type == "calendar_check":
        events = raw_output.get("events", [])
        timeframe = raw_output.get("timeframe", "specified time")
        
        if not events:
            return f"I found no events scheduled for {timeframe}."
            
        response = f"Here are your events for {timeframe}:\n\n"
        for event in events:
            response += f"• {event['summary']}\n"
            if 'start' in event:
                response += f"  Time: {event['start']}\n"
            if 'location' in event:
                response += f"  Location: {event['location']}\n"
            response += "\n"
        return response
        
    elif command_type == "calendar_add":
        event = raw_output.get("event", {})
        if raw_output.get("status") == "success":
            return f"I've added the event '{event.get('summary')}' to your calendar."
        return "I was unable to add the event to your calendar."
        
    elif command_type == "search_file":
        results = raw_output.get("results", [])
        search_term = raw_output.get("search_term", "")
        
        if not results:
            return f"I couldn't find any files matching '{search_term}'."
            
        response = f"I found these files matching '{search_term}':\n\n"
        for result in results:
            response += f"• {result}\n"
        return response
        
    elif command_type == "search_store":
        return raw_output.get("message", "Store search is not implemented yet.")
        
    elif command_type == "open_app":
        return raw_output.get("message", "Application launcher is not implemented yet.")
        
    else:
        return "I'm not sure how to format that type of response." 
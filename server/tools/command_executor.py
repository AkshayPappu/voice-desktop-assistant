from tools.file_search import search_file
from tools.calendar_handler import CalendarHandler
from tools.email_handler import EmailHandler
from datetime import datetime, timedelta
from llm.response_formatter import format_response
from voice.tts_speaker import speak_text

def execute_command(command_data):
    """
    Execute the command based on the processed LLM output.
    
    Args:
        command_data (dict): Dictionary containing the command and its parameters
    """
    command_type = command_data.get("command_type")
    
    # Handle general questions separately
    if command_type == "general_question":
        # For general questions, return the response directly from parameters
        response = command_data.get("parameters", {}).get("response", "")
        if response:
            # Speak the response
            speak_text(response)
            return response
        return "I apologize, but I couldn't generate a proper response to your question."
    
    # Handle other command types
    parameters = command_data.get("parameters", {})
    raw_output = {}
    
    if command_type == "email_check":
        try:
            email_handler = EmailHandler()
            days_back = parameters.get('days_back', 7)
            important_only = parameters.get('important_only', False)
            max_results = parameters.get('max_results', 10)
            
            emails = email_handler.get_recent_emails(
                max_results=max_results,
                days_back=days_back,
                important_only=important_only
            )
            
            raw_output = {
                "emails": emails,
                "count": len(emails),
                "timeframe": f"last {days_back} days",
                "important_only": important_only
            }
            
        except Exception as e:
            raw_output = {"error": str(e)}
            
    elif command_type == "email_send":
        try:
            email_handler = EmailHandler()
            to = parameters.get('to')
            subject = parameters.get('subject')
            body = parameters.get('body')
            
            if not all([to, subject, body]):
                raw_output = {"error": "Missing required parameters for sending email"}
                return
                
            result = email_handler.send_email(to, subject, body)
            if result:
                raw_output = {
                    "status": "success",
                    "message": result['message']
                }
            else:
                raw_output = {"error": "Failed to send email"}
                
        except Exception as e:
            raw_output = {"error": str(e)}
            
    elif command_type == "email_draft":
        try:
            email_handler = EmailHandler()
            to = parameters.get('to')
            subject = parameters.get('subject')
            body = parameters.get('body')
            
            if not all([to, subject, body]):
                raw_output = {"error": "Missing required parameters for drafting email"}
                return
                
            result = email_handler.draft_email(to, subject, body)
            if result:
                raw_output = {
                    "status": "success",
                    "message": result['message'],
                    "draft_id": result['id']
                }
            else:
                raw_output = {"error": "Failed to create email draft"}
                
        except Exception as e:
            raw_output = {"error": str(e)}
            
    elif command_type == "search_file":
        filename = parameters.get('filename')
        if filename:
            print(f"\nSearching for files containing '{filename}'...")
            results = search_file(filename)
            raw_output = {
                "search_term": filename,
                "results": results
            }
                
    elif command_type == "calendar_check":
        try:
            calendar = CalendarHandler()
            timeframe = parameters.get('timeframe')
            date = parameters.get('date')
            start_date = parameters.get('start_date')
            end_date = parameters.get('end_date')
            
            if timeframe:
                now = datetime.now()
                if timeframe.lower() in ["today", "now"]:
                    time_min = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    time_max = time_min + timedelta(days=1)
                elif timeframe.lower() in ["tomorrow", "next day"]:
                    time_min = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                    time_max = time_min + timedelta(days=1)
                elif timeframe.lower() in ["this week", "next week", "week"]:
                    time_min = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    time_max = time_min + timedelta(days=7)
                elif timeframe.lower() in ["next", "upcoming", "coming"]:
                    time_min = now
                    time_max = now + timedelta(days=1)
                else:
                    time_min = now
                    time_max = now + timedelta(days=1)
            elif date:
                time_min = datetime.strptime(date, "%Y-%m-%d")
                time_max = time_min + timedelta(days=1)
            elif start_date and end_date:
                time_min = datetime.strptime(start_date, "%Y-%m-%d")
                time_max = datetime.strptime(end_date, "%Y-%m-%d")
            else:
                time_min = datetime.now()
                time_max = time_min + timedelta(days=1)
            
            events = calendar.get_events(
                time_min=time_min.isoformat() + 'Z',
                time_max=time_max.isoformat() + 'Z'
            )
            
            raw_output = {
                "timeframe": timeframe or date or f"{start_date} to {end_date}",
                "events": events
            }
                
        except Exception as e:
            raw_output = {"error": str(e)}
            
    elif command_type == "calendar_add":
        try:
            calendar = CalendarHandler()
            title = parameters.get('title')
            date = parameters.get('date')
            time = parameters.get('time')
            
            if not all([title, date, time]):
                raw_output = {"error": "Missing required parameters for calendar event"}
                return
                
            event = calendar.add_event(
                summary=title,
                date=date,
                time=time
            )
            
            raw_output = {
                "event": event,
                "status": "success" if event else "failed"
            }
                
        except Exception as e:
            raw_output = {"error": str(e)}
            
    elif command_type == "search_store":
        raw_output = {"message": "Store search functionality not implemented yet."}
        
    elif command_type == "open_app":
        raw_output = {"message": "Application launcher not implemented yet."}
        
    else:
        raw_output = {"error": f"Unknown command type: {command_type}"}
    
    # Format the raw output into a natural response
    formatted_response = format_response(command_type, raw_output)
    print(f"\n{formatted_response}")
    
    # Speak the response
    speak_text(formatted_response) 
    return formatted_response
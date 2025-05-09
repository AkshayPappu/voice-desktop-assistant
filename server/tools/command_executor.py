from tools.file_search import search_file
from tools.calendar_handler import CalendarHandler
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
    parameters = command_data.get("parameters", {})
    raw_output = {}
    
    if command_type == "search_file":
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
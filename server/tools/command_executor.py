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
            
            # Get the timezone from the calendar handler
            timezone = calendar.timezone
            
            print("\nCalendar Check Debug Info:")
            print(f"Requested timeframe: {timeframe}")
            print(f"Requested date: {date}")
            print(f"Requested start_date: {start_date}")
            print(f"Requested end_date: {end_date}")
            
            if timeframe:
                now = datetime.now(timezone)  # Use timezone-aware datetime
                current_year = now.year  # Get current year
                print(f"Current time: {now}")
                print(f"Current year: {current_year}")
                
                if timeframe.lower() in ["today", "now"]:
                    time_min = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    time_max = time_min + timedelta(days=1)
                    print(f"Timeframe 'today': {time_min} to {time_max}")
                elif timeframe.lower() in ["tomorrow", "next day"]:
                    time_min = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                    time_max = time_min + timedelta(days=1)
                    print(f"Timeframe 'tomorrow': {time_min} to {time_max}")
                elif timeframe.lower() in ["this week", "this_week", "week"]:
                    # For this week, start from now and look ahead 7 days
                    time_min = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    time_max = time_min + timedelta(days=7)
                    print(f"Timeframe 'this week':")
                    print(f"  Start (today): {time_min}")
                    print(f"  End (7 days later): {time_max}")
                elif timeframe.lower() in ["next week"]:
                    # Get the start of next week (Monday)
                    time_min = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    days_since_monday = now.weekday()  # 0 for Monday, 6 for Sunday
                    time_min = time_min + timedelta(days=(7 - days_since_monday))
                    # Ensure we're using current year
                    time_min = time_min.replace(year=current_year)
                    # Set end to end of next Sunday
                    time_max = time_min + timedelta(days=7)
                    print(f"Timeframe 'next week':")
                    print(f"  Start (Monday): {time_min}")
                    print(f"  End (Sunday): {time_max}")
                elif timeframe.lower() in ["next", "upcoming", "coming"]:
                    time_min = now
                    time_max = now + timedelta(days=1)
                    print(f"Timeframe 'next/upcoming': {time_min} to {time_max}")
                else:
                    # Default to next 24 hours
                    time_min = now
                    time_max = now + timedelta(days=1)
                    print(f"Default timeframe: {time_min} to {time_max}")
            elif date:
                # Parse date and make it timezone-aware
                time_min = datetime.strptime(date, "%Y-%m-%d")
                time_min = timezone.localize(time_min)
                # Ensure we're using current year if not explicitly specified
                if time_min.year != current_year:
                    time_min = time_min.replace(year=current_year)
                time_max = time_min + timedelta(days=1)
                print(f"Specific date: {date}")
                print(f"Parsed time range: {time_min} to {time_max}")
            elif start_date and end_date:
                # Parse dates and make them timezone-aware
                time_min = datetime.strptime(start_date, "%Y-%m-%d")
                time_min = timezone.localize(time_min)
                # Ensure we're using current year if not explicitly specified
                if time_min.year != current_year:
                    time_min = time_min.replace(year=current_year)
                time_max = datetime.strptime(end_date, "%Y-%m-%d")
                time_max = timezone.localize(time_max)
                # Ensure we're using current year if not explicitly specified
                if time_max.year != current_year:
                    time_max = time_max.replace(year=current_year)
                print(f"Date range: {start_date} to {end_date}")
                print(f"Parsed time range: {time_min} to {time_max}")
            else:
                time_min = datetime.now(timezone)
                time_max = time_min + timedelta(days=1)
                print(f"No timeframe specified, using default: {time_min} to {time_max}")
            
            print(f"\nFinal time range for calendar query:")
            print(f"Start: {time_min.isoformat()}")
            print(f"End: {time_max.isoformat()}")
            
            events = calendar.get_events(
                time_min=time_min.isoformat(),
                time_max=time_max.isoformat()
            )
            
            print(f"\nFound {len(events)} events in the specified time range")
            for event in events:
                print(f"Event: {event['summary']} at {event['start']}")
            
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
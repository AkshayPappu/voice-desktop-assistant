from tools.file_search import search_file
from tools.calendar_handler import CalendarHandler
from datetime import datetime, timedelta

def execute_command(command_data):
    """
    Execute the command based on the processed LLM output.
    
    Args:
        command_data (dict): Dictionary containing the command and its parameters
    """
    command_type = command_data.get("command_type")
    parameters = command_data.get("parameters", {})
    
    if command_type == "search_file":
        filename = parameters.get('filename')
        if filename:
            print(f"\nSearching for files containing '{filename}'...")
            results = search_file(filename)
            
            if results:
                print(f"\nFound {len(results)} matching files:")
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. {result['name']}")
                    print(f"   Path: {result['path']}")
                    print(f"   Modified: {result['modified']}")
                    print(f"   Size: {result['size']} bytes")
            else:
                print("No matching files found.")
                
    elif command_type == "calendar_check":
        try:
            calendar = CalendarHandler()
            timeframe = parameters.get('timeframe')
            date = parameters.get('date')
            
            if timeframe:
                if timeframe == "today":
                    time_min = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    time_max = time_min + timedelta(days=1)
                elif timeframe == "tomorrow":
                    time_min = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                    time_max = time_min + timedelta(days=1)
                elif timeframe == "this_week":
                    time_min = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    time_max = time_min + timedelta(days=7)
                else:
                    print(f"Unknown timeframe: {timeframe}")
                    return
            elif date:
                time_min = datetime.strptime(date, "%Y-%m-%d")
                time_max = time_min + timedelta(days=1)
            else:
                # Default to next 7 days
                time_min = datetime.now()
                time_max = time_min + timedelta(days=7)
            
            events = calendar.get_events(
                time_min=time_min.isoformat() + 'Z',
                time_max=time_max.isoformat() + 'Z'
            )
            
            if events:
                print(f"\nFound {len(events)} events:")
                for event in events:
                    print(f"\nEvent: {event['summary']}")
                    print(f"Start: {event['start']}")
                    print(f"End: {event['end']}")
                    if event['location'] != 'No Location':
                        print(f"Location: {event['location']}")
            else:
                print("No events found for the specified time period.")
                
        except Exception as e:
            print(f"Error checking calendar: {str(e)}")
            
    elif command_type == "calendar_add":
        try:
            calendar = CalendarHandler()
            title = parameters.get('title')
            date = parameters.get('date')
            time = parameters.get('time')
            
            if not all([title, date, time]):
                print("Missing required parameters for calendar event")
                return
                
            event = calendar.add_event(
                summary=title,
                date=date,
                time=time
            )
            
            if event:
                print(f"\nSuccessfully added event:")
                print(f"Title: {event['summary']}")
                print(f"Start: {event['start']}")
                print(f"End: {event['end']}")
                if event['location'] != 'No Location':
                    print(f"Location: {event['location']}")
                if event['description'] != 'No Description':
                    print(f"Description: {event['description']}")
            else:
                print("Failed to add event to calendar")
                
        except Exception as e:
            print(f"Error adding calendar event: {str(e)}")
            
    elif command_type == "search_store":
        print("Store search functionality not implemented yet.")
        
    elif command_type == "open_app":
        print("Application launcher not implemented yet.")
        
    else:
        print(f"Unknown command type: {command_type}") 
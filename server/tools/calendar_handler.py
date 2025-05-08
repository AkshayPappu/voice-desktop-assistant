from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from dateutil import parser
from dateutil.relativedelta import relativedelta
import pytz

# Load environment variables
load_dotenv()

class CalendarHandler:
    def __init__(self):
        """Initialize the Calendar handler with credentials"""
        self.credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.target_calendar_email = os.getenv('TARGET_CALENDAR_EMAIL')
        self.timezone = pytz.timezone('America/New_York')  # Default to Eastern Time
        
        if not self.credentials_path:
            raise Exception("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        if not self.target_calendar_email:
            raise Exception("TARGET_CALENDAR_EMAIL environment variable not set")
            
        # Define the required scopes
        self.SCOPES = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events',
            'https://www.googleapis.com/auth/calendar.readonly'
        ]
            
        try:
            # Create credentials without domain-wide delegation
            self.credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            
            # Build the Calendar API service
            self.service = build('calendar', 'v3', credentials=self.credentials)
            
            # Test the connection
            self.test_connection()
            
        except Exception as e:
            print(f"Error initializing calendar handler: {str(e)}")
            print("\nPlease ensure you have:")
            print("1. Enabled the Google Calendar API in your Google Cloud Console")
            print("2. Set the correct TARGET_CALENDAR_EMAIL in your .env file")
            print("3. Shared your calendar with the service account email")
            raise
    
    def parse_natural_date(self, date_str):
        """
        Parse natural language date strings into datetime objects
        
        Args:
            date_str (str): Natural language date (e.g., "next Friday", "tomorrow", "next week")
            
        Returns:
            datetime: Parsed datetime object in local timezone
        """
        now = datetime.now(self.timezone)
        
        # Handle common natural language patterns
        if date_str.lower() == "tomorrow":
            return now + timedelta(days=1)
        elif date_str.lower() == "next week":
            return now + timedelta(days=7)
        elif date_str.lower() == "next month":
            return now + relativedelta(months=1)
        elif date_str.lower().startswith("next "):
            # Handle "next [day of week]"
            try:
                parsed_date = parser.parse(date_str, fuzzy=True)
                return self.timezone.localize(parsed_date)
            except:
                # If parser fails, try to handle it manually
                days = {
                    "monday": 0, "tuesday": 1, "wednesday": 2,
                    "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
                }
                day = date_str.lower().split()[-1]
                if day in days:
                    target_day = days[day]
                    current_day = now.weekday()
                    days_ahead = target_day - current_day
                    if days_ahead <= 0:
                        days_ahead += 7
                    return now + timedelta(days=days_ahead)
        
        # Try parsing with dateutil
        try:
            parsed_date = parser.parse(date_str, fuzzy=True)
            return self.timezone.localize(parsed_date)
        except:
            raise ValueError(f"Could not parse date: {date_str}")
    
    def parse_time(self, time_str):
        """
        Parse time string into datetime object
        
        Args:
            time_str (str): Time string (e.g., "17:30", "5:30 PM")
            
        Returns:
            datetime: Datetime object with the specified time in local timezone
        """
        try:
            # Try parsing with dateutil
            parsed_time = parser.parse(time_str)
            # Create a datetime object for today with the parsed time
            now = datetime.now(self.timezone)
            return now.replace(
                hour=parsed_time.hour,
                minute=parsed_time.minute,
                second=0,
                microsecond=0
            )
        except:
            # If that fails, try basic time format
            try:
                hour, minute = map(int, time_str.split(':'))
                now = datetime.now(self.timezone)
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            except:
                raise ValueError(f"Could not parse time: {time_str}")
    
    def test_connection(self):
        """Test the calendar connection"""
        try:
            # Try to list calendars to verify access
            calendar_list = self.service.calendarList().list().execute()
            print("Successfully connected to Google Calendar")
            return True
        except Exception as e:
            print(f"Failed to connect to Google Calendar: {str(e)}")
            return False
    
    def get_events(self, time_min=None, time_max=None, max_results=10):
        """
        Get events from the calendar within a time range
        
        Args:
            time_min (str): Start time in ISO format (default: now)
            time_max (str): End time in ISO format (default: 7 days from now)
            max_results (int): Maximum number of events to return
            
        Returns:
            list: List of event dictionaries
        """
        if not time_min:
            time_min = datetime.now(self.timezone).isoformat()
        if not time_max:
            time_max = (datetime.now(self.timezone) + timedelta(days=7)).isoformat()
            
        try:
            events_result = self.service.events().list(
                calendarId=self.target_calendar_email,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Format events for easier use
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                formatted_events.append({
                    'summary': event.get('summary', 'No Title'),
                    'start': start,
                    'end': end,
                    'location': event.get('location', 'No Location'),
                    'description': event.get('description', 'No Description')
                })
                
            return formatted_events
            
        except Exception as e:
            print(f"Error fetching calendar events: {str(e)}")
            return []
    
    def add_event(self, summary, start_time=None, end_time=None, date=None, time=None, description=None, location=None):
        """
        Add a new event to the calendar
        
        Args:
            summary (str): Event title
            start_time (str): Start time in ISO format or natural language (optional)
            end_time (str): End time in ISO format or natural language (optional)
            date (str): Date in natural language (e.g., "next Friday")
            time (str): Time in natural language (e.g., "17:30" or "5:30 PM")
            description (str): Event description
            location (str): Event location
            
        Returns:
            dict: The created event or None if failed
        """
        try:
            # Handle separate date and time parameters
            if date and time:
                # Parse the date
                start_dt = self.parse_natural_date(date)
                # Parse the time
                time_dt = self.parse_time(time)
                # Combine date and time
                start_dt = start_dt.replace(hour=time_dt.hour, minute=time_dt.minute)
                # Default to 1 hour duration
                end_dt = start_dt + timedelta(hours=1)
            else:
                # Handle combined start_time and end_time
                if isinstance(start_time, str):
                    start_dt = self.parse_natural_date(start_time)
                    if ':' in start_time:  # If time is included in the string
                        time_part = start_time.split()[-1]  # Get the time part
                        time_dt = self.parse_time(time_part)
                        start_dt = start_dt.replace(hour=time_dt.hour, minute=time_dt.minute)
                else:
                    start_dt = start_time
                    
                if isinstance(end_time, str):
                    end_dt = self.parse_natural_date(end_time)
                    if ':' in end_time:  # If time is included in the string
                        time_part = end_time.split()[-1]  # Get the time part
                        time_dt = self.parse_time(time_part)
                        end_dt = end_dt.replace(hour=time_dt.hour, minute=time_dt.minute)
                else:
                    end_dt = end_time
                
                # If no end time specified, make it 1 hour after start
                if not end_dt:
                    end_dt = start_dt + timedelta(hours=1)
            
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': str(self.timezone),
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': str(self.timezone),
                }
            }
            
            if description:
                event['description'] = description
            if location:
                event['location'] = location
                
            event = self.service.events().insert(
                calendarId=self.target_calendar_email,
                body=event
            ).execute()
            
            return {
                'summary': event.get('summary'),
                'start': event['start'].get('dateTime'),
                'end': event['end'].get('dateTime'),
                'location': event.get('location', 'No Location'),
                'description': event.get('description', 'No Description')
            }
            
        except Exception as e:
            print(f"Error adding calendar event: {str(e)}")
            return None
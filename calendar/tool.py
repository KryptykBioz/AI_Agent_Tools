# Filename: BASE/tools/installed/calendar/tool.py
"""
Calendar Tool - Simplified Architecture
Local calendar system for event management with persistent storage
"""
from typing import List, Dict, Any, Optional
from BASE.handlers.base_tool import BaseTool
from datetime import datetime, timedelta
from pathlib import Path
import json
import uuid


class CalendarStorage:
    """Handles persistent storage of calendar events"""
    
    def __init__(self, storage_path: Path, logger=None):
        """Initialize calendar storage"""
        self.storage_path = storage_path
        self.logger = logger
        self.events: Dict[str, Dict] = {}
        
        # Ensure storage directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing events
        self._load_events()
    
    def _load_events(self):
        """Load events from disk"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.events = json.load(f)
                
                if self.logger:
                    self.logger.system(f"[Calendar] Loaded {len(self.events)} events from storage")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"[Calendar] Failed to load events: {e}")
                self.events = {}
        else:
            self.events = {}
    
    def _save_events(self):
        """Save events to disk"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.events, f, indent=2, ensure_ascii=False)
            
            if self.logger:
                self.logger.system(f"[Calendar] Saved {len(self.events)} events to storage")
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"[Calendar] Failed to save events: {e}")
            return False
    
    def add_event(self, event: Dict) -> str:
        """Add new event and return its ID"""
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        event['id'] = event_id
        event['created_at'] = datetime.now().isoformat()
        
        self.events[event_id] = event
        self._save_events()
        
        return event_id
    
    def get_event(self, event_id: str) -> Optional[Dict]:
        """Get event by ID"""
        return self.events.get(event_id)
    
    def delete_event(self, event_id: str) -> bool:
        """Delete event by ID"""
        if event_id in self.events:
            del self.events[event_id]
            self._save_events()
            return True
        return False
    
    def get_all_events(self) -> List[Dict]:
        """Get all events"""
        return list(self.events.values())
    
    def get_events_by_date(self, date: datetime) -> List[Dict]:
        """Get events for a specific date"""
        target_date = date.date()
        matching_events = []
        
        for event in self.events.values():
            event_date = datetime.fromisoformat(event['datetime']).date()
            if event_date == target_date:
                matching_events.append(event)
        
        return sorted(matching_events, key=lambda e: e['datetime'])
    
    def get_events_in_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get events within date range"""
        start = start_date.date()
        end = end_date.date()
        matching_events = []
        
        for event in self.events.values():
            event_date = datetime.fromisoformat(event['datetime']).date()
            if start <= event_date <= end:
                matching_events.append(event)
        
        return sorted(matching_events, key=lambda e: e['datetime'])
    
    def search_events(self, query: str) -> List[Dict]:
        """Search events by title or description"""
        query_lower = query.lower()
        matching_events = []
        
        for event in self.events.values():
            title = event.get('title', '').lower()
            description = event.get('description', '').lower()
            
            if query_lower in title or query_lower in description:
                matching_events.append(event)
        
        return sorted(matching_events, key=lambda e: e['datetime'])
    
    def get_upcoming_events(self, count: int) -> List[Dict]:
        """Get next N upcoming events"""
        now = datetime.now()
        future_events = []
        
        for event in self.events.values():
            event_datetime = datetime.fromisoformat(event['datetime'])
            if event_datetime > now:
                future_events.append(event)
        
        # Sort by datetime and return first N
        future_events.sort(key=lambda e: e['datetime'])
        return future_events[:count]


class CalendarTool(BaseTool):
    """
    Calendar tool for event management
    Local storage with no external dependencies
    """
    
    @property
    def name(self) -> str:
        return "calendar"
    
    async def initialize(self) -> bool:
        """Initialize calendar tool"""
        # Determine storage path
        if hasattr(self._config, 'project_root'):
            storage_dir = Path(self._config.project_root) / 'BASE' / 'tools' / 'installed' / 'calendar'
        else:
            storage_dir = Path(__file__).parent
        
        storage_file = storage_dir / 'calendar_events.json'
        
        # Initialize storage
        self.storage = CalendarStorage(storage_file, self._logger)
        
        if self._logger:
            event_count = len(self.storage.events)
            self._logger.success(f"[Calendar] Initialized with {event_count} events")
        
        return True
    
    async def cleanup(self):
        """Cleanup calendar resources"""
        # Save any pending changes
        if hasattr(self, 'storage'):
            self.storage._save_events()
        
        if self._logger:
            self._logger.system("[Calendar] Cleaned up")
    
    def is_available(self) -> bool:
        """Check if calendar is available"""
        return hasattr(self, 'storage') and self.storage is not None
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute calendar command
        
        Commands:
        - create_event: Create new event
        - view_today: View today's events
        - view_week: View this week's events
        - view_date: View specific date's events
        - delete_event: Delete an event
        - search_events: Search events
        - upcoming: Get upcoming events
        
        Args:
            command: Command name
            args: Command arguments
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[Calendar] Command: '{command}', args: {args}")
        
        # Route commands
        if command == 'create_event':
            return await self._handle_create_event(args)
        elif command == 'view_today':
            return await self._handle_view_today()
        elif command == 'view_week':
            return await self._handle_view_week()
        elif command == 'view_date':
            return await self._handle_view_date(args)
        elif command == 'delete_event':
            return await self._handle_delete_event(args)
        elif command == 'search_events':
            return await self._handle_search_events(args)
        elif command == 'upcoming':
            return await self._handle_upcoming(args)
        else:
            return self._error_result(
                f'Unknown command: {command}',
                guidance='Available: create_event, view_today, view_week, view_date, delete_event, search_events, upcoming'
            )
    
    async def _handle_create_event(self, args: List[Any]) -> Dict[str, Any]:
        """Handle create_event command"""
        # Validate arguments
        if len(args) < 4:
            return self._error_result(
                'Missing required arguments',
                guidance='Required: title, date (YYYY-MM-DD), time (HH:MM), duration_minutes'
            )
        
        title = str(args[0])
        date_str = str(args[1])
        time_str = str(args[2])
        duration_minutes = int(args[3])
        description = str(args[4]) if len(args) > 4 else ''
        
        # Parse and validate datetime
        try:
            event_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError as e:
            return self._error_result(
                f'Invalid date/time format: {e}',
                guidance='Use YYYY-MM-DD for date and HH:MM for time (24-hour format)'
            )
        
        # Check if event is in the past
        if event_datetime < datetime.now():
            return self._error_result(
                'Cannot create events in the past',
                guidance='Choose a future date and time'
            )
        
        # Calculate end time
        end_datetime = event_datetime + timedelta(minutes=duration_minutes)
        
        # Create event object
        event = {
            'title': title,
            'description': description,
            'datetime': event_datetime.isoformat(),
            'end_datetime': end_datetime.isoformat(),
            'duration_minutes': duration_minutes,
            'date': date_str,
            'time': time_str
        }
        
        # Add to storage
        event_id = self.storage.add_event(event)
        
        # Format success message
        formatted_datetime = event_datetime.strftime("%A, %B %d, %Y at %I:%M %p")
        
        return self._success_result(
            f'Created event "{title}" on {formatted_datetime} ({duration_minutes} minutes)',
            metadata={
                'event_id': event_id,
                'title': title,
                'datetime': event_datetime.isoformat(),
                'duration_minutes': duration_minutes
            }
        )
    
    async def _handle_view_today(self) -> Dict[str, Any]:
        """Handle view_today command"""
        today = datetime.now()
        events = self.storage.get_events_by_date(today)
        
        if not events:
            return self._success_result(
                'No events scheduled for today',
                metadata={'count': 0}
            )
        
        # Format events
        formatted = self._format_event_list(events)
        
        return self._success_result(
            f'Today\'s events ({len(events)}):\n\n{formatted}',
            metadata={'count': len(events), 'date': today.date().isoformat()}
        )
    
    async def _handle_view_week(self) -> Dict[str, Any]:
        """Handle view_week command"""
        today = datetime.now()
        # Get start of week (Monday)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        events = self.storage.get_events_in_range(start_of_week, end_of_week)
        
        if not events:
            return self._success_result(
                'No events scheduled for this week',
                metadata={'count': 0}
            )
        
        # Format events grouped by date
        formatted = self._format_event_list_by_day(events)
        
        week_range = f"{start_of_week.strftime('%B %d')} - {end_of_week.strftime('%B %d, %Y')}"
        
        return self._success_result(
            f'This week\'s events ({week_range}):\n\n{formatted}',
            metadata={'count': len(events)}
        )
    
    async def _handle_view_date(self, args: List[Any]) -> Dict[str, Any]:
        """Handle view_date command"""
        if not args:
            return self._error_result(
                'Missing date argument',
                guidance='Provide date in YYYY-MM-DD format'
            )
        
        date_str = str(args[0])
        
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError as e:
            return self._error_result(
                f'Invalid date format: {e}',
                guidance='Use YYYY-MM-DD format (e.g., 2025-12-15)'
            )
        
        events = self.storage.get_events_by_date(target_date)
        
        if not events:
            formatted_date = target_date.strftime("%A, %B %d, %Y")
            return self._success_result(
                f'No events scheduled for {formatted_date}',
                metadata={'count': 0, 'date': date_str}
            )
        
        formatted = self._format_event_list(events)
        formatted_date = target_date.strftime("%A, %B %d, %Y")
        
        return self._success_result(
            f'Events on {formatted_date}:\n\n{formatted}',
            metadata={'count': len(events), 'date': date_str}
        )
    
    async def _handle_delete_event(self, args: List[Any]) -> Dict[str, Any]:
        """Handle delete_event command"""
        if not args:
            return self._error_result(
                'Missing event_id argument',
                guidance='Provide the event ID to delete'
            )
        
        event_id = str(args[0])
        
        # Get event details before deleting
        event = self.storage.get_event(event_id)
        
        if not event:
            return self._error_result(
                f'Event not found: {event_id}',
                guidance='Check the event ID and try again'
            )
        
        # Delete the event
        success = self.storage.delete_event(event_id)
        
        if success:
            title = event.get('title', 'Unknown')
            return self._success_result(
                f'Deleted event: {title}',
                metadata={'event_id': event_id, 'title': title}
            )
        else:
            return self._error_result(
                'Failed to delete event',
                guidance='Event may have already been deleted'
            )
    
    async def _handle_search_events(self, args: List[Any]) -> Dict[str, Any]:
        """Handle search_events command"""
        if not args:
            return self._error_result(
                'Missing search query',
                guidance='Provide a search term to find events'
            )
        
        query = str(args[0])
        events = self.storage.search_events(query)
        
        if not events:
            return self._success_result(
                f'No events found matching "{query}"',
                metadata={'count': 0, 'query': query}
            )
        
        formatted = self._format_event_list_by_day(events)
        
        return self._success_result(
            f'Found {len(events)} event(s) matching "{query}":\n\n{formatted}',
            metadata={'count': len(events), 'query': query}
        )
    
    async def _handle_upcoming(self, args: List[Any]) -> Dict[str, Any]:
        """Handle upcoming command"""
        if not args:
            count = 5
        else:
            count = min(int(args[0]), 20)  # Max 20 events
        
        events = self.storage.get_upcoming_events(count)
        
        if not events:
            return self._success_result(
                'No upcoming events scheduled',
                metadata={'count': 0}
            )
        
        formatted = self._format_event_list_by_day(events)
        
        return self._success_result(
            f'Next {len(events)} upcoming event(s):\n\n{formatted}',
            metadata={'count': len(events)}
        )
    
    def _format_event_list(self, events: List[Dict]) -> str:
        """Format list of events for display"""
        lines = []
        
        for event in events:
            event_dt = datetime.fromisoformat(event['datetime'])
            time_str = event_dt.strftime("%I:%M %p")
            duration = event.get('duration_minutes', 0)
            
            title = event.get('title', 'Untitled Event')
            description = event.get('description', '')
            event_id = event.get('id', 'unknown')
            
            line = f"• {time_str} - {title} ({duration}m)"
            if description:
                line += f"\n  {description}"
            line += f"\n  ID: {event_id}"
            
            lines.append(line)
        
        return '\n\n'.join(lines)
    
    def _format_event_list_by_day(self, events: List[Dict]) -> str:
        """Format list of events grouped by day"""
        # Group events by date
        events_by_date = {}
        for event in events:
            event_dt = datetime.fromisoformat(event['datetime'])
            date_key = event_dt.date()
            
            if date_key not in events_by_date:
                events_by_date[date_key] = []
            
            events_by_date[date_key].append(event)
        
        # Format each day
        lines = []
        for date_key in sorted(events_by_date.keys()):
            date_obj = datetime.combine(date_key, datetime.min.time())
            date_str = date_obj.strftime("%A, %B %d, %Y")
            
            lines.append(f"**{date_str}**")
            
            day_events = events_by_date[date_key]
            for event in day_events:
                event_dt = datetime.fromisoformat(event['datetime'])
                time_str = event_dt.strftime("%I:%M %p")
                duration = event.get('duration_minutes', 0)
                
                title = event.get('title', 'Untitled Event')
                description = event.get('description', '')
                event_id = event.get('id', 'unknown')
                
                line = f"  • {time_str} - {title} ({duration}m)"
                if description:
                    line += f"\n    {description}"
                line += f"\n    ID: {event_id}"
                
                lines.append(line)
        
        return '\n\n'.join(lines)
    
    def get_status(self) -> Dict[str, Any]:
        """Get calendar status (for debugging/monitoring)"""
        if not self.is_available():
            return {'available': False, 'total_events': 0}
        
        all_events = self.storage.get_all_events()
        upcoming = self.storage.get_upcoming_events(5)
        
        return {
            'available': True,
            'total_events': len(all_events),
            'upcoming_events': len(upcoming),
            'storage_path': str(self.storage.storage_path)
        }
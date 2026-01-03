# Filename: BASE/tools/installed/reminders/reminders.py
"""
Reminder Manager - Refactored for Tool Control System
Manages persistent reminders with automatic notification tracking and expiration
"""
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
import re


@dataclass(slots=True)
class Reminder:
    """Individual reminder entry"""
    id: str
    description: str
    trigger_time: float
    created_at: float
    notification_count: int = 0
    last_notified: Optional[float] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: dict) -> 'Reminder':
        # Handle old reminders without notification fields
        if 'notification_count' not in data:
            data['notification_count'] = 0
        if 'last_notified' not in data:
            data['last_notified'] = None
        return Reminder(**data)
    
    def is_overdue(self, current_time: float) -> bool:
        """Check if reminder is overdue"""
        return current_time >= self.trigger_time
    
    def is_due_within(self, current_time: float, minutes: int) -> bool:
        """Check if reminder is due within specified minutes"""
        time_diff = self.trigger_time - current_time
        return 0 < time_diff <= (minutes * 60)
    
    def get_time_until(self, current_time: float) -> str:
        """Get human-readable time until reminder"""
        diff = self.trigger_time - current_time
        
        if diff < 0:
            # Overdue
            diff = abs(diff)
            if diff < 60:
                return f"{int(diff)} seconds"
            elif diff < 3600:
                return f"{int(diff / 60)} minutes"
            elif diff < 86400:
                hours = int(diff / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                days = int(diff / 86400)
                return f"{days} day{'s' if days != 1 else ''}"
        else:
            # Future
            if diff < 60:
                return f"{int(diff)} seconds"
            elif diff < 3600:
                return f"{int(diff / 60)} minutes"
            elif diff < 86400:
                hours = int(diff / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                days = int(diff / 86400)
                return f"{days} day{'s' if days != 1 else ''}"
    
    def get_datetime_str(self) -> str:
        """Get formatted datetime string"""
        dt = datetime.fromtimestamp(self.trigger_time)
        return dt.strftime("%Y-%m-%d %I:%M %p")
    
    def should_expire(self, current_time: float) -> bool:
        """Check if reminder should be expired (overdue + notified 3 times)"""
        return (
            self.is_overdue(current_time) and 
            self.notification_count >= 3
        )


class ReminderManager:
    """
    Manages reminders with automatic notification tracking
    """
    __slots__ = ('project_root', 'logger', 'storage_file', 'reminders')
    
    def __init__(self, project_root: Path, logger=None):
        self.project_root = project_root
        self.logger = logger
        self.storage_file = project_root / "personality" / "memory" / "reminders.json"
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory reminder list
        self.reminders: List[Reminder] = []
        
        # Load existing reminders
        self._load_reminders()
        
        if self.logger:
            active = len([r for r in self.reminders if not r.should_expire(time.time())])
            overdue = len([r for r in self.reminders if r.is_overdue(time.time())])
            self.logger.system(
                f"[Reminder Manager] Loaded {active} active reminders "
                f"({overdue} overdue)"
            )
    
    # ========================================================================
    # PERSISTENCE
    # ========================================================================
    
    def _load_reminders(self):
        """Load reminders from persistent storage"""
        if not self.storage_file.exists():
            self.reminders = []
            return
        
        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
            
            self.reminders = [
                Reminder.from_dict(r) for r in data.get('reminders', [])
            ]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"[Reminder Manager] Error loading reminders: {e}")
            self.reminders = []
    
    def _save_reminders(self):
        """Save reminders to persistent storage"""
        try:
            data = {
                'reminders': [r.to_dict() for r in self.reminders],
                'last_saved': time.time()
            }
            
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"[Reminder Manager] Error saving reminders: {e}")
    
    # ========================================================================
    # REMINDER CREATION
    # ========================================================================
    
    def create_reminder(self, description: str, time_phrase: str) -> Dict:
        """
        Create a new reminder from natural language time phrase
        
        Returns:
            Dict with 'success', 'message', and 'reminder' (if successful)
        """
        trigger_time = self._parse_natural_time(time_phrase)
        
        if trigger_time is None:
            return {
                'success': False,
                'message': f"Could not parse time phrase: '{time_phrase}'",
                'reminder': None
            }
        
        # Check if in the past
        if trigger_time < time.time():
            return {
                'success': False,
                'message': f"Time phrase '{time_phrase}' is in the past",
                'reminder': None
            }
        
        # Create reminder
        reminder_id = f"{int(time.time() * 1000)}"
        
        reminder = Reminder(
            id=reminder_id,
            description=description,
            trigger_time=trigger_time,
            created_at=time.time()
        )
        
        self.reminders.append(reminder)
        self._save_reminders()
        
        if self.logger:
            self.logger.system(
                f"[Reminder Manager] Created: '{description}' "
                f"at {reminder.get_datetime_str()}"
            )
        
        return {
            'success': True,
            'message': 'Reminder created successfully',
            'reminder': self._format_reminder_dict(reminder)
        }
    
    # ========================================================================
    # REMINDER RETRIEVAL
    # ========================================================================
    
    def get_all_active_reminders(self) -> List[Dict]:
        """Get all reminders that haven't expired (notified < 3 times)"""
        current_time = time.time()
        
        active = [
            r for r in self.reminders
            if not r.should_expire(current_time)
        ]
        
        # Sort by trigger time
        active.sort(key=lambda r: r.trigger_time)
        
        return [self._format_reminder_dict(r) for r in active]
    
    def get_overdue_reminders(self) -> List[Dict]:
        """Get reminders that are overdue and haven't been notified 3 times"""
        current_time = time.time()
        
        overdue = [
            r for r in self.reminders
            if r.is_overdue(current_time) and r.notification_count < 3
        ]
        
        # Sort by how overdue (most overdue first)
        overdue.sort(key=lambda r: r.trigger_time)
        
        return [self._format_reminder_dict(r) for r in overdue]
    
    def get_reminders_due_within(self, minutes: int) -> List[Dict]:
        """Get reminders due within specified minutes (not overdue)"""
        current_time = time.time()
        
        upcoming = [
            r for r in self.reminders
            if r.is_due_within(current_time, minutes) and not r.should_expire(current_time)
        ]
        
        # Sort by trigger time (soonest first)
        upcoming.sort(key=lambda r: r.trigger_time)
        
        return [self._format_reminder_dict(r) for r in upcoming]
    
    def get_next_n_reminders(self, n: int = 3) -> List[Dict]:
        """Get next N upcoming reminders (not overdue, not expired)"""
        current_time = time.time()
        
        future = [
            r for r in self.reminders
            if not r.is_overdue(current_time) and not r.should_expire(current_time)
        ]
        
        # Sort by trigger time (soonest first)
        future.sort(key=lambda r: r.trigger_time)
        
        return [self._format_reminder_dict(r) for r in future[:n]]
    
    def _format_reminder_dict(self, reminder: Reminder) -> Dict:
        """Format reminder as dictionary with computed fields"""
        current_time = time.time()
        
        return {
            'id': reminder.id,
            'description': reminder.description,
            'trigger_time': reminder.trigger_time,
            'scheduled_time': reminder.get_datetime_str(),
            'time_until': reminder.get_time_until(current_time),
            'is_overdue': reminder.is_overdue(current_time),
            'overdue_duration': reminder.get_time_until(current_time) if reminder.is_overdue(current_time) else None,
            'notification_count': reminder.notification_count,
            'created_at': reminder.created_at
        }
    
    # ========================================================================
    # REMINDER MANAGEMENT
    # ========================================================================
    
    def mark_reminder_notified(self, reminder_id: str):
        """Mark reminder as notified (increment notification count)"""
        for reminder in self.reminders:
            if reminder.id == reminder_id:
                reminder.notification_count += 1
                reminder.last_notified = time.time()
                self._save_reminders()
                
                if self.logger:
                    self.logger.system(
                        f"[Reminder Manager] Notified ({reminder.notification_count}/3): "
                        f"'{reminder.description}'"
                    )
                
                break
    
    def delete_reminder(self, reminder_id: str) -> Dict:
        """Delete a reminder by ID"""
        for i, reminder in enumerate(self.reminders):
            if reminder.id == reminder_id:
                removed = self.reminders.pop(i)
                self._save_reminders()
                
                if self.logger:
                    self.logger.system(
                        f"[Reminder Manager] Deleted: '{removed.description}'"
                    )
                
                return {
                    'success': True,
                    'message': f"Deleted reminder: {removed.description}"
                }
        
        return {
            'success': False,
            'message': f"Reminder not found: {reminder_id}"
        }
    
    def cleanup_expired_reminders(self) -> int:
        """Remove reminders that have been notified 3 times"""
        current_time = time.time()
        
        original_count = len(self.reminders)
        
        self.reminders = [
            r for r in self.reminders
            if not r.should_expire(current_time)
        ]
        
        removed_count = original_count - len(self.reminders)
        
        if removed_count > 0:
            self._save_reminders()
            
            if self.logger:
                self.logger.system(
                    f"[Reminder Manager] Cleaned up {removed_count} expired reminder(s)"
                )
        
        return removed_count
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    def get_overdue_count(self) -> int:
        """Get count of overdue reminders"""
        current_time = time.time()
        return len([
            r for r in self.reminders
            if r.is_overdue(current_time) and r.notification_count < 3
        ])
    
    def get_upcoming_count(self, minutes: int = 30) -> int:
        """Get count of upcoming reminders within minutes"""
        current_time = time.time()
        return len([
            r for r in self.reminders
            if r.is_due_within(current_time, minutes)
        ])
    
    # ========================================================================
    # TIME PARSING
    # ========================================================================
    
    def _parse_natural_time(self, time_phrase: str) -> Optional[float]:
        """
        Parse natural language time phrases to Unix timestamp
        
        Supports:
        - "in X minutes/hours/days/weeks"
        - "in X seconds" (for testing)
        - "tomorrow at Xpm"
        - "next monday at Xpm"
        - Specific dates like "january 15 at 2:30pm"
        """
        time_phrase = time_phrase.lower().strip()
        now = datetime.now()
        
        # Map number words to digits
        word_to_num = {
            'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
            'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10'
        }
        
        for word, num in word_to_num.items():
            time_phrase = re.sub(r'\b' + word + r'\b', num, time_phrase)
        
        # Pattern: "in X minutes/hours/days/weeks"
        relative_match = re.match(r'in (\d+)\s*(minute|hour|day|week)s?', time_phrase)
        if relative_match:
            amount = int(relative_match.group(1))
            unit = relative_match.group(2)
            
            if unit == 'minute':
                delta = timedelta(minutes=amount)
            elif unit == 'hour':
                delta = timedelta(hours=amount)
            elif unit == 'day':
                delta = timedelta(days=amount)
            elif unit == 'week':
                delta = timedelta(weeks=amount)
            else:
                return None
            
            target = now + delta
            return target.timestamp()
        
        # Pattern: "in X seconds" (testing)
        seconds_match = re.match(r'in (\d+)\s*seconds?', time_phrase)
        if seconds_match:
            seconds = int(seconds_match.group(1))
            target = now + timedelta(seconds=seconds)
            return target.timestamp()
        
        # Pattern: "tomorrow at Xpm/Xam"
        if 'tomorrow' in time_phrase:
            time_part = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)', time_phrase)
            if time_part:
                hour = int(time_part.group(1))
                minute = int(time_part.group(2)) if time_part.group(2) else 0
                am_pm = time_part.group(3)
                
                if am_pm == 'pm' and hour != 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
                
                target = now + timedelta(days=1)
                target = target.replace(hour=hour, minute=minute, second=0, microsecond=0)
                return target.timestamp()
        
        # Pattern: "next monday/tuesday/etc at Xpm"
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day in enumerate(weekdays):
            if day in time_phrase:
                time_part = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)', time_phrase)
                if time_part:
                    hour = int(time_part.group(1))
                    minute = int(time_part.group(2)) if time_part.group(2) else 0
                    am_pm = time_part.group(3)
                    
                    if am_pm == 'pm' and hour != 12:
                        hour += 12
                    elif am_pm == 'am' and hour == 12:
                        hour = 0
                    
                    # Find next occurrence of this weekday
                    days_ahead = (i - now.weekday() + 7) % 7
                    if days_ahead == 0:
                        days_ahead = 7  # Next week if it's today
                    
                    target = now + timedelta(days=days_ahead)
                    target = target.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    return target.timestamp()
        
        return None
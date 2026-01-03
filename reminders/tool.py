# Filename: BASE/tools/installed/reminders/tool.py
"""
Reminders Tool - Refactored Architecture
Single master class with periodic context loop for proactive notifications
"""
import asyncio
from typing import List, Dict, Any
from pathlib import Path
from BASE.handlers.base_tool import BaseTool
from BASE.tools.installed.reminders.reminders import ReminderManager


class RemindersTool(BaseTool):
    """
    Time-based reminders with natural language parsing and proactive notifications
    Context loop checks every 30 minutes and notifies of due/upcoming reminders
    """

    __slots__ = ('reminder_manager')
    
    @property
    def name(self) -> str:
        return "reminders"
    
    def has_context_loop(self) -> bool:
        """Enable background context loop for proactive notifications"""
        return True
    
    async def initialize(self) -> bool:
        """Initialize reminder system"""
        # Get project root with fallback
        if hasattr(self._config, 'project_root'):
            project_root = Path(self._config.project_root)
        else:
            project_root = Path.cwd()
            if self._logger:
                self._logger.warning(
                    f"[Reminders] No project_root in config, using: {project_root}"
                )
        
        try:
            # Initialize reminder manager
            self.reminder_manager = ReminderManager(
                project_root=project_root,
                logger=self._logger
            )
            
            # Check for overdue reminders
            overdue_count = self.reminder_manager.get_overdue_count()
            upcoming_count = self.reminder_manager.get_upcoming_count()
            
            if self._logger:
                self._logger.system(
                    f"[Reminders] Initialized: {overdue_count} overdue, "
                    f"{upcoming_count} upcoming"
                )
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Reminders] Initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def cleanup(self):
        """Cleanup reminder resources"""
        if hasattr(self, 'reminder_manager') and self.reminder_manager:
            # Clean up expired reminders
            expired = self.reminder_manager.cleanup_expired_reminders()
            
            if expired > 0 and self._logger:
                self._logger.system(
                    f"[Reminders] Cleanup: removed {expired} expired reminder(s)"
                )
        
        if self._logger:
            self._logger.system("[Reminders] Cleanup complete")
    
    def is_available(self) -> bool:
        """Check if reminder system is ready"""
        return hasattr(self, 'reminder_manager') and self.reminder_manager is not None
    
    async def context_loop(self, thought_buffer):
        """
        Background loop for proactive reminder notifications
        Checks every 30 minutes and immediately on startup
        """
        if self._logger:
            self._logger.system("[Reminders] Context loop started")
        
        # Immediate check on startup for overdue reminders
        await self._check_and_notify(thought_buffer, startup=True)
        
        # Then check every 30 minutes
        while self._running:
            try:
                await asyncio.sleep(1800)  # 30 minutes
                
                if not self._running:
                    break
                
                await self._check_and_notify(thought_buffer, startup=False)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[Reminders] Context loop error: {e}")
                await asyncio.sleep(1800)
        
        if self._logger:
            self._logger.system("[Reminders] Context loop stopped")
    
    async def _check_and_notify(self, thought_buffer, startup: bool = False):
        """
        Check for reminders and notify via thought buffer
        
        Priority:
        1. Overdue reminders (immediate notification)
        2. Due in next 30 minutes
        3. Next 3 upcoming reminders (if nothing else)
        """
        if not self.reminder_manager:
            return
        
        # Get overdue reminders
        overdue = self.reminder_manager.get_overdue_reminders()
        
        # Inject overdue reminders (highest urgency)
        for reminder in overdue:
            notification_count = reminder.get('notification_count', 0)
            
            if startup:
                label = "[URGENT]"
                urgency_level = "Critical"
            elif notification_count == 0:
                label = "[OVERDUE]"
                urgency_level = "Critical"
            elif notification_count == 1:
                label = "[OVERDUE]"
                urgency_level = "High"
            else:  # notification_count >= 2
                label = "[OVERDUE]"
                urgency_level = "High"
            
            overdue_str = reminder['overdue_duration']
            
            thought_buffer.add_processed_thought(
                content=(
                    f"{label} REMINDER (notification {notification_count + 1}/3): "
                    f"{reminder['description']}\n"
                    f"Was due: {overdue_str} ago at {reminder['scheduled_time']}"
                ),
                source='urgent_reminder',
            )
            
            # Mark as notified
            self.reminder_manager.mark_reminder_notified(reminder['id'])
            
            if self._logger:
                self._logger.warning(
                    f"[Reminders] Notified overdue: '{reminder['description']}' "
                    f"(notification {notification_count + 1}/3)"
                )
        
        # Get reminders due in next 30 minutes
        upcoming_30min = self.reminder_manager.get_reminders_due_within(minutes=30)
        
        if upcoming_30min:
            # Inject upcoming reminders
            for reminder in upcoming_30min:
                time_until = reminder['time_until']
                
                thought_buffer.add_processed_thought(
                    content=(
                        f"[UPCOMING] Reminder in {time_until}: {reminder['description']}\n"
                        f"Scheduled for: {reminder['scheduled_time']}"
                    ),
                    source='reminder_upcoming',
                )
            
            if self._logger:
                self._logger.system(
                    f"[Reminders] Notified {len(upcoming_30min)} upcoming reminder(s)"
                )
        
        else:
            # No reminders in next 30 minutes - get next 3 upcoming
            next_three = self.reminder_manager.get_next_n_reminders(n=3)
            
            if next_three:
                reminder_lines = []
                for reminder in next_three:
                    reminder_lines.append(
                        f"  - {reminder['description']} (in {reminder['time_until']} at {reminder['scheduled_time']})"
                    )
                
                thought_buffer.add_processed_thought(
                    content=(
                        f"[INFO] Next upcoming reminders:\n" + "\n".join(reminder_lines)
                    ),
                    source='reminder_info',
                )
                
                if self._logger:
                    self._logger.system(
                        f"[Reminders] Notified next {len(next_three)} upcoming reminder(s)"
                    )
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute reminder command
        
        Commands:
        - create: Create reminder [description: str, time_phrase: str]
        - list: List all active reminders []
        - delete: Delete reminder [reminder_id: str]
        - clear: Clear specific reminder [reminder_id: str]
        
        Args:
            command: Command name
            args: Command arguments
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[Reminders] Command: '{command}', args: {args}")
        
        if not self.is_available():
            return self._error_result(
                'Reminder system not initialized',
                guidance='Check storage directory configuration'
            )
        
        try:
            if command == 'create':
                return await self._handle_create(args)
            elif command == 'list':
                return await self._handle_list(args)
            elif command in ['delete', 'clear']:
                return await self._handle_delete(args)
            else:
                return self._error_result(
                    f'Unknown command: {command}',
                    guidance='Available commands: create, list, delete, clear'
                )
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Reminders] Command execution error: {e}")
            return self._error_result(
                f'Command execution failed: {str(e)}',
                guidance='Check command format and arguments'
            )
    
    async def _handle_create(self, args: List[Any]) -> Dict[str, Any]:
        """Handle reminder creation"""
        if len(args) < 2:
            return self._error_result(
                'Missing arguments for reminder creation',
                guidance='Provide: description and time phrase (e.g., "take break", "in 30 minutes")'
            )
        
        description = str(args[0]).strip()
        time_phrase = str(args[1]).strip()
        
        if not description:
            return self._error_result(
                'Reminder description cannot be empty',
                guidance='Provide a meaningful description'
            )
        
        if not time_phrase:
            return self._error_result(
                'Time phrase cannot be empty',
                guidance='Use phrases like: "in 30 minutes", "tomorrow at 3pm", "next monday at 10am"'
            )
        
        # Create reminder
        result = self.reminder_manager.create_reminder(
            description=description,
            time_phrase=time_phrase
        )
        
        if not result['success']:
            return self._error_result(
                result['message'],
                metadata={
                    'description': description,
                    'time_phrase': time_phrase
                },
                guidance='Use phrases like: "in 30 minutes", "in 2 hours", "tomorrow at 3pm"'
            )
        
        reminder = result['reminder']
        
        if self._logger:
            self._logger.success(f"[Reminders] Created: '{description}' "
                f"(due in {reminder['time_until']} at {reminder['scheduled_time']})")
        
        return self._success_result(
            f"[SUCCESS] Reminder set: \"{description}\" at {reminder['scheduled_time']}",
            metadata=reminder
        )
    
    async def _handle_list(self, args: List[Any]) -> Dict[str, Any]:
        """Handle listing reminders"""
        reminders = self.reminder_manager.get_all_active_reminders()
        
        if not reminders:
            return self._success_result(
                'No active reminders',
                metadata={'count': 0, 'reminders': []}
            )
        
        lines = [f"Active reminders ({len(reminders)}):"]
        
        for reminder in reminders:
            status_label = "[OVERDUE]" if reminder.get('is_overdue') else "[SCHEDULED]"
            lines.append(f"  {status_label} [{reminder['id']}] {reminder['description']}")
            
            if reminder.get('is_overdue'):
                lines.append(f"    OVERDUE by {reminder['overdue_duration']}")
            else:
                lines.append(f"    Due in: {reminder['time_until']} ({reminder['scheduled_time']})")
        
        if self._logger:
            self._logger.success(f"[Reminders] Listed {len(reminders)} active reminders")
        
        return self._success_result(
            '\n'.join(lines),
            metadata={'count': len(reminders), 'reminders': reminders}
        )
    
    async def _handle_delete(self, args: List[Any]) -> Dict[str, Any]:
        """Handle reminder deletion"""
        if not args:
            return self._error_result(
                'No reminder ID provided',
                guidance='Provide reminder ID from reminders.list'
            )
        
        reminder_id = str(args[0])
        
        result = self.reminder_manager.delete_reminder(reminder_id)
        
        if result['success']:
            if self._logger:
                self._logger.success(f"[Reminders] Deleted reminder: {reminder_id}")
            
            return self._success_result(
                f"[SUCCESS] Deleted reminder: {reminder_id}",
                metadata={'reminder_id': reminder_id}
            )
        else:
            return self._error_result(
                result['message'],
                metadata={'reminder_id': reminder_id},
                guidance='Use reminders.list to see valid IDs'
            )
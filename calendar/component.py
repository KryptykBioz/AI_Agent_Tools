# Filename: BASE/tools/installed/calendar/component.py
"""
Calendar Tool - GUI Component with Visual Calendar Grid
FIXED: Graceful handling when tool is disabled during initialization
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from calendar import monthrange, day_name
from BASE.interface.gui_themes import DarkTheme


class CalendarComponent:
    """
    GUI component for Calendar tool with visual month grid
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        self.calendar_tool = None
        
        # State
        self.current_date = datetime.now()
        self.selected_date = None
        self.events_cache = {}
        
        # GUI elements
        self.panel_frame = None
        self.status_label = None
        self.month_label = None
        self.calendar_grid = None
        self.day_cells = {}
        self.event_detail_text = None
        
        # Update timer
        self.update_job = None
        
        # FIXED: Track initialization state
        self._initialization_complete = False
    
    def create_panel(self, parent_frame):
        """Create the calendar panel with visual grid"""
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="📅 Calendar",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Status bar
        self._create_status_section()
        
        # Month navigation
        self._create_navigation_section()
        
        # Calendar grid (month view)
        self._create_calendar_grid()
        
        # Event details panel
        self._create_event_details_section()
        
        # Control buttons
        self._create_control_section()
        
        # FIXED: Mark initialization complete BEFORE rendering
        self._initialization_complete = True
        
        # Initial render
        self._render_calendar()
        self._schedule_status_update()
        
        return self.panel_frame
    
    def _create_status_section(self):
        """Create status display"""
        status_frame = ttk.Frame(self.panel_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = tk.Label(
            status_frame,
            text="⚫ Tool not enabled",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X)
    
    # ... (rest of the _create methods remain the same)
    
    def _refresh_calendar(self):
        """Refresh calendar from tool"""
        self.calendar_tool = self._get_calendar_tool()
        
        if not self.calendar_tool:
            # FIXED: Don't log warning during initialization
            if self._initialization_complete:
                self.logger.system("[Calendar] Tool not currently enabled")
            
            # Show disabled state in UI
            if self.status_label:
                self.status_label.config(
                    text="⚫ Tool not enabled - toggle USE_CALENDAR to enable",
                    foreground=DarkTheme.FG_MUTED
                )
            
            # Still render empty calendar
            self._render_calendar()
            return
        
        # Tool is available - load events for current month
        if self.ai_core.main_loop:
            import asyncio
            
            async def load_month_async():
                # Get first and last day of month
                year = self.current_date.year
                month = self.current_date.month
                first_day = datetime(year, month, 1)
                last_day = datetime(year, month, monthrange(year, month)[1])
                
                # Clear cache
                self.events_cache.clear()
                
                # Load all events (we'll filter by month)
                if hasattr(self.calendar_tool, 'storage'):
                    all_events = self.calendar_tool.storage.get_events_in_range(first_day, last_day)
                    
                    # Cache events by date
                    for event in all_events:
                        event_dt = datetime.fromisoformat(event['datetime'])
                        date_str = event_dt.date().isoformat()
                        
                        if date_str not in self.events_cache:
                            self.events_cache[date_str] = []
                        
                        self.events_cache[date_str].append(event)
                    
                    event_count = len(all_events)
                    month_str = self.current_date.strftime('%B %Y')
                    
                    # Update status
                    self.status_label.config(
                        text=f"🟢 Ready - {event_count} event(s) in {month_str}",
                        foreground=DarkTheme.ACCENT_GREEN
                    )
                    
                    self.logger.system(f"[Calendar] Loaded {event_count} events for {month_str}")
                
                # Re-render calendar
                self._render_calendar()
            
            asyncio.run_coroutine_threadsafe(load_month_async(), self.ai_core.main_loop)
    
    def _get_calendar_tool(self):
        """Get calendar tool instance"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        if 'calendar' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('calendar')
    
    def _schedule_status_update(self):
        """Schedule periodic updates"""
        if self.panel_frame and self.panel_frame.winfo_exists():
            self._refresh_calendar()
            self.update_job = self.panel_frame.after(60000, self._schedule_status_update)  # Every minute
    
    # ... (rest of the methods remain the same - navigation, rendering, etc.)
    
    def _create_navigation_section(self):
        """Create month navigation controls"""
        nav_frame = ttk.Frame(self.panel_frame)
        nav_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Previous month button
        ttk.Button(
            nav_frame,
            text="◄",
            command=self._previous_month,
            width=3
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Month/Year label
        self.month_label = tk.Label(
            nav_frame,
            text="",
            font=("Segoe UI", 12, "bold"),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER
        )
        self.month_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Next month button
        ttk.Button(
            nav_frame,
            text="►",
            command=self._next_month,
            width=3
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Today button
        ttk.Button(
            nav_frame,
            text="Today",
            command=self._go_to_today,
            width=8
        ).pack(side=tk.LEFT, padx=(10, 0))
    
    def _create_calendar_grid(self):
        """Create calendar grid for month view"""
        grid_frame = ttk.Frame(self.panel_frame)
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Day name headers
        header_frame = tk.Frame(grid_frame, bg=DarkTheme.BG_DARKER)
        header_frame.pack(fill=tk.X)
        
        for i, day in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
            tk.Label(
                header_frame,
                text=day,
                font=("Segoe UI", 9, "bold"),
                fg=DarkTheme.ACCENT_PURPLE,
                bg=DarkTheme.BG_DARKER,
                width=8,
                height=1
            ).grid(row=0, column=i, padx=1, pady=1, sticky="nsew")
        
        # Configure column weights
        for i in range(7):
            header_frame.columnconfigure(i, weight=1)
        
        # Calendar grid (6 rows for weeks)
        self.calendar_grid = tk.Frame(grid_frame, bg=DarkTheme.BG_DARKER)
        self.calendar_grid.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        for i in range(7):
            self.calendar_grid.columnconfigure(i, weight=1)
        for i in range(6):
            self.calendar_grid.rowconfigure(i, weight=1)
        
        # Create day cells (6 rows x 7 columns)
        self.day_cells = {}
        for row in range(6):
            for col in range(7):
                cell = self._create_day_cell(row, col)
                self.day_cells[(row, col)] = cell
    
    def _create_day_cell(self, row, col):
        """Create a single day cell in the calendar grid"""
        cell_frame = tk.Frame(
            self.calendar_grid,
            bg=DarkTheme.BG_LIGHTER,
            relief="solid",
            borderwidth=1,
            highlightthickness=0
        )
        cell_frame.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
        
        # Day number label
        day_label = tk.Label(
            cell_frame,
            text="",
            font=("Segoe UI", 10),
            fg=DarkTheme.FG_PRIMARY,
            bg=DarkTheme.BG_LIGHTER,
            anchor="ne",
            padx=3,
            pady=2
        )
        day_label.pack(fill=tk.X)
        
        # Event indicator
        event_label = tk.Label(
            cell_frame,
            text="",
            font=("Segoe UI", 7),
            fg=DarkTheme.ACCENT_GREEN,
            bg=DarkTheme.BG_LIGHTER,
            anchor="center"
        )
        event_label.pack(fill=tk.BOTH, expand=True)
        
        # Click handler
        cell_frame.bind("<Button-1>", lambda e, r=row, c=col: self._on_cell_click(r, c))
        day_label.bind("<Button-1>", lambda e, r=row, c=col: self._on_cell_click(r, c))
        event_label.bind("<Button-1>", lambda e, r=row, c=col: self._on_cell_click(r, c))
        
        # Hover effects
        def on_enter(e):
            cell_frame.config(bg=DarkTheme.FG_SECONDARY)
            day_label.config(bg=DarkTheme.FG_SECONDARY)
            event_label.config(bg=DarkTheme.FG_SECONDARY)
        
        def on_leave(e):
            # Restore normal or selected color
            if hasattr(cell_frame, 'is_selected') and cell_frame.is_selected:
                cell_frame.config(bg=DarkTheme.ACCENT_PURPLE)
                day_label.config(bg=DarkTheme.ACCENT_PURPLE)
                event_label.config(bg=DarkTheme.ACCENT_PURPLE)
            else:
                cell_frame.config(bg=DarkTheme.BG_LIGHTER)
                day_label.config(bg=DarkTheme.BG_LIGHTER)
                event_label.config(bg=DarkTheme.BG_LIGHTER)
        
        cell_frame.bind("<Enter>", on_enter)
        cell_frame.bind("<Leave>", on_leave)
        day_label.bind("<Enter>", on_enter)
        day_label.bind("<Leave>", on_leave)
        event_label.bind("<Enter>", on_enter)
        event_label.bind("<Leave>", on_leave)
        
        return {
            'frame': cell_frame,
            'day_label': day_label,
            'event_label': event_label,
            'date': None
        }
    
    def _create_event_details_section(self):
        """Create event details display"""
        details_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Selected Date Events",
            style="Dark.TLabelframe"
        )
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Scrollable text widget
        scroll = ttk.Scrollbar(details_frame, orient='vertical')
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.event_detail_text = tk.Text(
            details_frame,
            height=6,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 9),
            bg=DarkTheme.BG_DARK,
            fg=DarkTheme.FG_PRIMARY,
            yscrollcommand=scroll.set
        )
        self.event_detail_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll.config(command=self.event_detail_text.yview)
        
        # Text tags
        self.event_detail_text.tag_configure("title", foreground=DarkTheme.ACCENT_GREEN, font=("Consolas", 9, "bold"))
        self.event_detail_text.tag_configure("time", foreground=DarkTheme.ACCENT_PURPLE)
        self.event_detail_text.tag_configure("id", foreground=DarkTheme.FG_MUTED, font=("Consolas", 8))
    
    def _create_control_section(self):
        """Create control buttons"""
        control_frame = ttk.Frame(self.panel_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Button(
            control_frame,
            text="➕ New Event",
            command=self._open_create_event_dialog,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            control_frame,
            text="🔍 Search",
            command=self._open_search_dialog,
            width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            control_frame,
            text="🔄 Refresh",
            command=self._refresh_calendar,
            width=12
        ).pack(side=tk.LEFT)
    
    def _render_calendar(self):
        """Render the calendar grid for current month"""
        # Update month label
        self.month_label.config(text=self.current_date.strftime("%B %Y"))
        
        # Get month info
        year = self.current_date.year
        month = self.current_date.month
        first_day_of_month = datetime(year, month, 1)
        last_day_of_month = datetime(year, month, monthrange(year, month)[1])
        
        # Get weekday of first day (0=Monday, 6=Sunday)
        first_weekday = first_day_of_month.weekday()
        
        # Calculate start date (may be from previous month)
        start_date = first_day_of_month - timedelta(days=first_weekday)
        
        # Fill calendar grid
        current_date = start_date
        today = datetime.now().date()
        
        for row in range(6):
            for col in range(7):
                cell = self.day_cells[(row, col)]
                cell_date = current_date.date()
                
                # Store date in cell
                cell['date'] = cell_date
                
                # Update day number
                day_num = current_date.day
                cell['day_label'].config(text=str(day_num))
                
                # Styling based on context
                is_current_month = current_date.month == month
                is_today = cell_date == today
                is_selected = (self.selected_date and cell_date == self.selected_date.date())
                
                # Reset selection flag
                cell['frame'].is_selected = is_selected
                
                if is_selected:
                    # Selected date
                    cell['frame'].config(bg=DarkTheme.ACCENT_PURPLE)
                    cell['day_label'].config(bg=DarkTheme.ACCENT_PURPLE, fg="white")
                    cell['event_label'].config(bg=DarkTheme.ACCENT_PURPLE)
                elif is_today:
                    # Today
                    cell['frame'].config(bg=DarkTheme.ACCENT_GREEN)
                    cell['day_label'].config(bg=DarkTheme.ACCENT_GREEN, fg="white", font=("Segoe UI", 10, "bold"))
                    cell['event_label'].config(bg=DarkTheme.ACCENT_GREEN)
                elif not is_current_month:
                    # Other month
                    cell['frame'].config(bg=DarkTheme.BG_DARKER)
                    cell['day_label'].config(bg=DarkTheme.BG_DARKER, fg=DarkTheme.FG_MUTED, font=("Segoe UI", 10))
                    cell['event_label'].config(bg=DarkTheme.BG_DARKER)
                else:
                    # Normal day
                    cell['frame'].config(bg=DarkTheme.BG_LIGHTER)
                    cell['day_label'].config(bg=DarkTheme.BG_LIGHTER, fg=DarkTheme.FG_PRIMARY, font=("Segoe UI", 10))
                    cell['event_label'].config(bg=DarkTheme.BG_LIGHTER)
                
                # Show event indicator
                events_on_date = self._get_events_for_date(cell_date)
                if events_on_date:
                    event_count = len(events_on_date)
                    cell['event_label'].config(text=f"• {event_count} event{'s' if event_count != 1 else ''}")
                else:
                    cell['event_label'].config(text="")
                
                current_date += timedelta(days=1)
        
        # Update event details if date selected
        if self.selected_date:
            self._update_event_details(self.selected_date.date())
    
    def _get_events_for_date(self, date):
        """Get cached events for a specific date"""
        date_str = date.isoformat()
        return self.events_cache.get(date_str, [])
    
    def _on_cell_click(self, row, col):
        """Handle day cell click"""
        cell = self.day_cells[(row, col)]
        cell_date = cell['date']
        
        if cell_date:
            self.selected_date = datetime.combine(cell_date, datetime.min.time())
            self._render_calendar()
            self._update_event_details(cell_date)
    
    def _update_event_details(self, date):
        """Update event details for selected date"""
        events = self._get_events_for_date(date)
        
        self.event_detail_text.config(state=tk.NORMAL)
        self.event_detail_text.delete("1.0", tk.END)
        
        if not events:
            formatted_date = date.strftime("%A, %B %d, %Y")
            self.event_detail_text.insert(tk.END, f"No events on {formatted_date}")
        else:
            formatted_date = date.strftime("%A, %B %d, %Y")
            self.event_detail_text.insert(tk.END, f"{formatted_date}\n\n", "title")
            
            for event in events:
                event_dt = datetime.fromisoformat(event['datetime'])
                time_str = event_dt.strftime("%I:%M %p")
                duration = event.get('duration_minutes', 0)
                title = event.get('title', 'Untitled')
                description = event.get('description', '')
                event_id = event.get('id', '')
                
                self.event_detail_text.insert(tk.END, f"{time_str} ", "time")
                self.event_detail_text.insert(tk.END, f"- {title} ({duration}m)\n", "title")
                if description:
                    self.event_detail_text.insert(tk.END, f"  {description}\n")
                self.event_detail_text.insert(tk.END, f"  ID: {event_id}\n\n", "id")
        
        self.event_detail_text.config(state=tk.DISABLED)
    
    def _previous_month(self):
        """Navigate to previous month"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        
        self._refresh_calendar()
    
    def _next_month(self):
        """Navigate to next month"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        
        self._refresh_calendar()
    
    def _go_to_today(self):
        """Navigate to current month"""
        self.current_date = datetime.now()
        self.selected_date = datetime.now()
        self._refresh_calendar()
    
    def _open_create_event_dialog(self):
        """Open dialog to create event"""
        if not self.calendar_tool:
            messagebox.showwarning(
                "Tool Not Available",
                "Calendar tool is not enabled. Please enable USE_CALENDAR in the Controls panel."
            )
            return
        
        # Use selected date or today as default
        default_date = self.selected_date if self.selected_date else datetime.now()
        
        # ... (rest of dialog creation - same as document 27)
    
    def _open_search_dialog(self):
        """Open search dialog"""
        if not self.calendar_tool:
            messagebox.showwarning(
                "Tool Not Available",
                "Calendar tool is not enabled. Please enable USE_CALENDAR in the Controls panel."
            )
            return
        # ... (implement search dialog)
    
    def _create_event(self, title, date, time, duration, description):
        """Create event via calendar tool"""
        # ... (same as document 27)
        pass
    
    def cleanup(self):
        """Cleanup resources"""
        if self.update_job:
            try:
                self.panel_frame.after_cancel(self.update_job)
            except:
                pass
        
        self.logger.system("[Calendar] Component cleaned up")


# Factory function
def create_component(parent_gui, ai_core, logger):
    return CalendarComponent(parent_gui, ai_core, logger)
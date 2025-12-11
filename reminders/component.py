# Filename: BASE/tools/installed/reminders/component.py
"""
Reminders Tool - GUI Component
Dynamic GUI panel for creating and managing time-based reminders
"""
import tkinter as tk
from tkinter import ttk, messagebox
from BASE.interface.gui_themes import DarkTheme
import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime


class RemindersComponent:
    """GUI component for Reminders tool - create and manage time-based reminders"""
    
    def __init__(self, parent_gui, ai_core, logger):
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        self.reminders_tool = None
        self.panel_frame = None
        self.status_label = None
        self.desc_entry = None
        self.time_entry = None
        self.reminder_container = None
        self.canvas = None
        self.update_job = None
        self._reminder_widgets = {}
    
    def create_panel(self, parent_frame):
        """Create the reminders panel"""
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="⏰ Reminders & Timers",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Status section
        self._create_status_section()
        
        # Input section for creating reminders
        self._create_input_section()
        
        # Reminders list section
        self._create_list_section()
        
        # Start status updates
        self._schedule_status_update()
        
        return self.panel_frame
    
    def _create_status_section(self):
        """Create status display"""
        status_frame = ttk.Frame(self.panel_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = tk.Label(
            status_frame,
            text="⚫ Loading...",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Refresh button
        refresh_btn = ttk.Button(
            status_frame,
            text="🔄",
            command=self._refresh_reminders,
            width=3
        )
        refresh_btn.pack(side=tk.RIGHT)
    
    def _create_input_section(self):
        """Create input form for new reminders"""
        input_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Create New Reminder",
            style="Dark.TLabelframe"
        )
        input_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        content_frame = ttk.Frame(input_frame)
        content_frame.pack(fill=tk.X, padx=8, pady=8)
        
        # Description field
        ttk.Label(
            content_frame,
            text="Description:",
            style="TLabel"
        ).grid(row=0, column=0, sticky=tk.W, pady=(0, 3))
        
        self.desc_entry = ttk.Entry(
            content_frame,
            width=40,
            font=("Segoe UI", 9)
        )
        self.desc_entry.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 8))
        self.desc_entry.bind('<Return>', lambda e: self._create_reminder())
        
        # Time phrase field
        ttk.Label(
            content_frame,
            text="When:",
            style="TLabel"
        ).grid(row=2, column=0, sticky=tk.W, pady=(0, 3))
        
        self.time_entry = ttk.Entry(
            content_frame,
            width=30,
            font=("Segoe UI", 9)
        )
        self.time_entry.grid(row=3, column=0, sticky=tk.EW, padx=(0, 5))
        self.time_entry.bind('<Return>', lambda e: self._create_reminder())
        
        # Create button
        create_btn = ttk.Button(
            content_frame,
            text="⏰ Create",
            command=self._create_reminder,
            width=12
        )
        create_btn.grid(row=3, column=1, sticky=tk.EW)
        
        content_frame.columnconfigure(0, weight=1)
        
        # Examples
        examples = tk.Label(
            content_frame,
            text="Examples: in 30 minutes, in 2 hours, tomorrow at 3pm, next monday at 10am",
            font=("Segoe UI", 8),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        examples.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
    
    def _create_list_section(self):
        """Create scrollable list of reminders"""
        list_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Active Reminders",
            style="Dark.TLabelframe"
        )
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Scrollable container
        self.canvas = tk.Canvas(
            list_frame,
            bg=DarkTheme.BG_DARK,
            highlightthickness=0,
            height=250
        )
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        self.reminder_container = ttk.Frame(self.canvas)
        
        self.reminder_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        canvas_frame = self.canvas.create_window((0, 0), window=self.reminder_container, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mouse wheel
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1*(e.delta//120), "units"))
        
        # Configure canvas frame to expand
        def _configure_canvas(event):
            self.canvas.itemconfig(canvas_frame, width=event.width)
        
        self.canvas.bind('<Configure>', _configure_canvas)
    
    def _create_reminder(self):
        """Create a new reminder"""
        description = self.desc_entry.get().strip()
        time_phrase = self.time_entry.get().strip()
        
        if not description:
            messagebox.showwarning("Missing Description", "Please enter a reminder description")
            return
        
        if not time_phrase:
            messagebox.showwarning("Missing Time", "Please enter when to remind you")
            return
        
        self.reminders_tool = self._get_reminders_tool()
        
        if not self.reminders_tool:
            self._show_error("Reminders tool not available")
            return
        
        # Execute create command
        if self.ai_core.main_loop:
            async def create_async():
                result = await self.reminders_tool.execute('create', [description, time_phrase])
                
                if result.get('success'):
                    self.desc_entry.delete(0, tk.END)
                    self.time_entry.delete(0, tk.END)
                    self._refresh_reminders()
                    
                    reminder = result.get('metadata', {})
                    scheduled_time = reminder.get('scheduled_time', 'soon')
                    messagebox.showinfo(
                        "Reminder Created",
                        f"Reminder set for {scheduled_time}"
                    )
                    self.logger.success(f"[Reminders] Created: {description}")
                else:
                    error = result.get('content', 'Unknown error')
                    messagebox.showerror("Error", f"Failed to create reminder:\n{error}")
                    self.logger.error(f"[Reminders] Create failed: {error}")
            
            asyncio.run_coroutine_threadsafe(create_async(), self.ai_core.main_loop)
    
    def _refresh_reminders(self):
        """Refresh the reminders list"""
        self.logger.system("[Reminders] Refreshing list...")
        self._update_reminders_display()
    
    def _update_reminders_display(self):
        """Update the display of all reminders"""
        # Clear existing widgets
        for widget in self.reminder_container.winfo_children():
            widget.destroy()
        self._reminder_widgets.clear()
        
        self.reminders_tool = self._get_reminders_tool()
        
        if not self.reminders_tool:
            self._show_no_reminders("Tool not available")
            return
        
        # Get reminder manager
        if not hasattr(self.reminders_tool, 'reminder_manager'):
            self._show_no_reminders("Reminder manager not initialized")
            return
        
        manager = self.reminders_tool.reminder_manager
        
        # Get all active reminders
        try:
            reminders = manager.get_all_active_reminders()
            
            if not reminders:
                self._show_no_reminders("No active reminders")
                return
            
            # Create widget for each reminder
            for idx, reminder in enumerate(reminders):
                self._create_reminder_widget(reminder, idx)
        
        except Exception as e:
            self.logger.error(f"[Reminders] Error loading reminders: {e}")
            self._show_no_reminders(f"Error: {e}")
    
    def _show_no_reminders(self, message: str):
        """Show message when no reminders available"""
        no_reminders = tk.Label(
            self.reminder_container,
            text=message,
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            pady=20
        )
        no_reminders.pack(fill=tk.BOTH, expand=True)
    
    def _create_reminder_widget(self, reminder: Dict[str, Any], index: int):
        """Create widget for a single reminder"""
        frame = tk.Frame(
            self.reminder_container,
            bg=DarkTheme.BG_LIGHT,
            highlightbackground=DarkTheme.BORDER,
            highlightthickness=1
        )
        frame.pack(fill=tk.X, pady=3, ipady=6, ipadx=8)
        
        # Status indicator
        is_overdue = reminder.get('is_overdue', False)
        status_color = DarkTheme.ACCENT_RED if is_overdue else DarkTheme.ACCENT_GREEN
        status_text = "OVERDUE" if is_overdue else "ACTIVE"
        
        status = tk.Label(
            frame,
            text=status_text,
            bg=status_color,
            fg="white",
            font=("Segoe UI", 7, "bold"),
            padx=6,
            pady=2
        )
        status.pack(side=tk.LEFT, padx=(0, 8))
        
        # Content area
        content_frame = tk.Frame(frame, bg=DarkTheme.BG_LIGHT)
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Description
        desc = tk.Label(
            content_frame,
            text=reminder['description'],
            bg=DarkTheme.BG_LIGHT,
            fg=DarkTheme.FG_PRIMARY,
            font=("Segoe UI", 10, "bold"),
            anchor=tk.W
        )
        desc.pack(fill=tk.X)
        
        # Time info
        if is_overdue:
            time_text = f"⚠️ Overdue by {reminder.get('overdue_duration', 'unknown')}"
            time_color = DarkTheme.ACCENT_RED
        else:
            time_text = f"⏰ Due in {reminder['time_until']} ({reminder['scheduled_time']})"
            time_color = DarkTheme.FG_MUTED
        
        time_label = tk.Label(
            content_frame,
            text=time_text,
            bg=DarkTheme.BG_LIGHT,
            fg=time_color,
            font=("Segoe UI", 8),
            anchor=tk.W
        )
        time_label.pack(fill=tk.X)
        
        # Notification count (if notified)
        notification_count = reminder.get('notification_count', 0)
        if notification_count > 0:
            notify_label = tk.Label(
                content_frame,
                text=f"📢 Notified {notification_count}/3 times",
                bg=DarkTheme.BG_LIGHT,
                fg=DarkTheme.ACCENT_ORANGE if hasattr(DarkTheme, 'ACCENT_ORANGE') else DarkTheme.FG_SECONDARY,
                font=("Segoe UI", 7),
                anchor=tk.W
            )
            notify_label.pack(fill=tk.X)
        
        # Delete button
        del_btn = tk.Button(
            frame,
            text="✕",
            bg=DarkTheme.BG_LIGHT,
            fg=DarkTheme.FG_MUTED,
            activebackground=DarkTheme.ACCENT_RED,
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            border=0,
            cursor="hand2",
            command=lambda: self._delete_reminder(reminder['id'])
        )
        del_btn.pack(side=tk.RIGHT, padx=5)
        
        # Hover effects
        def on_enter(e):
            if frame.winfo_exists():
                frame.configure(bg=DarkTheme.BG_HOVER)
                content_frame.configure(bg=DarkTheme.BG_HOVER)
                desc.configure(bg=DarkTheme.BG_HOVER)
                time_label.configure(bg=DarkTheme.BG_HOVER)
                del_btn.configure(bg=DarkTheme.BG_HOVER)
                if notification_count > 0:
                    notify_label.configure(bg=DarkTheme.BG_HOVER)
        
        def on_leave(e):
            if frame.winfo_exists():
                frame.configure(bg=DarkTheme.BG_LIGHT)
                content_frame.configure(bg=DarkTheme.BG_LIGHT)
                desc.configure(bg=DarkTheme.BG_LIGHT)
                time_label.configure(bg=DarkTheme.BG_LIGHT)
                del_btn.configure(bg=DarkTheme.BG_LIGHT)
                if notification_count > 0:
                    notify_label.configure(bg=DarkTheme.BG_LIGHT)
        
        frame.bind('<Enter>', on_enter)
        frame.bind('<Leave>', on_leave)
        content_frame.bind('<Enter>', on_enter)
        content_frame.bind('<Leave>', on_leave)
        
        self._reminder_widgets[reminder['id']] = frame
    
    def _delete_reminder(self, reminder_id: str):
        """Delete a reminder"""
        self.reminders_tool = self._get_reminders_tool()
        
        if not self.reminders_tool:
            messagebox.showerror("Error", "Reminders tool not available")
            return
        
        # Confirm deletion
        if not messagebox.askyesno("Delete Reminder", "Are you sure you want to delete this reminder?"):
            return
        
        # Execute delete command
        if self.ai_core.main_loop:
            async def delete_async():
                result = await self.reminders_tool.execute('delete', [reminder_id])
                
                if result.get('success'):
                    self._refresh_reminders()
                    self.logger.success(f"[Reminders] Deleted: {reminder_id}")
                else:
                    error = result.get('content', 'Unknown error')
                    messagebox.showerror("Error", f"Failed to delete:\n{error}")
            
            asyncio.run_coroutine_threadsafe(delete_async(), self.ai_core.main_loop)
    
    def _update_status(self):
        """Update status display"""
        self.reminders_tool = self._get_reminders_tool()
        
        if not self.reminders_tool:
            self._update_status_unavailable()
            return
        
        if not self.reminders_tool.is_available():
            self._update_status_unavailable()
            return
        
        # Get reminder counts
        try:
            manager = self.reminders_tool.reminder_manager
            overdue_count = manager.get_overdue_count()
            upcoming_count = manager.get_upcoming_count(30)
            total_count = len(manager.get_all_active_reminders())
            
            if overdue_count > 0:
                self.status_label.config(
                    text=f"⚠️ {overdue_count} overdue, {total_count} total active",
                    foreground=DarkTheme.ACCENT_RED
                )
            elif upcoming_count > 0:
                self.status_label.config(
                    text=f"🟡 {upcoming_count} due soon, {total_count} total active",
                    foreground=DarkTheme.ACCENT_ORANGE if hasattr(DarkTheme, 'ACCENT_ORANGE') else DarkTheme.FG_SECONDARY
                )
            elif total_count > 0:
                self.status_label.config(
                    text=f"🟢 {total_count} active reminder(s)",
                    foreground=DarkTheme.ACCENT_GREEN
                )
            else:
                self.status_label.config(
                    text="🟢 Ready - No active reminders",
                    foreground=DarkTheme.ACCENT_GREEN
                )
        
        except Exception as e:
            self.logger.warning(f"[Reminders] Status update error: {e}")
            self._update_status_unavailable()
    
    def _update_status_unavailable(self):
        """Update UI for unavailable state"""
        self.status_label.config(
            text="⚫ Tool Not Available",
            foreground=DarkTheme.FG_MUTED
        )
    
    def _schedule_status_update(self):
        """Schedule periodic status updates"""
        if self.panel_frame and self.panel_frame.winfo_exists():
            self._update_status()
            self._update_reminders_display()
            # Update every 30 seconds
            self.update_job = self.panel_frame.after(30000, self._schedule_status_update)
    
    def _get_reminders_tool(self):
        """Get Reminders tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'reminders' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('reminders')
    
    def _show_error(self, message: str):
        """Show error message"""
        self.status_label.config(
            text=f"❌ {message}",
            foreground=DarkTheme.ACCENT_RED
        )
        self.logger.error(f"[Reminders] {message}")
    
    def cleanup(self):
        """Cleanup component resources"""
        # Cancel scheduled updates
        if self.update_job:
            try:
                self.panel_frame.after_cancel(self.update_job)
            except:
                pass
        
        self.logger.system("[Reminders] Component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        RemindersComponent instance
    """
    return RemindersComponent(parent_gui, ai_core, logger)
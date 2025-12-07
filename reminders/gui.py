#!/usr/bin/env python3
"""
Reminders Tool GUI - Dark Theme
Lightweight, fast tkinter interface for managing reminders
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path
from datetime import datetime
import sys

# # Add BASE to path if running standalone
# sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from reminders import ReminderManager
except ImportError:
    print("Error: Could not import ReminderManager. Ensure BASE directory is accessible.")
    sys.exit(1)


class RemindersGUI:
    """Dark theme GUI for reminder management"""
    
    # Dark theme colors
    BG = "#1e1e1e"
    BG_LIGHT = "#2d2d2d"
    BG_HOVER = "#3e3e3e"
    FG = "#d4d4d4"
    FG_DIM = "#888888"
    ACCENT = "#007acc"
    ACCENT_HOVER = "#1a8cd8"
    SUCCESS = "#4ec9b0"
    WARNING = "#ce9178"
    ERROR = "#f48771"
    BORDER = "#3e3e3e"
    
    def __init__(self, root, project_root=None):
        self.root = root
        self.root.title("Reminders")
        self.root.geometry("700x500")
        self.root.configure(bg=self.BG)
        
        # Initialize reminder manager
        if project_root is None:
            project_root = Path.cwd()
        
        self.manager = ReminderManager(project_root=project_root, logger=None)
        
        # Setup UI
        self._setup_styles()
        self._create_widgets()
        self._load_reminders()
        
        # Auto-refresh every 30 seconds
        self._schedule_refresh()
    
    def _setup_styles(self):
        """Configure ttk styles for dark theme"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('.',
            background=self.BG,
            foreground=self.FG,
            fieldbackground=self.BG_LIGHT,
            bordercolor=self.BORDER,
            darkcolor=self.BG,
            lightcolor=self.BG_LIGHT,
            troughcolor=self.BG,
            selectbackground=self.ACCENT,
            selectforeground=self.FG)
        
        style.configure('TFrame', background=self.BG)
        style.configure('TLabel', background=self.BG, foreground=self.FG)
        style.configure('TButton',
            background=self.BG_LIGHT,
            foreground=self.FG,
            borderwidth=1,
            focuscolor=self.ACCENT,
            padding=6)
        style.map('TButton',
            background=[('active', self.BG_HOVER), ('pressed', self.ACCENT)],
            foreground=[('active', self.FG)])
        
        style.configure('Accent.TButton',
            background=self.ACCENT,
            foreground=self.FG,
            borderwidth=0,
            padding=6)
        style.map('Accent.TButton',
            background=[('active', self.ACCENT_HOVER), ('pressed', self.ACCENT)])
        
        style.configure('TEntry',
            fieldbackground=self.BG_LIGHT,
            foreground=self.FG,
            insertcolor=self.FG,
            borderwidth=1,
            relief='solid')
    
    def _create_widgets(self):
        """Create main UI components"""
        # Main container
        main = ttk.Frame(self.root, padding=15)
        main.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title = ttk.Label(title_frame, text="⏰ Reminders", 
                         font=('Segoe UI', 16, 'bold'))
        title.pack(side=tk.LEFT)
        
        refresh_btn = ttk.Button(title_frame, text="↻", width=3,
                                command=self._load_reminders)
        refresh_btn.pack(side=tk.RIGHT)
        
        # Input section
        input_frame = ttk.Frame(main)
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Description
        desc_label = ttk.Label(input_frame, text="Description:")
        desc_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.desc_entry = ttk.Entry(input_frame, width=50)
        self.desc_entry.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))
        self.desc_entry.bind('<Return>', lambda e: self._create_reminder())
        
        # Time phrase
        time_label = ttk.Label(input_frame, text="When:")
        time_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        self.time_entry = ttk.Entry(input_frame, width=30)
        self.time_entry.grid(row=3, column=0, sticky=tk.EW, padx=(0, 10))
        self.time_entry.bind('<Return>', lambda e: self._create_reminder())
        
        create_btn = ttk.Button(input_frame, text="Create Reminder",
                               style='Accent.TButton',
                               command=self._create_reminder)
        create_btn.grid(row=3, column=1, sticky=tk.EW)
        
        input_frame.columnconfigure(0, weight=1)
        
        # Examples
        examples = ttk.Label(input_frame,
            text="Examples: in 30 minutes, in 2 hours, tomorrow at 3pm, next monday at 10am",
            foreground=self.FG_DIM,
            font=('Segoe UI', 8))
        examples.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Reminders list
        list_frame = ttk.Frame(main)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        list_label = ttk.Label(list_frame, text="Active Reminders:",
                              font=('Segoe UI', 10, 'bold'))
        list_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Scrollable canvas
        canvas = tk.Canvas(list_frame, bg=self.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.reminder_container = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        canvas_frame = canvas.create_window((0, 0), window=self.reminder_container, anchor=tk.NW)
        
        def _configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
            canvas.itemconfig(canvas_frame, width=event.width)
        
        self.reminder_container.bind('<Configure>', _configure_scroll)
        canvas.bind('<Configure>', _configure_scroll)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all('<MouseWheel>', _on_mousewheel)
    
    def _create_reminder(self):
        """Create new reminder"""
        desc = self.desc_entry.get().strip()
        time_phrase = self.time_entry.get().strip()
        
        if not desc:
            messagebox.showwarning("Missing Description", "Please enter a description")
            return
        
        if not time_phrase:
            messagebox.showwarning("Missing Time", "Please enter when to remind you")
            return
        
        result = self.manager.create_reminder(desc, time_phrase)
        
        if result['success']:
            self.desc_entry.delete(0, tk.END)
            self.time_entry.delete(0, tk.END)
            self._load_reminders()
            messagebox.showinfo("Success", f"Reminder created for {result['reminder']['scheduled_time']}")
        else:
            messagebox.showerror("Error", result['message'])
    
    def _load_reminders(self):
        """Load and display reminders"""
        # Clear existing
        for widget in self.reminder_container.winfo_children():
            widget.destroy()
        
        reminders = self.manager.get_all_active_reminders()
        
        if not reminders:
            no_reminders = ttk.Label(self.reminder_container,
                text="No active reminders. Create one above!",
                foreground=self.FG_DIM)
            no_reminders.pack(pady=20)
            return
        
        for i, reminder in enumerate(reminders):
            self._create_reminder_widget(reminder, i)
    
    def _create_reminder_widget(self, reminder, index):
        """Create widget for single reminder"""
        frame = tk.Frame(self.reminder_container,
            bg=self.BG_LIGHT,
            highlightbackground=self.BORDER,
            highlightthickness=1)
        frame.pack(fill=tk.X, pady=5, ipady=8, ipadx=10)
        
        # Status indicator
        is_overdue = reminder.get('is_overdue', False)
        status_color = self.ERROR if is_overdue else self.SUCCESS
        status_text = "OVERDUE" if is_overdue else "SCHEDULED"
        
        status = tk.Label(frame, text=status_text,
            bg=status_color, fg=self.BG,
            font=('Segoe UI', 7, 'bold'),
            padx=6, pady=2)
        status.pack(side=tk.LEFT, padx=(0, 10))
        
        # Content
        content_frame = tk.Frame(frame, bg=self.BG_LIGHT)
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        desc = tk.Label(content_frame,
            text=reminder['description'],
            bg=self.BG_LIGHT, fg=self.FG,
            font=('Segoe UI', 10, 'bold'),
            anchor=tk.W)
        desc.pack(fill=tk.X)
        
        if is_overdue:
            time_text = f"Overdue by {reminder['overdue_duration']}"
            time_color = self.ERROR
        else:
            time_text = f"Due in {reminder['time_until']} ({reminder['scheduled_time']})"
            time_color = self.FG_DIM
        
        time_label = tk.Label(content_frame,
            text=time_text,
            bg=self.BG_LIGHT, fg=time_color,
            font=('Segoe UI', 8),
            anchor=tk.W)
        time_label.pack(fill=tk.X)
        
        # Delete button
        del_btn = tk.Button(frame, text="✕",
            bg=self.BG_LIGHT, fg=self.FG_DIM,
            activebackground=self.ERROR, activeforeground=self.FG,
            font=('Segoe UI', 10, 'bold'),
            border=0, cursor='hand2',
            command=lambda: self._delete_reminder(reminder['id']))
        del_btn.pack(side=tk.RIGHT, padx=5)
        
        # Hover effects
        def on_enter(e):
            frame.configure(bg=self.BG_HOVER)
            content_frame.configure(bg=self.BG_HOVER)
            desc.configure(bg=self.BG_HOVER)
            time_label.configure(bg=self.BG_HOVER)
            del_btn.configure(bg=self.BG_HOVER)
        
        def on_leave(e):
            frame.configure(bg=self.BG_LIGHT)
            content_frame.configure(bg=self.BG_LIGHT)
            desc.configure(bg=self.BG_LIGHT)
            time_label.configure(bg=self.BG_LIGHT)
            del_btn.configure(bg=self.BG_LIGHT)
        
        frame.bind('<Enter>', on_enter)
        frame.bind('<Leave>', on_leave)
        content_frame.bind('<Enter>', on_enter)
        content_frame.bind('<Leave>', on_leave)
    
    def _delete_reminder(self, reminder_id):
        """Delete reminder"""
        result = self.manager.delete_reminder(reminder_id)
        
        if result['success']:
            self._load_reminders()
        else:
            messagebox.showerror("Error", result['message'])
    
    def _schedule_refresh(self):
        """Auto-refresh every 30 seconds"""
        self._load_reminders()
        self.root.after(30000, self._schedule_refresh)


def main():
    """Launch GUI"""
    root = tk.Tk()
    
    # Set project root (adjust as needed)
    project_root = Path.cwd()
    
    app = RemindersGUI(root, project_root=project_root)
    root.mainloop()


if __name__ == '__main__':
    main()
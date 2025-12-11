# Filename: BASE/tools/installed/youtube_chat/component.py
"""
YouTube Chat Tool - GUI Component
Dynamic GUI panel for YouTube live chat monitoring
"""
import tkinter as tk
from tkinter import ttk
from BASE.interface.gui_themes import DarkTheme


class YouTubeChatComponent:
    """
    GUI component for YouTube Chat tool
    Provides interface for monitoring and controlling YouTube live chat
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        """
        Initialize YouTube chat component
        
        Args:
            parent_gui: Main GUI instance
            ai_core: AI Core instance
            logger: Logger instance
        """
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        
        # Tool instance (will be set when available)
        self.youtube_tool = None
        
        # GUI elements
        self.panel_frame = None
        self.status_label = None
        self.video_id_var = None
        self.message_display = None
        self.start_button = None
        self.stop_button = None
        
        # Update timer
        self.update_job = None
    
    def create_panel(self, parent_frame):
        """
        Create the YouTube chat panel
        
        Args:
            parent_frame: Parent frame to add panel to
        """
        # Main panel frame
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="YouTube Live Chat",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Configuration section
        self._create_config_section()
        
        # Control section
        self._create_control_section()
        
        # Status section
        self._create_status_section()
        
        # Message display section
        self._create_message_section()
        
        # Start status updates
        self._schedule_status_update()
        
        return self.panel_frame
    
    def _create_config_section(self):
        """Create configuration section"""
        config_frame = ttk.Frame(self.panel_frame)
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Video ID label
        ttk.Label(
            config_frame,
            text="Video ID:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Video ID entry
        self.video_id_var = tk.StringVar()
        video_id_entry = ttk.Entry(
            config_frame,
            textvariable=self.video_id_var,
            width=30,
            font=("Consolas", 9)
        )
        video_id_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Load current video ID from config
        try:
            from BASE.tools.installed.youtube_chat import config
            self.video_id_var.set(config.YOUTUBE_VIDEO_ID)
        except:
            pass
        
        # Info label
        info_label = tk.Label(
            config_frame,
            text="ℹ️",
            font=("Segoe UI", 10),
            foreground=DarkTheme.ACCENT_PURPLE,
            background=DarkTheme.BG_DARKER,
            cursor="hand2"
        )
        info_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Tooltip for info
        self._create_tooltip(
            info_label,
            "Find Video ID in YouTube URL:\n"
            "youtube.com/watch?v=VIDEO_ID\n\n"
            "Example: dQw4w9WgXcQ\n\n"
            "Stream must be LIVE with chat enabled"
        )
    
    def _create_control_section(self):
        """Create control buttons section"""
        control_frame = ttk.Frame(self.panel_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Start button
        self.start_button = ttk.Button(
            control_frame,
            text="▶️ Start Monitoring",
            command=self._start_monitoring,
            width=20
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Stop button
        self.stop_button = ttk.Button(
            control_frame,
            text="⏹️ Stop Monitoring",
            command=self._stop_monitoring,
            width=20,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Clear button
        clear_button = ttk.Button(
            control_frame,
            text="🗑️ Clear Messages",
            command=self._clear_messages,
            width=20
        )
        clear_button.pack(side=tk.LEFT)
    
    def _create_status_section(self):
        """Create status display section"""
        status_frame = ttk.Frame(self.panel_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Status icon and text
        self.status_label = tk.Label(
            status_frame,
            text="⚫ Not Connected",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Refresh button
        refresh_button = ttk.Button(
            status_frame,
            text="🔄",
            command=self._refresh_status,
            width=3
        )
        refresh_button.pack(side=tk.RIGHT)
    
    def _create_message_section(self):
        """Create message display section"""
        message_frame = ttk.Frame(self.panel_frame)
        message_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Label
        ttk.Label(
            message_frame,
            text="Recent Chat Messages:",
            style="TLabel"
        ).pack(anchor=tk.W, pady=(0, 3))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(message_frame, orient='vertical')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Message display
        self.message_display = tk.Text(
            message_frame,
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 9),
            bg=DarkTheme.BG_DARK,
            fg=DarkTheme.FG_PRIMARY,
            insertbackground=DarkTheme.FG_PRIMARY,
            selectbackground=DarkTheme.ACCENT_PURPLE,
            selectforeground=DarkTheme.FG_PRIMARY,
            borderwidth=1,
            relief="solid",
            yscrollcommand=scrollbar.set
        )
        self.message_display.pack(fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.message_display.yview)
        
        # Configure message tags
        self.message_display.tag_configure(
            "timestamp",
            foreground=DarkTheme.FG_MUTED
        )
        self.message_display.tag_configure(
            "username",
            foreground=DarkTheme.ACCENT_PURPLE,
            font=("Consolas", 9, "bold")
        )
        self.message_display.tag_configure(
            "message",
            foreground=DarkTheme.FG_PRIMARY
        )
    
    def _start_monitoring(self):
        """Start YouTube chat monitoring"""
        video_id = self.video_id_var.get().strip()
        
        if not video_id:
            self._show_error("Please enter a Video ID")
            return
        
        # Get tool instance
        self.youtube_tool = self._get_youtube_tool()
        
        if not self.youtube_tool:
            self._show_error("YouTube tool not initialized")
            return
        
        # Update video ID in tool
        self.youtube_tool.video_id = video_id
        
        # Start monitoring
        if self.ai_core.main_loop:
            import asyncio
            
            async def start_async():
                result = await self.youtube_tool.execute('start', [])
                if result.get('success'):
                    self._update_status_connected()
                else:
                    error = result.get('content', 'Unknown error')
                    self._show_error(f"Failed to start: {error}")
            
            asyncio.run_coroutine_threadsafe(start_async(), self.ai_core.main_loop)
        
        self.logger.youtube("Starting YouTube chat monitoring...")
    
    def _stop_monitoring(self):
        """Stop YouTube chat monitoring"""
        self.youtube_tool = self._get_youtube_tool()
        
        if not self.youtube_tool:
            return
        
        if self.ai_core.main_loop:
            import asyncio
            
            async def stop_async():
                await self.youtube_tool.execute('stop', [])
                self._update_status_disconnected()
            
            asyncio.run_coroutine_threadsafe(stop_async(), self.ai_core.main_loop)
        
        self.logger.youtube("Stopping YouTube chat monitoring...")
    
    def _clear_messages(self):
        """Clear message display"""
        self.message_display.config(state=tk.NORMAL)
        self.message_display.delete("1.0", tk.END)
        self.message_display.config(state=tk.DISABLED)
        self.logger.youtube("Cleared message display")
    
    def _refresh_status(self):
        """Refresh status display"""
        self._update_status()
    
    def _update_status(self):
        """Update status display based on tool state"""
        self.youtube_tool = self._get_youtube_tool()
        
        if not self.youtube_tool:
            self._update_status_not_available()
            return
        
        if self.youtube_tool.is_available():
            self._update_status_connected()
            self._update_messages()
        else:
            self._update_status_disconnected()
    
    def _update_status_not_available(self):
        """Update UI for tool not available"""
        self.status_label.config(
            text="⚫ Tool Not Available",
            foreground=DarkTheme.FG_MUTED
        )
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
    
    def _update_status_connected(self):
        """Update UI for connected state"""
        self.status_label.config(
            text="🟢 Monitoring Active",
            foreground=DarkTheme.ACCENT_GREEN
        )
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
    
    def _update_status_disconnected(self):
        """Update UI for disconnected state"""
        self.status_label.config(
            text="⚫ Not Connected",
            foreground=DarkTheme.FG_MUTED
        )
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def _update_messages(self):
        """Update message display with recent messages"""
        if not self.youtube_tool:
            return
        
        try:
            # Get recent messages from tool
            messages = self.youtube_tool.get_context_for_ai()
            
            if not messages:
                return
            
            # Parse and display messages
            self.message_display.config(state=tk.NORMAL)
            
            # Only add new messages (check if last message matches)
            current_content = self.message_display.get("1.0", tk.END)
            
            for line in messages.split('\n'):
                if line.strip() and line not in current_content:
                    # Parse message format: "username: message"
                    if ':' in line:
                        username, message = line.split(':', 1)
                        
                        # Add timestamp
                        from datetime import datetime
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        self.message_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
                        self.message_display.insert(tk.END, f"{username.strip()}: ", "username")
                        self.message_display.insert(tk.END, f"{message.strip()}\n", "message")
            
            self.message_display.config(state=tk.DISABLED)
            self.message_display.see(tk.END)
        
        except Exception as e:
            self.logger.warning(f"Error updating messages: {e}")
    
    def _schedule_status_update(self):
        """Schedule periodic status updates"""
        if self.panel_frame and self.panel_frame.winfo_exists():
            self._update_status()
            # Schedule next update in 2 seconds
            self.update_job = self.panel_frame.after(2000, self._schedule_status_update)
    
    def _get_youtube_tool(self):
        """Get YouTube tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'youtube_chat' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('youtube_chat')
    
    def _show_error(self, message: str):
        """Show error message"""
        self.status_label.config(
            text=f"❌ {message}",
            foreground=DarkTheme.ACCENT_RED
        )
        self.logger.error(f"[YouTube] {message}")
    
    def _create_tooltip(self, widget, text):
        """Create tooltip for widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            tooltip.configure(bg=DarkTheme.BG_DARK)
            
            label = tk.Label(
                tooltip,
                text=text,
                background=DarkTheme.BG_DARK,
                foreground=DarkTheme.FG_PRIMARY,
                font=("Segoe UI", 9),
                wraplength=300,
                padx=8,
                pady=4,
                justify=tk.LEFT
            )
            label.pack()
            
            widget.tooltip = tooltip
        
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
    
    def cleanup(self):
        """Cleanup component resources"""
        # Cancel scheduled updates
        if self.update_job:
            try:
                self.panel_frame.after_cancel(self.update_job)
            except:
                pass
        
        self.logger.youtube("YouTube component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        YouTubeChatComponent instance
    """
    return YouTubeChatComponent(parent_gui, ai_core, logger)
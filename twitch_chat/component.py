# Filename: BASE/tools/installed/twitch_chat/component.py
"""
Twitch Chat Tool - GUI Component
Dynamic GUI panel for Twitch IRC chat monitoring
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from BASE.interface.gui_themes import DarkTheme


class TwitchChatComponent:
    """
    GUI component for Twitch Chat tool
    Provides interface for monitoring and controlling Twitch IRC chat
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        """
        Initialize Twitch chat component
        
        Args:
            parent_gui: Main GUI instance
            ai_core: AI Core instance
            logger: Logger instance
        """
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        
        # Tool instance (will be set when available)
        self.twitch_tool = None
        
        # GUI elements
        self.panel_frame = None
        self.status_label = None
        self.channel_var = None
        self.oauth_var = None
        self.nickname_var = None
        self.message_display = None
        self.message_entry = None
        self.start_button = None
        self.stop_button = None
        self.send_button = None
        self.stats_label = None
        self.batch_status_label = None
        
        # Update timer
        self.update_job = None
    
    def create_panel(self, parent_frame):
        """
        Create the Twitch chat panel
        
        Args:
            parent_frame: Parent frame to add panel to
        """
        # Main panel frame
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="Twitch Live Chat (IRC)",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Configuration section
        self._create_config_section()
        
        # OAuth section (collapsible)
        self._create_oauth_section()
        
        # Status and control section
        self._create_control_section()
        
        # Message display section
        self._create_message_section()
        
        # Send message section
        self._create_send_section()
        
        # Statistics section
        self._create_stats_section()
        
        # Start status updates
        self._schedule_status_update()
        
        return self.panel_frame
    
    def _create_config_section(self):
        """Create configuration section"""
        config_frame = ttk.Frame(self.panel_frame)
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Channel input
        ttk.Label(
            config_frame,
            text="Channel:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.channel_var = tk.StringVar()
        channel_entry = ttk.Entry(
            config_frame,
            textvariable=self.channel_var,
            width=20,
            font=("Consolas", 9)
        )
        channel_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # Load current channel from config
        try:
            from BASE.tools.installed.twitch_chat import config
            self.channel_var.set(config.TWITCH_CHANNEL)
        except:
            pass
        
        # Set button
        ttk.Button(
            config_frame,
            text="Set",
            command=self._save_channel,
            width=8
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Info icon
        info_label = tk.Label(
            config_frame,
            text="ℹ️",
            font=("Segoe UI", 10),
            foreground=DarkTheme.ACCENT_PURPLE,
            background=DarkTheme.BG_DARKER,
            cursor="hand2"
        )
        info_label.pack(side=tk.RIGHT)
        
        self._create_tooltip(
            info_label,
            "Enter channel name without # symbol\n"
            "Example: 'shroud' for twitch.tv/shroud\n\n"
            "Anonymous mode (no OAuth): Read-only\n"
            "Authenticated mode (with OAuth): Can send messages"
        )
    
    def _create_oauth_section(self):
        """Create OAuth authentication section (collapsible)"""
        oauth_container = ttk.Frame(self.panel_frame)
        oauth_container.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Toggle button
        self.oauth_toggle_btn = ttk.Button(
            oauth_container,
            text="▶ Authentication (Optional)",
            command=self._toggle_oauth,
            width=30
        )
        self.oauth_toggle_btn.pack(anchor=tk.W)
        
        # OAuth frame (initially hidden)
        self.oauth_frame = ttk.LabelFrame(
            oauth_container,
            text="OAuth Settings",
            style="Dark.TLabelframe"
        )
        
        # OAuth token
        oauth_token_frame = ttk.Frame(self.oauth_frame)
        oauth_token_frame.pack(fill=tk.X, padx=3, pady=2)
        
        tk.Label(
            oauth_token_frame,
            text="OAuth Token:",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.oauth_var = tk.StringVar()
        oauth_entry = ttk.Entry(
            oauth_token_frame,
            textvariable=self.oauth_var,
            show="*",
            width=30
        )
        oauth_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(
            oauth_token_frame,
            text="?",
            command=self._show_oauth_help,
            width=3
        ).pack(side=tk.RIGHT)
        
        # Nickname
        nickname_frame = ttk.Frame(self.oauth_frame)
        nickname_frame.pack(fill=tk.X, padx=3, pady=2)
        
        tk.Label(
            nickname_frame,
            text="Nickname:",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.nickname_var = tk.StringVar()
        ttk.Entry(
            nickname_frame,
            textvariable=self.nickname_var,
            width=20
        ).pack(side=tk.LEFT)
        
        # Load OAuth settings
        try:
            from BASE.tools.installed.twitch_chat import config
            self.oauth_var.set(config.TWITCH_OAUTH_TOKEN)
            self.nickname_var.set(config.TWITCH_NICKNAME)
        except:
            pass
    
    def _create_control_section(self):
        """Create status and control buttons section"""
        control_frame = ttk.Frame(self.panel_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        # Status label
        self.status_label = tk.Label(
            control_frame,
            text="⚫ Not Connected",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Control buttons
        button_container = ttk.Frame(control_frame)
        button_container.pack(side=tk.RIGHT)
        
        self.start_button = ttk.Button(
            button_container,
            text="▶️ Start",
            command=self._start_monitoring,
            width=10
        )
        self.start_button.pack(side=tk.LEFT, padx=2)
        
        self.stop_button = ttk.Button(
            button_container,
            text="⏹️ Stop",
            command=self._stop_monitoring,
            width=10,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=2)
    
    def _create_message_section(self):
        """Create message display section"""
        message_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Chat Messages",
            style="Dark.TLabelframe"
        )
        message_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(message_frame, orient='vertical')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Message display
        self.message_display = tk.Text(
            message_frame,
            height=10,
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
        self.message_display.tag_configure(
            "system",
            foreground=DarkTheme.ACCENT_YELLOW,
            font=("Consolas", 9, "italic")
        )
        
        # Clear button
        ttk.Button(
            message_frame,
            text="🗑️ Clear",
            command=self._clear_messages,
            width=10
        ).pack(pady=2)
    
    def _create_send_section(self):
        """Create send message section"""
        send_frame = ttk.Frame(self.panel_frame)
        send_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.message_entry = ttk.Entry(
            send_frame,
            font=("Segoe UI", 9),
            state=tk.DISABLED
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_entry.bind('<Return>', lambda e: self._send_message())
        
        self.send_button = ttk.Button(
            send_frame,
            text="Send",
            command=self._send_message,
            width=10,
            state=tk.DISABLED
        )
        self.send_button.pack(side=tk.RIGHT)
    
    def _create_stats_section(self):
        """Create statistics section"""
        stats_frame = ttk.Frame(self.panel_frame)
        stats_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.stats_label = tk.Label(
            stats_frame,
            text="Messages: 0 | Mode: Not Connected",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.stats_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Batch status indicator
        self.batch_status_label = tk.Label(
            stats_frame,
            text="📦 Batch: OFF",
            font=("Segoe UI", 8),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER
        )
        self.batch_status_label.pack(side=tk.RIGHT)
    
    def _toggle_oauth(self):
        """Toggle OAuth section visibility"""
        if self.oauth_frame.winfo_ismapped():
            self.oauth_frame.pack_forget()
            self.oauth_toggle_btn.config(text="▶ Authentication (Optional)")
        else:
            self.oauth_frame.pack(fill=tk.X, padx=5, pady=5, after=self.oauth_toggle_btn)
            self.oauth_toggle_btn.config(text="▼ Authentication (Optional)")
    
    def _show_oauth_help(self):
        """Show OAuth help dialog"""
        help_text = """OAuth Token for Twitch

To get an OAuth token:
1. Visit: https://twitchapps.com/tmi/
2. Click 'Connect' and authorize
3. Copy the token (starts with 'oauth:')
4. Paste it in the OAuth field

Without OAuth:
• Read-only mode (justinfan)
• Cannot send messages

With OAuth:
• Can send messages to chat
• Use your custom nickname"""
        
        messagebox.showinfo("OAuth Help", help_text)
    
    def _save_channel(self):
        """Save channel configuration"""
        channel = self.channel_var.get().strip().lower().lstrip('#')
        
        if not channel:
            messagebox.showwarning("Invalid Input", "Please enter a Twitch channel name")
            return
        
        try:
            # Update config file
            import re
            from pathlib import Path
            
            config_path = Path(__file__).parent / 'config.py'
            
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Update channel
            content = re.sub(
                r'TWITCH_CHANNEL = ".*"',
                f'TWITCH_CHANNEL = "{channel}"',
                content
            )
            
            # Update OAuth if provided
            oauth = self.oauth_var.get().strip()
            if oauth:
                content = re.sub(
                    r'TWITCH_OAUTH_TOKEN = ".*"',
                    f'TWITCH_OAUTH_TOKEN = "{oauth}"',
                    content
                )
            
            # Update nickname if provided
            nickname = self.nickname_var.get().strip()
            if nickname:
                content = re.sub(
                    r'TWITCH_NICKNAME = ".*"',
                    f'TWITCH_NICKNAME = "{nickname}"',
                    content
                )
            
            with open(config_path, 'w') as f:
                f.write(content)
            
            mode = "authenticated" if oauth else "anonymous (read-only)"
            self.logger.twitch(f"✅ Channel configured: #{channel} ({mode})")
            messagebox.showinfo("Success", f"Channel configured:\n#{channel}\nMode: {mode}")
            
        except Exception as e:
            self.logger.error(f"Failed to save channel: {e}")
            messagebox.showerror("Error", f"Failed to save:\n{e}")
    
    def _start_monitoring(self):
        """Start Twitch chat monitoring"""
        self.twitch_tool = self._get_twitch_tool()
        
        if not self.twitch_tool:
            messagebox.showerror("Error", "Twitch tool not initialized")
            return
        
        self.logger.twitch("🚀 Starting Twitch chat monitoring...")
        
        if self.ai_core.main_loop:
            import asyncio
            
            async def start_async():
                result = await self.twitch_tool.execute('start', [])
                if result.get('success'):
                    self._update_status_connected()
                    self.logger.twitch("✅ Monitoring started")
                else:
                    error = result.get('content', 'Unknown error')
                    self._show_error(f"Failed to start: {error}")
            
            asyncio.run_coroutine_threadsafe(start_async(), self.ai_core.main_loop)
    
    def _stop_monitoring(self):
        """Stop Twitch chat monitoring"""
        self.twitch_tool = self._get_twitch_tool()
        
        if not self.twitch_tool:
            return
        
        if self.ai_core.main_loop:
            import asyncio
            
            async def stop_async():
                await self.twitch_tool.execute('stop', [])
                self._update_status_disconnected()
                self.logger.twitch("⏹️ Monitoring stopped")
            
            asyncio.run_coroutine_threadsafe(stop_async(), self.ai_core.main_loop)
    
    def _send_message(self):
        """Send message to Twitch chat"""
        message = self.message_entry.get().strip()
        
        if not message:
            return
        
        self.twitch_tool = self._get_twitch_tool()
        
        if not self.twitch_tool or not self.twitch_tool.is_available():
            messagebox.showwarning("Not Connected", "Twitch chat is not running")
            return
        
        if self.ai_core.main_loop:
            import asyncio
            
            async def send_async():
                result = await self.twitch_tool.execute('send_message', [message])
                if result.get('success'):
                    self.message_entry.delete(0, tk.END)
                    self._log_message("[You]", message, "system")
                    self.logger.twitch(f"✅ Sent: {message}")
                else:
                    error = result.get('content', 'Unknown error')
                    messagebox.showerror("Send Failed", f"Failed to send:\n{error}")
            
            asyncio.run_coroutine_threadsafe(send_async(), self.ai_core.main_loop)
    
    def _clear_messages(self):
        """Clear message display"""
        self.message_display.config(state=tk.NORMAL)
        self.message_display.delete("1.0", tk.END)
        self.message_display.config(state=tk.DISABLED)
        self.logger.twitch("🗑️ Messages cleared")
    
    def _update_status(self):
        """Update status display"""
        self.twitch_tool = self._get_twitch_tool()
        
        if not self.twitch_tool:
            self._update_status_not_available()
            return
        
        if self.twitch_tool.is_available():
            self._update_status_connected()
            self._update_messages()
            self._update_stats()
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
        
        # Enable send if authenticated
        oauth = self.oauth_var.get().strip()
        if oauth:
            self.message_entry.config(state=tk.NORMAL)
            self.send_button.config(state=tk.NORMAL)
    
    def _update_status_disconnected(self):
        """Update UI for disconnected state"""
        self.status_label.config(
            text="⚫ Not Connected",
            foreground=DarkTheme.FG_MUTED
        )
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.message_entry.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
    
    def _update_messages(self):
        """Update message display with recent messages"""
        if not self.twitch_tool:
            return
        
        try:
            # Get recent messages
            context = self.twitch_tool.get_context_for_ai()
            
            if not context:
                return
            
            # Get current content
            current_content = self.message_display.get("1.0", tk.END)
            
            # Parse and add new messages
            self.message_display.config(state=tk.NORMAL)
            
            for line in context.split('\n'):
                if line.strip() and line not in current_content:
                    if ':' in line:
                        username, message = line.split(':', 1)
                        self._log_message(username.strip(), message.strip(), "chat")
            
            self.message_display.config(state=tk.DISABLED)
            
        except Exception as e:
            self.logger.warning(f"Error updating messages: {e}")
    
    def _update_stats(self):
        """Update statistics display"""
        if not self.twitch_tool:
            return
        
        try:
            status = self.twitch_tool.get_status()
            
            mode = status.get('mode', 'unknown')
            buffered = status.get('buffered', 0)
            unbatched = status.get('unbatched', 0)
            
            self.stats_label.config(
                text=f"Messages: {buffered} buffered | Mode: {mode}"
            )
            
            # Update batch status
            if status.get('batching_enabled'):
                batch_interval = status.get('batch_interval', 0)
                batch_active = status.get('batch_callback_active', False)
                
                if batch_active:
                    self.batch_status_label.config(
                        text=f"📦 Batch: ON ({batch_interval}s) | Pending: {unbatched}",
                        foreground=DarkTheme.ACCENT_GREEN
                    )
                else:
                    self.batch_status_label.config(
                        text=f"📦 Batch: INACTIVE",
                        foreground=DarkTheme.ACCENT_YELLOW
                    )
            else:
                self.batch_status_label.config(
                    text="📦 Batch: OFF",
                    foreground=DarkTheme.FG_MUTED
                )
            
        except Exception as e:
            self.logger.warning(f"Error updating stats: {e}")
    
    def _log_message(self, username: str, message: str, msg_type: str = "chat"):
        """Log message to display"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.message_display.config(state=tk.NORMAL)
        self.message_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        if msg_type == "system":
            self.message_display.insert(tk.END, f"{username}: {message}\n", "system")
        else:
            self.message_display.insert(tk.END, f"{username}: ", "username")
            self.message_display.insert(tk.END, f"{message}\n", "message")
        
        self.message_display.see(tk.END)
        self.message_display.config(state=tk.DISABLED)
    
    def _schedule_status_update(self):
        """Schedule periodic status updates"""
        if self.panel_frame and self.panel_frame.winfo_exists():
            self._update_status()
            # Schedule next update in 2 seconds
            self.update_job = self.panel_frame.after(2000, self._schedule_status_update)
    
    def _get_twitch_tool(self):
        """Get Twitch tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'twitch_chat' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('twitch_chat')
    
    def _show_error(self, message: str):
        """Show error message"""
        self.status_label.config(
            text=f"❌ {message}",
            foreground=DarkTheme.ACCENT_RED
        )
        self.logger.error(f"[Twitch] {message}")
        messagebox.showerror("Error", message)
    
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
        
        self.logger.twitch("Twitch component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        TwitchChatComponent instance
    """
    return TwitchChatComponent(parent_gui, ai_core, logger)
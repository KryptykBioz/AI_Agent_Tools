# Filename: BASE/tools/installed/discord_chat/component.py
"""
Discord Chat Tool - GUI Component
Dynamic GUI panel for Discord bot integration
"""
import tkinter as tk
from tkinter import ttk, messagebox
from BASE.interface.gui_themes import DarkTheme


class DiscordChatComponent:
    """
    GUI component for Discord Chat tool
    Provides interface for monitoring and controlling Discord bot
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        """
        Initialize Discord chat component
        
        Args:
            parent_gui: Main GUI instance
            ai_core: AI Core instance
            logger: Logger instance
        """
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        
        # Tool instance (will be set when available)
        self.discord_tool = None
        
        # GUI elements
        self.panel_frame = None
        self.status_label = None
        self.token_var = None
        self.prefix_var = None
        self.auto_start_var = None
        self.channels_var = None
        self.guilds_var = None
        self.respond_mentions_var = None
        self.respond_replies_var = None
        self.start_button = None
        self.stop_button = None
        self.stats_text = None
        
        # Update timer
        self.update_job = None
    
    def create_panel(self, parent_frame):
        """
        Create the Discord chat panel
        
        Args:
            parent_frame: Parent frame to add panel to
        """
        # Main panel frame
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="Discord Bot Control",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Configuration section
        self._create_config_section()
        
        # Status section
        self._create_status_section()
        
        # Control section
        self._create_control_section()
        
        # Statistics section
        self._create_stats_section()
        
        # Start status updates
        self._schedule_status_update()
        
        return self.panel_frame
    
    def _create_config_section(self):
        """Create configuration section"""
        config_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Configuration",
            style="Dark.TLabelframe"
        )
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Bot Token
        token_frame = ttk.Frame(config_frame)
        token_frame.pack(fill=tk.X, padx=3, pady=2)
        
        tk.Label(
            token_frame,
            text="Bot Token:",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER,
            width=15,
            anchor="w"
        ).pack(side=tk.LEFT)
        
        self.token_var = tk.StringVar()
        token_entry = ttk.Entry(token_frame, textvariable=self.token_var, show="*", width=40)
        token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        ttk.Button(
            token_frame,
            text="Show",
            command=lambda: self._toggle_token_visibility(token_entry),
            width=6
        ).pack(side=tk.LEFT, padx=2)
        
        # Load current token
        try:
            from BASE.tools.installed.discord_chat import config
            self.token_var.set(config.DISCORD_BOT_TOKEN)
        except:
            pass
        
        # Command Prefix
        prefix_frame = ttk.Frame(config_frame)
        prefix_frame.pack(fill=tk.X, padx=3, pady=2)
        
        tk.Label(
            prefix_frame,
            text="Command Prefix:",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER,
            width=15,
            anchor="w"
        ).pack(side=tk.LEFT)
        
        self.prefix_var = tk.StringVar(value="!")
        ttk.Entry(prefix_frame, textvariable=self.prefix_var, width=10).pack(side=tk.LEFT, padx=2)
        
        # Auto Start
        self.auto_start_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            prefix_frame,
            text="Auto-start on launch",
            variable=self.auto_start_var
        ).pack(side=tk.LEFT, padx=10)
        
        # Allowed Channels
        channels_frame = ttk.Frame(config_frame)
        channels_frame.pack(fill=tk.X, padx=3, pady=2)
        
        tk.Label(
            channels_frame,
            text="Allowed Channels:",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER,
            width=15,
            anchor="w"
        ).pack(side=tk.LEFT)
        
        self.channels_var = tk.StringVar()
        ttk.Entry(channels_frame, textvariable=self.channels_var, width=40).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=2
        )
        
        tk.Label(
            channels_frame,
            text="(comma-separated IDs)",
            font=("Segoe UI", 8),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER
        ).pack(side=tk.LEFT, padx=2)
        
        # Allowed Guilds
        guilds_frame = ttk.Frame(config_frame)
        guilds_frame.pack(fill=tk.X, padx=3, pady=2)
        
        tk.Label(
            guilds_frame,
            text="Allowed Guilds:",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER,
            width=15,
            anchor="w"
        ).pack(side=tk.LEFT)
        
        self.guilds_var = tk.StringVar()
        ttk.Entry(guilds_frame, textvariable=self.guilds_var, width=40).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=2
        )
        
        tk.Label(
            guilds_frame,
            text="(comma-separated IDs)",
            font=("Segoe UI", 8),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER
        ).pack(side=tk.LEFT, padx=2)
        
        # Behavior options
        behavior_frame = ttk.Frame(config_frame)
        behavior_frame.pack(fill=tk.X, padx=3, pady=2)
        
        tk.Label(
            behavior_frame,
            text="Respond to:",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER,
            width=15,
            anchor="w"
        ).pack(side=tk.LEFT)
        
        self.respond_mentions_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(behavior_frame, text="Mentions", variable=self.respond_mentions_var).pack(
            side=tk.LEFT, padx=5
        )
        
        self.respond_replies_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(behavior_frame, text="Replies", variable=self.respond_replies_var).pack(
            side=tk.LEFT, padx=5
        )
        
        # Save button
        button_frame = ttk.Frame(config_frame)
        button_frame.pack(fill=tk.X, padx=3, pady=5)
        
        ttk.Button(
            button_frame,
            text="💾 Save Settings",
            command=self._save_settings,
            width=15
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            button_frame,
            text="🔄 Reload",
            command=self._reload_settings,
            width=15
        ).pack(side=tk.LEFT, padx=2)
    
    def _create_status_section(self):
        """Create status display section"""
        status_frame = ttk.Frame(self.panel_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(
            status_frame,
            text="Status:",
            font=("Segoe UI", 9, "bold"),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER
        ).pack(side=tk.LEFT)
        
        self.status_label = tk.Label(
            status_frame,
            text="🔴 Not Connected",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER
        )
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
    
    def _create_control_section(self):
        """Create control buttons section"""
        control_frame = ttk.Frame(self.panel_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.start_button = ttk.Button(
            control_frame,
            text="▶️ Start Bot",
            command=self._start_bot,
            width=12
        )
        self.start_button.pack(side=tk.LEFT, padx=2)
        
        self.stop_button = ttk.Button(
            control_frame,
            text="⏹️ Stop Bot",
            command=self._stop_bot,
            width=12,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            control_frame,
            text="🔄 Refresh Status",
            command=self._refresh_status,
            width=15
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            control_frame,
            text="🧪 Test Connection",
            command=self._test_connection,
            width=15
        ).pack(side=tk.LEFT, padx=2)
    
    def _create_stats_section(self):
        """Create statistics display section"""
        stats_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Statistics",
            style="Dark.TLabelframe"
        )
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        self.stats_text = tk.Text(
            stats_frame,
            height=6,
            font=("Consolas", 8),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER,
            borderwidth=0,
            highlightthickness=0,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
    
    def _toggle_token_visibility(self, entry_widget):
        """Toggle token visibility"""
        current = entry_widget.cget('show')
        entry_widget.config(show='' if current == '*' else '*')
    
    def _save_settings(self):
        """Save Discord settings to config file"""
        try:
            token = self.token_var.get().strip()
            if not token:
                messagebox.showwarning("Invalid Token", "Bot token cannot be empty")
                return
            
            # Parse channel and guild IDs
            channels = []
            if self.channels_var.get().strip():
                try:
                    channels = [int(x.strip()) for x in self.channels_var.get().split(',') if x.strip()]
                except ValueError:
                    messagebox.showerror("Invalid Input", "Channel IDs must be numbers")
                    return
            
            guilds = []
            if self.guilds_var.get().strip():
                try:
                    guilds = [int(x.strip()) for x in self.guilds_var.get().split(',') if x.strip()]
                except ValueError:
                    messagebox.showerror("Invalid Input", "Guild IDs must be numbers")
                    return
            
            # Update config file
            import json
            from pathlib import Path
            
            config_path = Path(__file__).parent / 'config.py'
            
            # Read current config
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Update values using regex
            import re
            
            content = re.sub(
                r'DISCORD_BOT_TOKEN = ".*"',
                f'DISCORD_BOT_TOKEN = "{token}"',
                content
            )
            
            content = re.sub(
                r'DISCORD_COMMAND_PREFIX = ".*"',
                f'DISCORD_COMMAND_PREFIX = "{self.prefix_var.get().strip()}"',
                content
            )
            
            content = re.sub(
                r'DISCORD_AUTO_START = (True|False)',
                f'DISCORD_AUTO_START = {self.auto_start_var.get()}',
                content
            )
            
            channels_str = str(channels) if channels else "None"
            content = re.sub(
                r'DISCORD_ALLOWED_CHANNELS = .*',
                f'DISCORD_ALLOWED_CHANNELS = {channels_str}',
                content
            )
            
            guilds_str = str(guilds) if guilds else "None"
            content = re.sub(
                r'DISCORD_ALLOWED_GUILDS = .*',
                f'DISCORD_ALLOWED_GUILDS = {guilds_str}',
                content
            )
            
            content = re.sub(
                r'DISCORD_RESPOND_TO_MENTIONS = (True|False)',
                f'DISCORD_RESPOND_TO_MENTIONS = {self.respond_mentions_var.get()}',
                content
            )
            
            content = re.sub(
                r'DISCORD_RESPOND_TO_REPLIES = (True|False)',
                f'DISCORD_RESPOND_TO_REPLIES = {self.respond_replies_var.get()}',
                content
            )
            
            # Write back
            with open(config_path, 'w') as f:
                f.write(content)
            
            self.logger.discord("✅ Settings saved to config.py")
            messagebox.showinfo("Success", "Settings saved! Restart the bot for changes to take effect.")
            
        except Exception as e:
            self.logger.error(f"Failed to save Discord settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")
    
    def _reload_settings(self):
        """Reload settings from config file"""
        try:
            # Force reload of config module
            import importlib
            from BASE.tools.installed.discord_chat import config
            importlib.reload(config)
            
            # Update UI
            self.token_var.set(config.DISCORD_BOT_TOKEN)
            self.prefix_var.set(config.DISCORD_COMMAND_PREFIX)
            self.auto_start_var.set(config.DISCORD_AUTO_START)
            
            channels_val = ','.join(map(str, config.DISCORD_ALLOWED_CHANNELS)) if config.DISCORD_ALLOWED_CHANNELS else ""
            self.channels_var.set(channels_val)
            
            guilds_val = ','.join(map(str, config.DISCORD_ALLOWED_GUILDS)) if config.DISCORD_ALLOWED_GUILDS else ""
            self.guilds_var.set(guilds_val)
            
            self.respond_mentions_var.set(getattr(config, 'DISCORD_RESPOND_TO_MENTIONS', True))
            self.respond_replies_var.set(getattr(config, 'DISCORD_RESPOND_TO_REPLIES', True))
            
            self.logger.discord("🔄 Settings reloaded from config.py")
            
        except Exception as e:
            self.logger.error(f"Failed to reload settings: {e}")
    
    def _test_connection(self):
        """Test Discord bot connection"""
        token = self.token_var.get().strip()
        if not token:
            messagebox.showwarning("No Token", "Please enter a bot token first")
            return
        
        self.logger.discord("🧪 Testing Discord connection...")
        
        try:
            import discord
            import asyncio
            
            async def test():
                intents = discord.Intents.default()
                client = discord.Client(intents=intents)
                
                @client.event
                async def on_ready():
                    self.logger.discord(f"✅ Connected as {client.user}")
                    self.logger.discord(f"Bot ID: {client.user.id}")
                    await client.close()
                
                try:
                    await asyncio.wait_for(client.start(token), timeout=10)
                except asyncio.TimeoutError:
                    await client.close()
            
            asyncio.run(test())
            messagebox.showinfo("Success", "Connection test successful!")
            
        except discord.LoginFailure:
            self.logger.error("❌ Invalid token")
            messagebox.showerror("Error", "Invalid bot token")
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            messagebox.showerror("Error", f"Connection test failed:\n{e}")
    
    def _start_bot(self):
        """Start Discord bot"""
        self.discord_tool = self._get_discord_tool()
        
        if not self.discord_tool:
            messagebox.showerror("Error", "Discord tool not initialized")
            return
        
        if self.ai_core.main_loop:
            import asyncio
            
            async def start_async():
                result = await self.discord_tool.execute('start', [])
                if result.get('success'):
                    self._update_status_connected()
                    self.logger.discord("✅ Discord bot started")
                else:
                    error = result.get('content', 'Unknown error')
                    messagebox.showerror("Error", f"Failed to start: {error}")
            
            asyncio.run_coroutine_threadsafe(start_async(), self.ai_core.main_loop)
        else:
            messagebox.showerror("Error", "AI Core event loop not available")
    
    def _stop_bot(self):
        """Stop Discord bot"""
        self.discord_tool = self._get_discord_tool()
        
        if not self.discord_tool:
            return
        
        if self.ai_core.main_loop:
            import asyncio
            
            async def stop_async():
                await self.discord_tool.execute('stop', [])
                self._update_status_disconnected()
                self.logger.discord("⏹️ Discord bot stopped")
            
            asyncio.run_coroutine_threadsafe(stop_async(), self.ai_core.main_loop)
    
    def _refresh_status(self):
        """Refresh status display"""
        self._update_status()
    
    def _update_status(self):
        """Update status display based on tool state"""
        self.discord_tool = self._get_discord_tool()
        
        if not self.discord_tool:
            self._update_status_not_available()
            return
        
        if self.discord_tool.is_available():
            self._update_status_connected()
        else:
            self._update_status_disconnected()
        
        # Update statistics
        self._update_stats()
    
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
            text="🟢 Bot Online",
            foreground=DarkTheme.ACCENT_GREEN
        )
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
    
    def _update_status_disconnected(self):
        """Update UI for disconnected state"""
        self.status_label.config(
            text="🔴 Bot Offline",
            foreground=DarkTheme.ACCENT_RED
        )
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def _update_stats(self):
        """Update statistics display"""
        if not self.discord_tool:
            return
        
        try:
            status = self.discord_tool.get_status()
            
            stats_text = f"""Messages Received: {status.get('messages_received', 0)}
Messages Sent: {status.get('messages_sent', 0)}
Errors: {status.get('errors', 0)}
Guilds: {status.get('guilds', 0)}
Connected: {'Yes' if status.get('connected') else 'No'}
Prefix: {status.get('command_prefix', '!')}"""
            
            self.stats_text.config(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
            self.stats_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.logger.warning(f"Error updating stats: {e}")
    
    def _schedule_status_update(self):
        """Schedule periodic status updates"""
        if self.panel_frame and self.panel_frame.winfo_exists():
            self._update_status()
            # Schedule next update in 3 seconds
            self.update_job = self.panel_frame.after(3000, self._schedule_status_update)
    
    def _get_discord_tool(self):
        """Get Discord tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'discord_chat' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('discord_chat')
    
    def cleanup(self):
        """Cleanup component resources"""
        # Cancel scheduled updates
        if self.update_job:
            try:
                self.panel_frame.after_cancel(self.update_job)
            except:
                pass
        
        self.logger.discord("Discord component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        DiscordChatComponent instance
    """
    return DiscordChatComponent(parent_gui, ai_core, logger)
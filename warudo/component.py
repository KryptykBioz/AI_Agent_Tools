# Filename: BASE/tools/installed/warudo/component.py
"""
Warudo Tool - GUI Component
Dynamic GUI panel for Warudo avatar animation control
Follows modular tool panel system architecture
"""
import tkinter as tk
from tkinter import ttk
from BASE.interface.gui_themes import DarkTheme


class WarudoComponent:
    """
    GUI component for Warudo Tool
    Provides interface for controlling avatar animations and emotions
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        """
        Initialize Warudo component
        
        Args:
            parent_gui: Main GUI instance
            ai_core: AI Core instance
            logger: Logger instance
        """
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        
        # Tool instance (will be set when available)
        self.warudo_tool = None
        
        # GUI elements
        self.panel_frame = None
        self.status_label = None
        self.ws_url_var = None
        self.last_command_label = None
        self.connect_button = None
        self.disconnect_button = None
        
        # Update timer
        self.update_job = None
    
    def create_panel(self, parent_frame):
        """
        Create the Warudo control panel
        
        Args:
            parent_frame: Parent frame to add panel to
        """
        # Main panel frame
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="🎭 Warudo Avatar Control",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Configuration section
        self._create_config_section()
        
        # Control section
        self._create_control_section()
        
        # Status section
        self._create_status_section()
        
        # Emotions section
        self._create_emotions_section()
        
        # Animations section
        self._create_animations_section()
        
        # Start status updates
        self._schedule_status_update()
        
        return self.panel_frame
    
    def _create_config_section(self):
        """Create configuration section"""
        config_frame = ttk.Frame(self.panel_frame)
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # WebSocket URL label
        ttk.Label(
            config_frame,
            text="WebSocket URL:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # WebSocket URL entry
        self.ws_url_var = tk.StringVar()
        ws_url_entry = ttk.Entry(
            config_frame,
            textvariable=self.ws_url_var,
            width=30,
            font=("Consolas", 9)
        )
        ws_url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Load current URL from config
        try:
            from BASE.tools.installed.warudo import config
            url = getattr(config, 'WARUDO_WEBSOCKET_URL', 'ws://127.0.0.1:19190')
            self.ws_url_var.set(url)
        except:
            self.ws_url_var.set('ws://127.0.0.1:19190')
        
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
            "Warudo WebSocket Connection\n\n"
            "Default: ws://127.0.0.1:19190\n\n"
            "Requirements:\n"
            "- Warudo application running\n"
            "- WebSocket server enabled in Warudo\n"
            "- Port 19190 not blocked by firewall"
        )
    
    def _create_control_section(self):
        """Create control buttons section"""
        control_frame = ttk.Frame(self.panel_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Connect button
        self.connect_button = ttk.Button(
            control_frame,
            text="▶️ Connect",
            command=self._connect,
            width=15
        )
        self.connect_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Disconnect button
        self.disconnect_button = ttk.Button(
            control_frame,
            text="⏹️ Disconnect",
            command=self._disconnect,
            width=15,
            state=tk.DISABLED
        )
        self.disconnect_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Test button
        test_button = ttk.Button(
            control_frame,
            text="🧪 Test",
            command=self._test_connection,
            width=15
        )
        test_button.pack(side=tk.LEFT)
    
    def _create_status_section(self):
        """Create status display section"""
        status_frame = ttk.Frame(self.panel_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Connection status
        status_label_frame = ttk.Frame(status_frame)
        status_label_frame.pack(fill=tk.X, pady=(0, 3))
        
        ttk.Label(
            status_label_frame,
            text="Connection:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.status_label = tk.Label(
            status_label_frame,
            text="⚫ Not Connected",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Last command
        last_cmd_frame = ttk.Frame(status_frame)
        last_cmd_frame.pack(fill=tk.X)
        
        ttk.Label(
            last_cmd_frame,
            text="Last Command:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.last_command_label = tk.Label(
            last_cmd_frame,
            text="None",
            font=("Consolas", 9),
            foreground=DarkTheme.FG_SECONDARY,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.last_command_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _create_emotions_section(self):
        """Create emotions control section"""
        emotions_frame = ttk.LabelFrame(
            self.panel_frame,
            text="😊 Emotions",
            style="Dark.TLabelframe"
        )
        emotions_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Emotions grid
        emotions = ['happy', 'angry', 'sad', 'relaxed', 'surprised']
        
        button_frame = ttk.Frame(emotions_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        for i, emotion in enumerate(emotions):
            btn = ttk.Button(
                button_frame,
                text=emotion.capitalize(),
                command=lambda e=emotion: self._send_emotion(e),
                width=12
            )
            btn.grid(row=i//3, column=i%3, padx=2, pady=2, sticky=tk.EW)
        
        # Configure grid columns to expand evenly
        for j in range(3):
            button_frame.columnconfigure(j, weight=1)
    
    def _create_animations_section(self):
        """Create animations control section"""
        animations_frame = ttk.LabelFrame(
            self.panel_frame,
            text="🎬 Animations",
            style="Dark.TLabelframe"
        )
        animations_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Animations grid
        animations = [
            'nod', 'laugh', 'shrug', 'upset', 'wave', 'cat',
            'confused', 'shy', 'swing', 'stretch', 'yay', 'taunt',
            'bow', 'scare', 'refuse', 'snap'
        ]
        
        button_frame = ttk.Frame(animations_frame)
        button_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        for i, animation in enumerate(animations):
            btn = ttk.Button(
                button_frame,
                text=animation.capitalize(),
                command=lambda a=animation: self._send_animation(a),
                width=10
            )
            btn.grid(row=i//4, column=i%4, padx=2, pady=2, sticky=tk.EW)
        
        # Configure grid columns to expand evenly
        for j in range(4):
            button_frame.columnconfigure(j, weight=1)
    
    def _connect(self):
        """Connect to Warudo WebSocket"""
        ws_url = self.ws_url_var.get().strip()
        
        if not ws_url:
            self._show_error("Please enter a WebSocket URL")
            return
        
        # Get tool instance
        self.warudo_tool = self._get_warudo_tool()
        
        if not self.warudo_tool:
            self._show_error("Warudo tool not initialized")
            return
        
        # Update URL in tool's manager if possible
        if hasattr(self.warudo_tool, 'manager') and self.warudo_tool.manager:
            self.warudo_tool.manager.controller.websocket_url = ws_url
        
        # Attempt connection
        if self.ai_core.main_loop:
            import asyncio
            
            async def connect_async():
                # Initialize tool if needed
                if not hasattr(self.warudo_tool, 'manager') or not self.warudo_tool.manager:
                    await self.warudo_tool.initialize()
                
                # Check connection
                if self.warudo_tool.is_available():
                    self._update_status_connected()
                    self.logger.system("[Warudo] Connected successfully")
                else:
                    self._show_error("Failed to connect - check Warudo is running")
            
            asyncio.run_coroutine_threadsafe(connect_async(), self.ai_core.main_loop)
        
        self.logger.system(f"[Warudo] Connecting to {ws_url}...")
    
    def _disconnect(self):
        """Disconnect from Warudo WebSocket"""
        self.warudo_tool = self._get_warudo_tool()
        
        if not self.warudo_tool:
            return
        
        if self.ai_core.main_loop:
            import asyncio
            
            async def disconnect_async():
                await self.warudo_tool.cleanup()
                self._update_status_disconnected()
            
            asyncio.run_coroutine_threadsafe(disconnect_async(), self.ai_core.main_loop)
        
        self.logger.system("[Warudo] Disconnecting...")
    
    def _test_connection(self):
        """Test connection with sample commands"""
        self.warudo_tool = self._get_warudo_tool()
        
        if not self.warudo_tool or not self.warudo_tool.is_available():
            self._show_error("Not connected - connect first")
            return
        
        if self.ai_core.main_loop:
            import asyncio
            import time
            
            async def test_async():
                self.logger.system("[Warudo] Running test sequence...")
                
                # Test emotion
                await self.warudo_tool.execute('emotion', ['happy'])
                await asyncio.sleep(1)
                
                # Test animation
                await self.warudo_tool.execute('animation', ['wave'])
                await asyncio.sleep(1)
                
                # Test another animation
                await self.warudo_tool.execute('animation', ['nod'])
                
                self.logger.system("[Warudo] Test sequence complete")
            
            asyncio.run_coroutine_threadsafe(test_async(), self.ai_core.main_loop)
    
    def _send_emotion(self, emotion: str):
        """Send emotion command"""
        self.warudo_tool = self._get_warudo_tool()
        
        if not self.warudo_tool or not self.warudo_tool.is_available():
            self._show_error("Not connected")
            return
        
        if self.ai_core.main_loop:
            import asyncio
            
            async def send_async():
                result = await self.warudo_tool.execute('emotion', [emotion])
                if result.get('success'):
                    self.last_command_label.config(text=f"emotion: {emotion}")
                    self.logger.system(f"[Warudo] Emotion: {emotion}")
                else:
                    error = result.get('content', 'Unknown error')
                    self._show_error(f"Failed: {error}")
            
            asyncio.run_coroutine_threadsafe(send_async(), self.ai_core.main_loop)
    
    def _send_animation(self, animation: str):
        """Send animation command"""
        self.warudo_tool = self._get_warudo_tool()
        
        if not self.warudo_tool or not self.warudo_tool.is_available():
            self._show_error("Not connected")
            return
        
        if self.ai_core.main_loop:
            import asyncio
            
            async def send_async():
                result = await self.warudo_tool.execute('animation', [animation])
                if result.get('success'):
                    self.last_command_label.config(text=f"animation: {animation}")
                    self.logger.system(f"[Warudo] Animation: {animation}")
                else:
                    error = result.get('content', 'Unknown error')
                    self._show_error(f"Failed: {error}")
            
            asyncio.run_coroutine_threadsafe(send_async(), self.ai_core.main_loop)
    
    def _update_status(self):
        """Update status display based on tool state"""
        self.warudo_tool = self._get_warudo_tool()
        
        if not self.warudo_tool:
            self._update_status_not_available()
            return
        
        if self.warudo_tool.is_available():
            self._update_status_connected()
        else:
            self._update_status_disconnected()
    
    def _update_status_not_available(self):
        """Update UI for tool not available"""
        self.status_label.config(
            text="⚫ Tool Not Available",
            foreground=DarkTheme.FG_MUTED
        )
        self.connect_button.config(state=tk.DISABLED)
        self.disconnect_button.config(state=tk.DISABLED)
    
    def _update_status_connected(self):
        """Update UI for connected state"""
        self.status_label.config(
            text="🟢 Connected",
            foreground=DarkTheme.ACCENT_GREEN
        )
        self.connect_button.config(state=tk.DISABLED)
        self.disconnect_button.config(state=tk.NORMAL)
    
    def _update_status_disconnected(self):
        """Update UI for disconnected state"""
        self.status_label.config(
            text="⚫ Not Connected",
            foreground=DarkTheme.FG_MUTED
        )
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
    
    def _schedule_status_update(self):
        """Schedule periodic status updates"""
        if self.panel_frame and self.panel_frame.winfo_exists():
            self._update_status()
            # Schedule next update in 2 seconds
            self.update_job = self.panel_frame.after(2000, self._schedule_status_update)
    
    def _get_warudo_tool(self):
        """Get Warudo tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'warudo' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('warudo')
    
    def _show_error(self, message: str):
        """Show error message"""
        self.status_label.config(
            text=f"❌ {message}",
            foreground=DarkTheme.ACCENT_RED
        )
        self.logger.error(f"[Warudo] {message}")
    
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
        
        self.logger.system("[Warudo] Component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        WarudoComponent instance
    """
    return WarudoComponent(parent_gui, ai_core, logger)
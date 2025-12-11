# Filename: BASE/tools/installed/unity/component.py
"""
Unity Animation Tool - GUI Component
Dynamic GUI panel for Unity VRM character animation control
"""
import tkinter as tk
from tkinter import ttk
from BASE.interface.gui_themes import DarkTheme
from datetime import datetime


class UnityAnimationComponent:
    """
    GUI component for Unity Animation tool
    Provides interface for controlling VRM character emotions and animations
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        """
        Initialize Unity animation component
        
        Args:
            parent_gui: Main GUI instance
            ai_core: AI Core instance
            logger: Logger instance
        """
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        
        # Tool instance
        self.unity_tool = None
        
        # GUI elements
        self.panel_frame = None
        self.status_label = None
        self.avatar_label = None
        self.emotion_buttons = []
        self.animation_buttons = []
        self.intensity_var = None
        self.log_text = None
        
        # State
        self.connected = False
        self.update_job = None
        self.last_command_time = 0
        
        # Available emotions and animations (will be updated from Unity)
        self.emotions = ['happy', 'sad', 'angry', 'surprised', 'neutral', 'relaxed']
        self.animations = ['wave', 'nod', 'bow', 'dance', 'jump', 'sit']
    
    def create_panel(self, parent_frame):
        """
        Create the Unity animation control panel
        
        Args:
            parent_frame: Parent frame to add panel to
        """
        # Main panel frame
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="🎭 Unity VRM Animation",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Create sections
        self._create_status_section()
        self._create_intensity_section()
        self._create_emotions_section()
        self._create_animations_section()
        self._create_control_section()
        self._create_log_section()
        
        # Start status updates
        self._schedule_status_update()
        
        return self.panel_frame
    
    def _create_status_section(self):
        """Create status display section"""
        status_frame = ttk.Frame(self.panel_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Connection status
        status_left = ttk.Frame(status_frame)
        status_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.status_label = tk.Label(
            status_left,
            text="⚫ Not Connected",
            font=("Segoe UI", 9, "bold"),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Avatar name
        self.avatar_label = tk.Label(
            status_left,
            text="Avatar: --",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_SECONDARY,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.avatar_label.pack(side=tk.LEFT)
        
        # Refresh button
        status_right = ttk.Frame(status_frame)
        status_right.pack(side=tk.RIGHT)
        
        refresh_btn = ttk.Button(
            status_right,
            text="🔄 Refresh",
            command=self._refresh_status,
            width=12
        )
        refresh_btn.pack(side=tk.LEFT, padx=2)
        
        reconnect_btn = ttk.Button(
            status_right,
            text="🔌 Connect",
            command=self._connect_unity,
            width=12
        )
        reconnect_btn.pack(side=tk.LEFT, padx=2)
    
    def _create_intensity_section(self):
        """Create intensity control section"""
        intensity_frame = ttk.Frame(self.panel_frame)
        intensity_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(
            intensity_frame,
            text="Intensity:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.intensity_var = tk.DoubleVar(value=0.8)
        
        intensity_scale = ttk.Scale(
            intensity_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.intensity_var,
            length=200
        )
        intensity_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        intensity_label = tk.Label(
            intensity_frame,
            textvariable=self.intensity_var,
            font=("Consolas", 9),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER,
            width=4
        )
        intensity_label.pack(side=tk.LEFT)
        
        # Update label format
        def update_intensity_label(*args):
            intensity_label.config(text=f"{self.intensity_var.get():.2f}")
        
        self.intensity_var.trace('w', update_intensity_label)
        update_intensity_label()
    
    def _create_emotions_section(self):
        """Create emotions control section"""
        emotions_frame = ttk.LabelFrame(
            self.panel_frame,
            text="😊 Emotions",
            style="Dark.TLabelframe"
        )
        emotions_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Info label
        info_label = tk.Label(
            emotions_frame,
            text="Express character emotions and feelings",
            font=("Segoe UI", 8, "italic"),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER
        )
        info_label.pack(fill=tk.X, padx=5, pady=(5, 3))
        
        # Emotion buttons container
        buttons_container = ttk.Frame(emotions_frame)
        buttons_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Create emotion buttons
        self.emotion_buttons = []
        
        # Emotion icons mapping
        emotion_icons = {
            'happy': '😊',
            'sad': '😢',
            'angry': '😠',
            'surprised': '😮',
            'neutral': '😐',
            'relaxed': '😌',
            'excited': '🤩',
            'confused': '😕'
        }
        
        row_frame = None
        for i, emotion in enumerate(self.emotions):
            if i % 4 == 0:  # 4 buttons per row
                row_frame = ttk.Frame(buttons_container)
                row_frame.pack(fill=tk.X, pady=2)
            
            icon = emotion_icons.get(emotion, '🎭')
            text = f"{icon} {emotion.title()}"
            
            btn = ttk.Button(
                row_frame,
                text=text,
                command=lambda e=emotion: self._execute_emotion(e),
                width=15
            )
            btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
            self.emotion_buttons.append(btn)
    
    def _create_animations_section(self):
        """Create animations control section"""
        animations_frame = ttk.LabelFrame(
            self.panel_frame,
            text="🎬 Animations",
            style="Dark.TLabelframe"
        )
        animations_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Info label
        info_label = tk.Label(
            animations_frame,
            text="Play character animations and actions",
            font=("Segoe UI", 8, "italic"),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER
        )
        info_label.pack(fill=tk.X, padx=5, pady=(5, 3))
        
        # Animation buttons container
        buttons_container = ttk.Frame(animations_frame)
        buttons_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Create animation buttons
        self.animation_buttons = []
        
        # Animation icons mapping
        animation_icons = {
            'wave': '👋',
            'nod': '🙂',
            'shake_head': '🙃',
            'bow': '🙇',
            'dance': '💃',
            'jump': '🦘',
            'sit': '🪑',
            'stand': '🧍',
            'idle': '🧘',
            'laugh': '😂',
            'shrug': '🤷',
            'upset': '😤',
            'cat': '🐱',
            'confused': '😕',
            'shy': '😳',
            'swing': '⛳',
            'stretch': '🤸',
            'yay': '🎉',
            'taunt': '😜',
            'scare': '😱',
            'refuse': '🙅',
            'snap': '👌'
        }
        
        row_frame = None
        for i, animation in enumerate(self.animations):
            if i % 4 == 0:  # 4 buttons per row
                row_frame = ttk.Frame(buttons_container)
                row_frame.pack(fill=tk.X, pady=2)
            
            icon = animation_icons.get(animation, '🎬')
            text = f"{icon} {animation.replace('_', ' ').title()}"
            
            btn = ttk.Button(
                row_frame,
                text=text,
                command=lambda a=animation: self._execute_animation(a),
                width=15
            )
            btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
            self.animation_buttons.append(btn)
    
    def _create_control_section(self):
        """Create manual control section"""
        control_frame = ttk.LabelFrame(
            self.panel_frame,
            text="⚙️ Manual Control",
            style="Dark.TLabelframe"
        )
        control_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Command type
        type_frame = ttk.Frame(control_frame)
        type_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(
            type_frame,
            text="Type:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.command_type_var = tk.StringVar(value='emotion')
        
        type_radio_frame = ttk.Frame(type_frame)
        type_radio_frame.pack(side=tk.LEFT)
        
        ttk.Radiobutton(
            type_radio_frame,
            text="Emotion",
            variable=self.command_type_var,
            value='emotion'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            type_radio_frame,
            text="Animation",
            variable=self.command_type_var,
            value='animation'
        ).pack(side=tk.LEFT, padx=5)
        
        # Custom value entry
        value_frame = ttk.Frame(control_frame)
        value_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(
            value_frame,
            text="Value:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.custom_value_var = tk.StringVar()
        
        value_entry = tk.Entry(
            value_frame,
            textvariable=self.custom_value_var,
            font=("Consolas", 9),
            bg=DarkTheme.BG_DARK,
            fg=DarkTheme.FG_PRIMARY,
            insertbackground=DarkTheme.FG_PRIMARY,
            relief="solid",
            borderwidth=1
        )
        value_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        value_entry.bind('<Return>', lambda e: self._execute_custom())
        
        # Execute button
        exec_btn = ttk.Button(
            value_frame,
            text="▶ Send",
            command=self._execute_custom,
            width=12
        )
        exec_btn.pack(side=tk.LEFT)
    
    def _create_log_section(self):
        """Create activity log section"""
        log_frame = ttk.LabelFrame(
            self.panel_frame,
            text="📋 Activity Log",
            style="Dark.TLabelframe"
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(log_frame, orient='vertical')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Log text
        self.log_text = tk.Text(
            log_frame,
            height=6,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 8),
            bg=DarkTheme.BG_DARK,
            fg=DarkTheme.FG_SECONDARY,
            insertbackground=DarkTheme.FG_PRIMARY,
            borderwidth=0,
            yscrollcommand=scrollbar.set
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        scrollbar.config(command=self.log_text.yview)
        
        # Configure tags
        self.log_text.tag_configure('error', foreground=DarkTheme.ACCENT_RED)
        self.log_text.tag_configure('success', foreground=DarkTheme.ACCENT_GREEN)
        self.log_text.tag_configure('cmd', foreground=DarkTheme.ACCENT_PURPLE)
        self.log_text.tag_configure('info', foreground=DarkTheme.FG_SECONDARY)
    
    def _execute_emotion(self, emotion: str):
        """Execute emotion command"""
        intensity = self.intensity_var.get()
        self._execute_command('emotion', [emotion, intensity])
    
    def _execute_animation(self, animation: str):
        """Execute animation command"""
        intensity = self.intensity_var.get()
        self._execute_command('animation', [animation, intensity])
    
    def _execute_custom(self):
        """Execute custom command"""
        command_type = self.command_type_var.get()
        value = self.custom_value_var.get().strip()
        
        if not value:
            self._add_log("No value entered", 'error')
            return
        
        intensity = self.intensity_var.get()
        self._execute_command(command_type, [value, intensity])
        
        # Clear entry
        self.custom_value_var.set("")
    
    def _execute_command(self, command: str, args: list):
        """Execute Unity command"""
        self.unity_tool = self._get_unity_tool()
        
        if not self.unity_tool:
            self._add_log("Unity tool not available", 'error')
            return
        
        if not self.unity_tool.is_available():
            self._add_log("Unity not connected - attempting to connect...", 'info')
            self._connect_unity()
            return
        
        # Format args display
        if len(args) > 1:
            args_display = f"{args[0]} (intensity: {args[1]:.2f})"
        else:
            args_display = str(args[0])
        
        self._add_log(f"Sending: {command} {args_display}", 'cmd')
        
        # Execute via AI Core
        if self.ai_core.main_loop:
            import asyncio
            
            async def execute_async():
                result = await self.unity_tool.execute(command, args)
                
                if result.get('success'):
                    message = result.get('content', 'Success')
                    self._add_log(message, 'success')
                else:
                    error = result.get('content', 'Command failed')
                    self._add_log(error, 'error')
                    
                    # Show guidance if available
                    guidance = result.get('guidance')
                    if guidance:
                        self._add_log(f"  → {guidance}", 'info')
            
            asyncio.run_coroutine_threadsafe(execute_async(), self.ai_core.main_loop)
    
    def _connect_unity(self):
        """Attempt to connect to Unity"""
        self.unity_tool = self._get_unity_tool()
        
        if not self.unity_tool:
            self._add_log("Unity tool not initialized", 'error')
            return
        
        self._add_log("Connecting to Unity...", 'info')
        
        if self.ai_core.main_loop:
            import asyncio
            
            async def connect_async():
                result = await self.unity_tool.execute('connect', [])
                
                if result.get('success'):
                    self._add_log("Connected to Unity!", 'success')
                    self._update_status()
                else:
                    error = result.get('content', 'Connection failed')
                    self._add_log(error, 'error')
            
            asyncio.run_coroutine_threadsafe(connect_async(), self.ai_core.main_loop)
    
    def _refresh_status(self):
        """Force status refresh"""
        self._add_log("Refreshing status...", 'info')
        self._update_status()
    
    def _update_status(self):
        """Update status display"""
        self.unity_tool = self._get_unity_tool()
        
        if not self.unity_tool:
            self._update_status_disconnected()
            return
        
        # Get status from tool
        status = self.unity_tool.get_status()
        
        if status.get('connected'):
            self._update_status_connected(status)
            
            # Update available emotions/animations if they've changed
            if status.get('emotions') and status['emotions'] != self.emotions:
                self.emotions = status['emotions']
                self._rebuild_emotion_buttons()
            
            if status.get('animations') and status['animations'] != self.animations:
                self.animations = status['animations']
                self._rebuild_animation_buttons()
        else:
            self._update_status_disconnected()
    
    def _update_status_connected(self, status: dict):
        """Update UI for connected state"""
        self.connected = True
        
        self.status_label.config(
            text="🟢 Connected",
            foreground=DarkTheme.ACCENT_GREEN
        )
        
        avatar_name = status.get('avatar_name', 'Unknown')
        vrm_status = "VRM OK" if status.get('vrm_connected') else "No VRM"
        
        self.avatar_label.config(
            text=f"Avatar: {avatar_name} • {vrm_status}",
            foreground=DarkTheme.FG_PRIMARY
        )
    
    def _update_status_disconnected(self):
        """Update UI for disconnected state"""
        self.connected = False
        
        self.status_label.config(
            text="⚫ Not Connected",
            foreground=DarkTheme.FG_MUTED
        )
        
        self.avatar_label.config(
            text="Avatar: --",
            foreground=DarkTheme.FG_MUTED
        )
    
    def _rebuild_emotion_buttons(self):
        """Rebuild emotion buttons with updated list"""
        # Clear existing buttons
        for btn in self.emotion_buttons:
            btn.destroy()
        self.emotion_buttons.clear()
        
        # Note: Full rebuild would require recreating the entire section
        # For now, just log the change
        self._add_log(f"Emotions updated: {len(self.emotions)} available", 'info')
    
    def _rebuild_animation_buttons(self):
        """Rebuild animation buttons with updated list"""
        # Clear existing buttons
        for btn in self.animation_buttons:
            btn.destroy()
        self.animation_buttons.clear()
        
        # Note: Full rebuild would require recreating the entire section
        # For now, just log the change
        self._add_log(f"Animations updated: {len(self.animations)} available", 'info')
    
    def _add_log(self, message: str, tag='info'):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)
        
        # Limit log size
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > 100:
            self.log_text.delete('1.0', '51.0')
        
        self.log_text.config(state=tk.DISABLED)
    
    def _schedule_status_update(self):
        """Schedule periodic status updates"""
        if self.panel_frame and self.panel_frame.winfo_exists():
            self._update_status()
            # Update every 5 seconds
            self.update_job = self.panel_frame.after(5000, self._schedule_status_update)
    
    def _get_unity_tool(self):
        """Get Unity tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'unity' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('unity')
    
    def cleanup(self):
        """Cleanup component resources"""
        # Cancel scheduled updates
        if self.update_job:
            try:
                self.panel_frame.after_cancel(self.update_job)
            except:
                pass
        
        if self.logger:
            self.logger.system("[Unity] Component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        UnityAnimationComponent instance
    """
    return UnityAnimationComponent(parent_gui, ai_core, logger)
# Filename: BASE/tools/installed/game_vision/component.py
"""
Game Vision Tool - GUI Component
Dynamic GUI panel for game screen monitoring and analysis control
Follows modular tool panel system architecture
"""
import tkinter as tk
from tkinter import ttk
from BASE.interface.gui_themes import DarkTheme


class GameVisionComponent:
    """
    GUI component for Game Vision Tool
    Provides interface for controlling continuous screen monitoring and window capture
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        """
        Initialize Game Vision component
        
        Args:
            parent_gui: Main GUI instance
            ai_core: AI Core instance
            logger: Logger instance
        """
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        
        # Tool instance (will be set when available)
        self.game_vision_tool = None
        
        # GUI elements
        self.panel_frame = None
        self.status_label = None
        self.capture_count_label = None
        self.last_capture_label = None
        self.capture_mode_label = None
        self.window_status_label = None
        self.model_label = None
        self.interval_var = None
        self.capture_now_button = None
        self.list_windows_button = None
        self.window_listbox = None
        self.set_window_button = None
        self.reset_monitor_button = None
        
        # Update timer
        self.update_job = None
        
        # Window list cache
        self.available_windows = []
    
    def create_panel(self, parent_frame):
        """
        Create the Game Vision control panel
        
        Args:
            parent_frame: Parent frame to add panel to
        """
        # Main panel frame
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="🎮 Game Vision Monitor",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Status section
        self._create_status_section()
        
        # Control section
        self._create_control_section()
        
        # Capture settings section
        self._create_capture_settings_section()
        
        # Window selection section
        self._create_window_selection_section()
        
        # Start status updates
        self._schedule_status_update()
        
        return self.panel_frame
    
    def _create_status_section(self):
        """Create status display section"""
        status_frame = ttk.LabelFrame(
            self.panel_frame,
            text="📊 Status",
            style="Dark.TLabelframe"
        )
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Tool status
        status_row1 = ttk.Frame(status_frame)
        status_row1.pack(fill=tk.X, padx=5, pady=(5, 2))
        
        ttk.Label(
            status_row1,
            text="Tool:",
            style="TLabel",
            width=12
        ).pack(side=tk.LEFT)
        
        self.status_label = tk.Label(
            status_row1,
            text="⚫ Not Available",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Capture count
        status_row2 = ttk.Frame(status_frame)
        status_row2.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(
            status_row2,
            text="Captures:",
            style="TLabel",
            width=12
        ).pack(side=tk.LEFT)
        
        self.capture_count_label = tk.Label(
            status_row2,
            text="0",
            font=("Consolas", 9),
            foreground=DarkTheme.FG_SECONDARY,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.capture_count_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Last capture time
        status_row3 = ttk.Frame(status_frame)
        status_row3.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(
            status_row3,
            text="Last Capture:",
            style="TLabel",
            width=12
        ).pack(side=tk.LEFT)
        
        self.last_capture_label = tk.Label(
            status_row3,
            text="Never",
            font=("Consolas", 9),
            foreground=DarkTheme.FG_SECONDARY,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.last_capture_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Capture mode
        status_row4 = ttk.Frame(status_frame)
        status_row4.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(
            status_row4,
            text="Mode:",
            style="TLabel",
            width=12
        ).pack(side=tk.LEFT)
        
        self.capture_mode_label = tk.Label(
            status_row4,
            text="Monitor",
            font=("Consolas", 9),
            foreground=DarkTheme.ACCENT_BLUE,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.capture_mode_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Window status (only shown in window mode)
        status_row5 = ttk.Frame(status_frame)
        status_row5.pack(fill=tk.X, padx=5, pady=(2, 5))
        
        ttk.Label(
            status_row5,
            text="Window:",
            style="TLabel",
            width=12
        ).pack(side=tk.LEFT)
        
        self.window_status_label = tk.Label(
            status_row5,
            text="N/A",
            font=("Consolas", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.window_status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _create_control_section(self):
        """Create control buttons section"""
        control_frame = ttk.LabelFrame(
            self.panel_frame,
            text="🎛️ Controls",
            style="Dark.TLabelframe"
        )
        control_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        button_row = ttk.Frame(control_frame)
        button_row.pack(fill=tk.X, padx=5, pady=5)
        
        # Capture now button
        self.capture_now_button = ttk.Button(
            button_row,
            text="📸 Capture Now",
            command=self._capture_now,
            width=18
        )
        self.capture_now_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # List windows button
        self.list_windows_button = ttk.Button(
            button_row,
            text="🪟 List Windows",
            command=self._list_windows,
            width=18
        )
        self.list_windows_button.pack(side=tk.LEFT)
    
    def _create_capture_settings_section(self):
        """Create capture settings section"""
        settings_frame = ttk.LabelFrame(
            self.panel_frame,
            text="⚙️ Settings",
            style="Dark.TLabelframe"
        )
        settings_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Capture interval
        interval_row = ttk.Frame(settings_frame)
        interval_row.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(
            interval_row,
            text="Capture Interval:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.interval_var = tk.StringVar(value="10.0")
        interval_entry = ttk.Entry(
            interval_row,
            textvariable=self.interval_var,
            width=8,
            font=("Consolas", 9)
        )
        interval_entry.pack(side=tk.LEFT)
        
        ttk.Label(
            interval_row,
            text="seconds",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Info about interval
        ttk.Label(
            settings_frame,
            text="⚠️ Interval changes require tool restart",
            style="TLabel",
            foreground=DarkTheme.FG_MUTED,
            font=("Segoe UI", 8)
        ).pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Vision model info
        model_row = ttk.Frame(settings_frame)
        model_row.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(
            model_row,
            text="Vision Model:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.model_label = tk.Label(
            model_row,
            text="llava:latest",
            font=("Consolas", 9),
            foreground=DarkTheme.FG_SECONDARY,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.model_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _create_window_selection_section(self):
        """Create window selection section"""
        window_frame = ttk.LabelFrame(
            self.panel_frame,
            text="🪟 Window Capture",
            style="Dark.TLabelframe"
        )
        window_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Instructions
        ttk.Label(
            window_frame,
            text="Select a window to capture instead of full monitor:",
            style="TLabel",
            font=("Segoe UI", 9)
        ).pack(fill=tk.X, padx=5, pady=(5, 2))
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(window_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.window_listbox = tk.Listbox(
            list_frame,
            height=8,
            font=("Consolas", 9),
            background=DarkTheme.BG_DARK,
            foreground=DarkTheme.FG_PRIMARY,
            selectbackground=DarkTheme.ACCENT_PURPLE,
            selectforeground=DarkTheme.FG_PRIMARY,
            yscrollcommand=scrollbar.set,
            activestyle='none'
        )
        self.window_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.window_listbox.yview)
        
        # Double-click to select
        self.window_listbox.bind('<Double-Button-1>', lambda e: self._set_selected_window())
        
        # Buttons
        button_row = ttk.Frame(window_frame)
        button_row.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.set_window_button = ttk.Button(
            button_row,
            text="✅ Set Window",
            command=self._set_selected_window,
            width=18
        )
        self.set_window_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.reset_monitor_button = ttk.Button(
            button_row,
            text="🖥️ Reset to Monitor",
            command=self._reset_to_monitor,
            width=18
        )
        self.reset_monitor_button.pack(side=tk.LEFT)
    
    def _capture_now(self):
        """Force immediate screenshot capture"""
        self.game_vision_tool = self._get_game_vision_tool()
        
        if not self.game_vision_tool or not self.game_vision_tool.is_available():
            self._show_error("Tool not available")
            return
        
        if self.ai_core.main_loop:
            import asyncio
            
            async def capture_async():
                result = await self.game_vision_tool.execute('capture_now', [])
                
                if result.get('success'):
                    self.logger.system("[Game Vision] Capture complete")
                    self._update_status()
                else:
                    error = result.get('content', 'Unknown error')
                    self._show_error(f"Capture failed: {error}")
            
            asyncio.run_coroutine_threadsafe(capture_async(), self.ai_core.main_loop)
    
    def _list_windows(self):
        """List all available windows"""
        self.game_vision_tool = self._get_game_vision_tool()
        
        if not self.game_vision_tool or not self.game_vision_tool.is_available():
            self._show_error("Tool not available")
            return
        
        if self.ai_core.main_loop:
            import asyncio
            
            async def list_async():
                result = await self.game_vision_tool.execute('list_windows', [])
                
                if result.get('success'):
                    windows = result.get('metadata', {}).get('windows', [])
                    self.available_windows = windows
                    
                    # Update listbox
                    self.window_listbox.delete(0, tk.END)
                    
                    for window in windows:
                        title = window.get('title', 'Unknown')
                        size = window.get('size', '?x?')
                        minimized = window.get('minimized', False)
                        
                        display = f"{title} ({size})"
                        if minimized:
                            display += " [minimized]"
                        
                        self.window_listbox.insert(tk.END, display)
                    
                    self.logger.system(f"[Game Vision] Found {len(windows)} windows")
                else:
                    error = result.get('content', 'Unknown error')
                    self._show_error(f"List failed: {error}")
            
            asyncio.run_coroutine_threadsafe(list_async(), self.ai_core.main_loop)
    
    def _set_selected_window(self):
        """Set selected window as capture target"""
        selection = self.window_listbox.curselection()
        
        if not selection:
            self._show_error("No window selected")
            return
        
        index = selection[0]
        
        if index >= len(self.available_windows):
            self._show_error("Invalid selection")
            return
        
        window = self.available_windows[index]
        window_title = window.get('title')
        
        if not window_title:
            self._show_error("Invalid window title")
            return
        
        self.game_vision_tool = self._get_game_vision_tool()
        
        if not self.game_vision_tool or not self.game_vision_tool.is_available():
            self._show_error("Tool not available")
            return
        
        if self.ai_core.main_loop:
            import asyncio
            
            async def set_window_async():
                result = await self.game_vision_tool.execute('set_window', [window_title])
                
                if result.get('success'):
                    self.logger.system(f"[Game Vision] Window set: {window_title}")
                    self._update_status()
                else:
                    error = result.get('content', 'Unknown error')
                    self._show_error(f"Set window failed: {error}")
            
            asyncio.run_coroutine_threadsafe(set_window_async(), self.ai_core.main_loop)
    
    def _reset_to_monitor(self):
        """Reset to full monitor capture mode"""
        self.game_vision_tool = self._get_game_vision_tool()
        
        if not self.game_vision_tool or not self.game_vision_tool.is_available():
            self._show_error("Tool not available")
            return
        
        if self.ai_core.main_loop:
            import asyncio
            
            async def reset_async():
                result = await self.game_vision_tool.execute('set_window', [None])
                
                if result.get('success'):
                    self.logger.system("[Game Vision] Reset to monitor mode")
                    self._update_status()
                else:
                    error = result.get('content', 'Unknown error')
                    self._show_error(f"Reset failed: {error}")
            
            asyncio.run_coroutine_threadsafe(reset_async(), self.ai_core.main_loop)
    
    def _update_status(self):
        """Update status display based on tool state"""
        self.game_vision_tool = self._get_game_vision_tool()
        
        if not self.game_vision_tool:
            self._update_status_not_available()
            return
        
        if not self.game_vision_tool.is_available():
            self._update_status_unavailable()
            return
        
        # Get tool status
        status = self.game_vision_tool.get_status()
        
        # Update status labels
        self.status_label.config(
            text="🟢 Active",
            foreground=DarkTheme.ACCENT_GREEN
        )
        
        # Capture count
        count = status.get('screenshot_count', 0)
        self.capture_count_label.config(text=str(count))
        
        # Last capture time
        last_capture = status.get('last_capture', 0)
        if last_capture > 0:
            import time
            time_ago = time.time() - last_capture
            if time_ago < 60:
                time_str = f"{time_ago:.1f}s ago"
            elif time_ago < 3600:
                time_str = f"{time_ago/60:.1f}m ago"
            else:
                time_str = f"{time_ago/3600:.1f}h ago"
            self.last_capture_label.config(text=time_str)
        else:
            self.last_capture_label.config(text="Never")
        
        # Capture mode
        capture_mode = status.get('capture_mode', 'monitor')
        if capture_mode == 'window':
            self.capture_mode_label.config(
                text="Window",
                foreground=DarkTheme.ACCENT_PURPLE
            )
            
            # Window status
            window_found = status.get('window_found', False)
            if window_found:
                window_info = status.get('window_info', {})
                title = window_info.get('title', 'Unknown')
                minimized = window_info.get('minimized', False)
                
                status_text = title
                if minimized:
                    status_text += " [minimized]"
                
                self.window_status_label.config(
                    text=status_text,
                    foreground=DarkTheme.ACCENT_GREEN if not minimized else DarkTheme.ACCENT_ORANGE
                )
            else:
                target = status.get('target_window', 'Unknown')
                self.window_status_label.config(
                    text=f"{target} [not found]",
                    foreground=DarkTheme.ACCENT_RED
                )
        else:
            self.capture_mode_label.config(
                text="Monitor",
                foreground=DarkTheme.ACCENT_BLUE
            )
            self.window_status_label.config(
                text="N/A",
                foreground=DarkTheme.FG_MUTED
            )
        
        # Vision model
        model = status.get('vision_model', 'Unknown')
        self.model_label.config(text=model)
        
        # Enable controls
        self.capture_now_button.config(state=tk.NORMAL)
        self.list_windows_button.config(state=tk.NORMAL)
        self.set_window_button.config(state=tk.NORMAL)
        self.reset_monitor_button.config(state=tk.NORMAL)
    
    def _update_status_not_available(self):
        """Update UI for tool not available"""
        self.status_label.config(
            text="⚫ Not Available",
            foreground=DarkTheme.FG_MUTED
        )
        
        self.capture_count_label.config(text="0")
        self.last_capture_label.config(text="Never")
        self.capture_mode_label.config(text="N/A", foreground=DarkTheme.FG_MUTED)
        self.window_status_label.config(text="N/A", foreground=DarkTheme.FG_MUTED)
        self.model_label.config(text="N/A")
        
        # Disable controls
        self.capture_now_button.config(state=tk.DISABLED)
        self.list_windows_button.config(state=tk.DISABLED)
        self.set_window_button.config(state=tk.DISABLED)
        self.reset_monitor_button.config(state=tk.DISABLED)
    
    def _update_status_unavailable(self):
        """Update UI for tool unavailable (libraries missing)"""
        self.status_label.config(
            text="⚠️ Libraries Missing",
            foreground=DarkTheme.ACCENT_ORANGE
        )
        
        self.capture_count_label.config(text="N/A")
        self.last_capture_label.config(text="N/A")
        self.capture_mode_label.config(text="N/A", foreground=DarkTheme.FG_MUTED)
        self.window_status_label.config(text="N/A", foreground=DarkTheme.FG_MUTED)
        self.model_label.config(text="N/A")
        
        # Disable controls
        self.capture_now_button.config(state=tk.DISABLED)
        self.list_windows_button.config(state=tk.DISABLED)
        self.set_window_button.config(state=tk.DISABLED)
        self.reset_monitor_button.config(state=tk.DISABLED)
    
    def _schedule_status_update(self):
        """Schedule periodic status updates"""
        if self.panel_frame and self.panel_frame.winfo_exists():
            self._update_status()
            # Schedule next update in 2 seconds
            self.update_job = self.panel_frame.after(2000, self._schedule_status_update)
    
    def _get_game_vision_tool(self):
        """Get Game Vision tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'game_vision' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('game_vision')
    
    def _show_error(self, message: str):
        """Show error message"""
        self.status_label.config(
            text=f"❌ {message}",
            foreground=DarkTheme.ACCENT_RED
        )
        self.logger.error(f"[Game Vision] {message}")
    
    def cleanup(self):
        """Cleanup component resources"""
        # Cancel scheduled updates
        if self.update_job:
            try:
                self.panel_frame.after_cancel(self.update_job)
            except:
                pass
        
        self.logger.system("[Game Vision] Component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        GameVisionComponent instance
    """
    return GameVisionComponent(parent_gui, ai_core, logger)
# Filename: BASE/tools/installed/sound/component.py
"""
Sounds Tool - GUI Component
Dynamic GUI panel for sound effects playback
"""
import tkinter as tk
from tkinter import ttk
from BASE.interface.gui_themes import DarkTheme
import asyncio
from typing import Optional, Dict, List


class SoundsComponent:
    """GUI component for Sounds tool - plays sound effects on command"""
    
    def __init__(self, parent_gui, ai_core, logger):
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        self.sounds_tool = None
        self.panel_frame = None
        self.status_label = None
        self.sound_buttons = {}
        self.volume_var = None
        self.volume_label = None
        self.mute_btn = None
        self.scrollable_frame = None
        self.update_job = None
        self._available_sounds = []
        self._is_muted = False
        self._pre_mute_volume = 1.0
    
    def create_panel(self, parent_frame):
        """Create the sounds panel"""
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="Sound Effects Player",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Status section
        self._create_status_section()
        
        # Volume control section
        self._create_volume_section()
        
        # Sound buttons section
        self._create_sounds_section()
        
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
            command=self._refresh_sounds,
            width=3
        )
        refresh_btn.pack(side=tk.RIGHT)
    
    def _create_volume_section(self):
        """Create volume control"""
        volume_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Volume Control",
            style="Dark.TLabelframe"
        )
        volume_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        control_frame = ttk.Frame(volume_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Volume label
        ttk.Label(
            control_frame,
            text="Volume:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Volume slider
        self.volume_var = tk.DoubleVar(value=1.0)
        volume_slider = ttk.Scale(
            control_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.volume_var,
            command=self._on_volume_change
        )
        volume_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Volume percentage label
        self.volume_label = tk.Label(
            control_frame,
            text="100%",
            font=("Consolas", 9),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER,
            width=5
        )
        self.volume_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Mute button
        self.mute_btn = ttk.Button(
            control_frame,
            text="🔊",
            command=self._toggle_mute,
            width=3
        )
        self.mute_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Stop all button
        stop_btn = ttk.Button(
            control_frame,
            text="⏹️ Stop All",
            command=self._stop_all_sounds,
            width=10
        )
        stop_btn.pack(side=tk.LEFT, padx=(5, 0))
    
    def _create_sounds_section(self):
        """Create sound effect buttons"""
        sounds_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Available Sounds",
            style="Dark.TLabelframe"
        )
        sounds_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Scrollable container
        canvas = tk.Canvas(
            sounds_frame,
            bg=DarkTheme.BG_DARK,
            highlightthickness=0,
            height=200
        )
        scrollbar = ttk.Scrollbar(sounds_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mouse wheel
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))
        
        # Load sounds
        self._load_available_sounds()
    
    def _load_available_sounds(self):
        """Load and display available sound effects"""
        # Clear existing buttons
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.sound_buttons.clear()
        
        self.sounds_tool = self._get_sounds_tool()
        
        if not self.sounds_tool:
            self._show_error("Sound tool not initialized")
            self._show_no_sounds("Tool not initialized")
            return
        
        # Get available sounds
        try:
            sounds = self.sounds_tool.get_available_sounds()
            self._available_sounds = sounds
            
            if not sounds:
                self._show_no_sounds("No sound files found in sounds/ directory")
                self._update_status_unavailable("No sounds found")
                return
            
            # Create grid of sound buttons (3 columns)
            sorted_sounds = sorted(sounds.keys())
            
            for idx, sound in enumerate(sorted_sounds):
                row = idx // 3
                col = idx % 3
                
                btn_frame = ttk.Frame(self.scrollable_frame)
                btn_frame.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
                
                # Configure grid weights
                self.scrollable_frame.columnconfigure(col, weight=1)
                
                # Sound button
                sound_btn = ttk.Button(
                    btn_frame,
                    text=f"🔊 {sound}",
                    command=lambda s=sound: self._play_sound(s),
                    width=15
                )
                sound_btn.pack(fill=tk.X)
                
                self.sound_buttons[sound] = sound_btn
            
            # Update status
            self._update_status_available(len(sounds))
            
        except Exception as e:
            self.logger.error(f"[Sounds] Error loading sounds: {e}")
            self._show_error(f"Error loading sounds: {e}")
            self._show_no_sounds(f"Error: {e}")
    
    def _show_no_sounds(self, message: str):
        """Show message when no sounds available"""
        no_sounds_label = tk.Label(
            self.scrollable_frame,
            text=message,
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            pady=20
        )
        no_sounds_label.pack(fill=tk.BOTH, expand=True)
    
    def _play_sound(self, sound_name: str):
        """Play a sound effect"""
        if not self.sounds_tool:
            self._show_error("Sound tool not available")
            return
        
        # Get current volume
        volume = self.volume_var.get() if not self._is_muted else 0.0
        
        # Execute play command
        if self.ai_core.main_loop:
            async def play_async():
                result = await self.sounds_tool.execute('play', [sound_name, volume])
                if result.get('success'):
                    self.logger.success(f"[Sounds] Played: {sound_name}")
                else:
                    error = result.get('content', 'Unknown error')
                    self._show_error(f"Failed to play: {error}")
            
            asyncio.run_coroutine_threadsafe(play_async(), self.ai_core.main_loop)
        
        self.logger.system(f"[Sounds] Playing: {sound_name} (volume: {int(volume * 100)}%)")
    
    def _stop_all_sounds(self):
        """Stop all playing sounds"""
        if not self.sounds_tool:
            return
        
        if self.ai_core.main_loop:
            async def stop_async():
                result = await self.sounds_tool.execute('stop', [])
                if result.get('success'):
                    self.logger.system("[Sounds] Stopped all sounds")
            
            asyncio.run_coroutine_threadsafe(stop_async(), self.ai_core.main_loop)
    
    def _on_volume_change(self, value):
        """Handle volume slider change"""
        volume = float(value)
        percentage = int(volume * 100)
        self.volume_label.config(text=f"{percentage}%")
        
        # Update mute button if volume changed from 0
        if volume > 0 and self._is_muted:
            self._is_muted = False
            self.mute_btn.config(text="🔊")
    
    def _toggle_mute(self):
        """Toggle mute state"""
        if self._is_muted:
            # Unmute - restore previous volume
            self.volume_var.set(self._pre_mute_volume)
            self.mute_btn.config(text="🔊")
            self._is_muted = False
            self.logger.system("[Sounds] Unmuted")
        else:
            # Mute - save current volume and set to 0
            self._pre_mute_volume = self.volume_var.get()
            self.volume_var.set(0.0)
            self.mute_btn.config(text="🔇")
            self._is_muted = True
            self.logger.system("[Sounds] Muted")
    
    def _refresh_sounds(self):
        """Refresh sound list"""
        self.logger.system("[Sounds] Refreshing sound list...")
        self._load_available_sounds()
    
    def _update_status(self):
        """Update status display"""
        self.sounds_tool = self._get_sounds_tool()
        
        if not self.sounds_tool:
            self._update_status_unavailable("Tool not available")
            return
        
        status = self.sounds_tool.get_status()
        
        if status.get('available'):
            sound_count = status.get('sound_count', 0)
            self._update_status_available(sound_count)
        else:
            reasons = []
            if not status.get('pygame_available'):
                reasons.append("pygame not installed")
            if not status.get('initialized'):
                reasons.append("mixer failed")
            if status.get('sound_count', 0) == 0:
                reasons.append("no sounds found")
            
            reason = ", ".join(reasons) if reasons else "unavailable"
            self._update_status_unavailable(reason)
    
    def _update_status_available(self, sound_count: int):
        """Update UI for available state"""
        self.status_label.config(
            text=f"🟢 Ready - {sound_count} sound(s) available",
            foreground=DarkTheme.ACCENT_GREEN
        )
    
    def _update_status_unavailable(self, reason: str):
        """Update UI for unavailable state"""
        self.status_label.config(
            text=f"⚫ Not Available: {reason}",
            foreground=DarkTheme.FG_MUTED
        )
    
    def _schedule_status_update(self):
        """Schedule periodic status updates"""
        if self.panel_frame and self.panel_frame.winfo_exists():
            self._update_status()
            # Schedule next update in 5 seconds
            self.update_job = self.panel_frame.after(5000, self._schedule_status_update)
    
    def _get_sounds_tool(self):
        """Get Sounds tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'sound' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('sound')
    
    def _show_error(self, message: str):
        """Show error message"""
        self.status_label.config(
            text=f"❌ {message}",
            foreground=DarkTheme.ACCENT_RED
        )
        self.logger.error(f"[Sounds] {message}")
    
    def cleanup(self):
        """Cleanup component resources"""
        # Cancel scheduled updates
        if self.update_job:
            try:
                self.panel_frame.after_cancel(self.update_job)
            except:
                pass
        
        self.logger.system("[Sounds] Component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        SoundsComponent instance
    """
    return SoundsComponent(parent_gui, ai_core, logger)
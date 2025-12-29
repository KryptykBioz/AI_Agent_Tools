# Filename: BASE/tools/installed/minecraft_spectator/component.py
"""
Minecraft Spectator Tool v2.0 - GUI Component
Direct connection spectator (no bot server required)
"""
import tkinter as tk
from tkinter import ttk
from BASE.interface.gui_themes import DarkTheme
from datetime import datetime


class MinecraftSpectatorComponent:
    """
    GUI component for Minecraft Spectator v2.0
    Direct connection monitoring interface
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        """Initialize Minecraft Spectator component"""
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        
        # Tool instance
        self.spectator_tool = None
        
        # GUI elements
        self.panel_frame = None
        self.status_label = None
        self.connection_label = None
        self.health_label = None
        self.food_label = None
        self.position_label = None
        self.time_label = None
        self.threats_text = None
        self.blocks_text = None
        self.inventory_text = None
        self.log_text = None
        
        # Configuration widgets
        self.host_var = None
        self.port_var = None
        self.username_var = None
        
        # State
        self.connected = False
        self.update_job = None
    
    def create_panel(self, parent_frame):
        """Create the Minecraft Spectator panel"""
        # Main panel frame
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="👁️ Minecraft Spectator v2.0 (Direct Connection)",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Create sections
        self._create_connection_section()
        self._create_status_section()
        self._create_info_section()
        self._create_log_section()
        
        # Start status updates
        self._schedule_status_update()
        
        return self.panel_frame
    
    def _create_connection_section(self):
        """Create connection configuration section"""
        conn_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Connection Settings",
            style="Dark.TLabelframe"
        )
        conn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Settings grid
        settings_frame = ttk.Frame(conn_frame)
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Host
        ttk.Label(
            settings_frame,
            text="Host:",
            style="TLabel"
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.host_var = tk.StringVar(value="localhost")
        host_entry = ttk.Entry(
            settings_frame,
            textvariable=self.host_var,
            font=("Consolas", 9),
            width=20
        )
        host_entry.grid(row=0, column=1, sticky=tk.EW, padx=(0, 10))
        
        # Port
        ttk.Label(
            settings_frame,
            text="Port:",
            style="TLabel"
        ).grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        
        self.port_var = tk.StringVar(value="25565")
        port_entry = ttk.Entry(
            settings_frame,
            textvariable=self.port_var,
            font=("Consolas", 9),
            width=8
        )
        port_entry.grid(row=0, column=3, sticky=tk.W)
        
        # Username
        ttk.Label(
            settings_frame,
            text="Username:",
            style="TLabel"
        ).grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        
        self.username_var = tk.StringVar(value="SpectatorBot")
        username_entry = ttk.Entry(
            settings_frame,
            textvariable=self.username_var,
            font=("Consolas", 9),
            width=20
        )
        username_entry.grid(row=1, column=1, sticky=tk.EW, pady=(5, 0))
        
        # Connection info label
        self.connection_label = tk.Label(
            settings_frame,
            text="Configure above, then enable tool to connect",
            font=("Segoe UI", 8, "italic"),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.connection_label.grid(
            row=1, column=2, columnspan=2,
            sticky=tk.W, padx=(10, 0), pady=(5, 0)
        )
        
        settings_frame.columnconfigure(1, weight=1)
    
    def _create_status_section(self):
        """Create status display section"""
        status_frame = ttk.Frame(self.panel_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
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
        
        # Mode indicator
        mode_label = tk.Label(
            status_left,
            text="(Direct Connection - No Bot Server)",
            font=("Segoe UI", 8, "italic"),
            foreground=DarkTheme.ACCENT_PURPLE,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        mode_label.pack(side=tk.LEFT)
        
        # Health & Food
        status_right = ttk.Frame(status_frame)
        status_right.pack(side=tk.RIGHT)
        
        self.health_label = tk.Label(
            status_right,
            text="❤ --/20",
            font=("Consolas", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER
        )
        self.health_label.pack(side=tk.LEFT, padx=5)
        
        self.food_label = tk.Label(
            status_right,
            text="🍖 --/20",
            font=("Consolas", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER
        )
        self.food_label.pack(side=tk.LEFT, padx=5)
        
        # Position & Time
        env_frame = ttk.Frame(self.panel_frame)
        env_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.position_label = tk.Label(
            env_frame,
            text="Position: --, --, --",
            font=("Consolas", 8),
            foreground=DarkTheme.ACCENT_PURPLE,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.position_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.time_label = tk.Label(
            env_frame,
            text="Time: --",
            font=("Consolas", 8),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.time_label.pack(side=tk.LEFT)
    
    def _create_info_section(self):
        """Create information display section"""
        info_frame = ttk.Frame(self.panel_frame)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Left column
        left_column = ttk.Frame(info_frame)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))
        
        # Threats
        threats_frame = ttk.LabelFrame(
            left_column,
            text="⚠️ Nearby Threats",
            style="Dark.TLabelframe"
        )
        threats_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.threats_text = tk.Text(
            threats_frame,
            height=6,
            font=("Consolas", 8),
            background=DarkTheme.BG_DARKER,
            foreground=DarkTheme.FG_PRIMARY,
            relief=tk.FLAT,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.threats_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Blocks
        blocks_frame = ttk.LabelFrame(
            left_column,
            text="🧱 Nearby Blocks",
            style="Dark.TLabelframe"
        )
        blocks_frame.pack(fill=tk.BOTH, expand=True)
        
        self.blocks_text = tk.Text(
            blocks_frame,
            height=6,
            font=("Consolas", 8),
            background=DarkTheme.BG_DARKER,
            foreground=DarkTheme.FG_PRIMARY,
            relief=tk.FLAT,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.blocks_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Right column
        right_column = ttk.Frame(info_frame)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(2, 0))
        
        inventory_frame = ttk.LabelFrame(
            right_column,
            text="🎒 Inventory",
            style="Dark.TLabelframe"
        )
        inventory_frame.pack(fill=tk.BOTH, expand=True)
        
        self.inventory_text = tk.Text(
            inventory_frame,
            height=12,
            font=("Consolas", 8),
            background=DarkTheme.BG_DARKER,
            foreground=DarkTheme.FG_PRIMARY,
            relief=tk.FLAT,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.inventory_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
    
    def _create_log_section(self):
        """Create activity log section"""
        log_frame = ttk.LabelFrame(
            self.panel_frame,
            text="📋 Activity Log",
            style="Dark.TLabelframe"
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        self.log_text = tk.Text(
            log_frame,
            height=6,
            font=("Consolas", 8),
            background=DarkTheme.BG_DARKER,
            foreground=DarkTheme.FG_PRIMARY,
            relief=tk.FLAT,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Log tags
        self.log_text.tag_config('info', foreground=DarkTheme.FG_PRIMARY)
        self.log_text.tag_config('alert', foreground=DarkTheme.ACCENT_YELLOW)
        self.log_text.tag_config('critical', foreground=DarkTheme.ACCENT_RED)
        self.log_text.tag_config('success', foreground=DarkTheme.ACCENT_GREEN)
    
    def _update_status(self):
        """Update status display"""
        # Get spectator tool instance
        self.spectator_tool = self._get_spectator_tool()
        
        if not self.spectator_tool:
            self._update_status_disconnected()
            return
        
        # Check if connected
        if not self.spectator_tool._connected:
            self._update_status_disconnected()
            return
        
        # Update connected state
        self._update_status_connected()
        
        # Update displays from game state
        self._update_game_state()
    
    def _update_status_disconnected(self):
        """Update UI for disconnected state"""
        self.connected = False
        
        self.status_label.config(
            text="⚫ Not Connected",
            foreground=DarkTheme.FG_MUTED
        )
        
        self.connection_label.config(
            text="Configure above, then enable tool to connect"
        )
        
        self.health_label.config(text="❤ --/20", foreground=DarkTheme.FG_MUTED)
        self.food_label.config(text="🍖 --/20", foreground=DarkTheme.FG_MUTED)
        self.position_label.config(text="Position: --, --, --")
        self.time_label.config(text="Time: --")
        
        self._clear_text_widget(self.threats_text, "Not connected")
        self._clear_text_widget(self.blocks_text, "Not connected")
        self._clear_text_widget(self.inventory_text, "Not connected")
    
    def _update_status_connected(self):
        """Update UI for connected state"""
        if not self.connected:
            self.connected = True
            self._add_log("Connected to server", 'success')
        
        self.status_label.config(
            text="🟢 Connected & Spectating",
            foreground=DarkTheme.ACCENT_GREEN
        )
        
        host = self.host_var.get()
        port = self.port_var.get()
        self.connection_label.config(
            text=f"Connected to {host}:{port}"
        )
    
    def _update_game_state(self):
        """Update displays from tool's game state"""
        if not self.spectator_tool:
            return
        
        game_state = self.spectator_tool._game_state
        
        # Update player stats
        player = game_state.get('player', {})
        
        health = player.get('health', 0)
        food = player.get('food', 0)
        
        health_color = DarkTheme.ACCENT_RED if health < 10 else DarkTheme.ACCENT_GREEN
        food_color = DarkTheme.ACCENT_RED if food < 6 else DarkTheme.ACCENT_GREEN
        
        self.health_label.config(
            text=f"❤ {health:.1f}/20",
            foreground=health_color
        )
        self.food_label.config(
            text=f"🍖 {food}/20",
            foreground=food_color
        )
        
        # Update position
        pos = player.get('position', {})
        self.position_label.config(
            text=f"Position: {pos.get('x', 0):.1f}, {pos.get('y', 0):.1f}, {pos.get('z', 0):.1f}"
        )
        
        # Update time
        game = game_state.get('game', {})
        time_ticks = game.get('time', 0)
        time_phase = self._get_time_phase(time_ticks)
        self.time_label.config(text=f"Time: {time_phase}")
        
        # Update threats
        self._update_threats(game_state.get('entities', []))
        
        # Update blocks
        self._update_blocks(game_state.get('nearby_blocks', []))
        
        # Update inventory
        self._update_inventory(game_state.get('inventory', []))
    
    def _update_threats(self, entities: list):
        """Update threats display"""
        hostile = [e for e in entities if e.get('hostile', False)]
        
        self._clear_text_widget(self.threats_text, "")
        
        if not hostile:
            self._set_text_widget(
                self.threats_text,
                "No threats detected",
                DarkTheme.ACCENT_GREEN
            )
            return
        
        self.threats_text.config(state=tk.NORMAL)
        
        hostile_sorted = sorted(hostile, key=lambda e: e.get('distance', 999))
        
        for mob in hostile_sorted[:8]:
            distance = mob.get('distance', 0)
            threat_level = "HIGH" if distance < 10 else "MED" if distance < 20 else "LOW"
            
            pos = mob.get('position', {})
            text = (
                f"[{threat_level}] {mob.get('type', 'unknown')} - {distance:.1f}m\n"
                f"  ({pos.get('x', 0):.0f}, {pos.get('y', 0):.0f}, {pos.get('z', 0):.0f})\n"
            )
            
            self.threats_text.insert(tk.END, text)
        
        if len(hostile) > 8:
            self.threats_text.insert(tk.END, f"... and {len(hostile) - 8} more")
        
        self.threats_text.config(state=tk.DISABLED)
    
    def _update_blocks(self, blocks: list):
        """Update blocks display"""
        self._clear_text_widget(self.blocks_text, "")
        
        if not blocks:
            self._set_text_widget(self.blocks_text, "No block data available")
            return
        
        blocks_sorted = sorted(blocks, key=lambda b: b.get('distance', 999))
        
        self.blocks_text.config(state=tk.NORMAL)
        
        for block in blocks_sorted[:10]:
            text = (
                f"{block.get('name', 'unknown')} - {block.get('distance', 0):.1f}m\n"
            )
            self.blocks_text.insert(tk.END, text)
        
        if len(blocks) > 10:
            self.blocks_text.insert(tk.END, f"... and {len(blocks) - 10} more")
        
        self.blocks_text.config(state=tk.DISABLED)
    
    def _update_inventory(self, inventory: list):
        """Update inventory display"""
        self._clear_text_widget(self.inventory_text, "")
        
        if not inventory:
            self._set_text_widget(self.inventory_text, "Inventory empty")
            return
        
        self.inventory_text.config(state=tk.NORMAL)
        
        # Count items
        from collections import defaultdict
        item_counts = defaultdict(int)
        
        for item in inventory:
            name = item.get('name', 'unknown')
            count = item.get('count', 1)
            item_counts[name] += count
        
        total = sum(item_counts.values())
        self.inventory_text.insert(tk.END, f"Total: {total} items\n\n")
        
        sorted_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)
        
        for name, count in sorted_items[:15]:
            self.inventory_text.insert(tk.END, f"{name}: {count}\n")
        
        if len(sorted_items) > 15:
            self.inventory_text.insert(tk.END, f"\n... and {len(sorted_items) - 15} more")
        
        self.inventory_text.config(state=tk.DISABLED)
    
    def _get_time_phase(self, ticks: int) -> str:
        """Convert ticks to time phase"""
        ticks = ticks % 24000
        if 0 <= ticks < 6000:
            return "Day"
        elif 6000 <= ticks < 12000:
            return "Noon"
        elif 12000 <= ticks < 18000:
            return "Evening"
        else:
            return "Night"
    
    def _clear_text_widget(self, widget, text=""):
        """Clear and optionally set text in widget"""
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        if text:
            widget.insert(tk.END, text)
        widget.config(state=tk.DISABLED)
    
    def _set_text_widget(self, widget, text, color=None):
        """Set text in widget with optional color"""
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        if color:
            widget.config(fg=color)
        widget.config(state=tk.DISABLED)
    
    def _add_log(self, message: str, tag='info'):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)
        
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > 100:
            self.log_text.delete('1.0', '51.0')
        
        self.log_text.config(state=tk.DISABLED)
    
    def _schedule_status_update(self):
        """Schedule periodic status updates"""
        if self.panel_frame and self.panel_frame.winfo_exists():
            self._update_status()
            self.update_job = self.panel_frame.after(
                3000,
                self._schedule_status_update
            )
    
    def _get_spectator_tool(self):
        """Get Minecraft Spectator tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        if 'minecraft_spectator' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('minecraft_spectator')
    
    def cleanup(self):
        """Cleanup component resources"""
        if self.update_job:
            try:
                self.panel_frame.after_cancel(self.update_job)
            except:
                pass
        
        if self.logger:
            self.logger.system("[Minecraft Spectator] Component cleaned up")


def create_component(parent_gui, ai_core, logger):
    """Factory function called by GUI system"""
    return MinecraftSpectatorComponent(parent_gui, ai_core, logger)
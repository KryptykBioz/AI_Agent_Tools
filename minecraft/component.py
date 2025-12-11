# Filename: BASE/tools/installed/minecraft/component.py
"""
Minecraft Tool - GUI Component
Dynamic GUI panel for Minecraft bot control and monitoring
"""
import tkinter as tk
from tkinter import ttk
from BASE.interface.gui_themes import DarkTheme
import requests
from datetime import datetime


class MinecraftComponent:
    """
    GUI component for Minecraft tool
    Provides interface for controlling bot and monitoring game state
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        """
        Initialize Minecraft component
        
        Args:
            parent_gui: Main GUI instance
            ai_core: AI Core instance
            logger: Logger instance
        """
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        
        # Tool instance
        self.minecraft_tool = None
        
        # GUI elements
        self.panel_frame = None
        self.status_label = None
        self.health_label = None
        self.food_label = None
        self.position_label = None
        self.biome_label = None
        self.time_label = None
        self.threats_text = None
        self.blocks_text = None
        self.inventory_text = None
        self.log_text = None
        
        # Command controls
        self.command_var = None
        self.args_entry = None
        
        # State
        self.connected = False
        self.update_job = None
        self.last_vision = None
    
    def create_panel(self, parent_frame):
        """
        Create the Minecraft control panel
        
        Args:
            parent_frame: Parent frame to add panel to
        """
        # Main panel frame
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="🎮 Minecraft Bot Control",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Create sections
        self._create_status_section()
        self._create_quick_actions_section()
        self._create_command_section()
        self._create_info_section()
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
        
        # Position & Environment
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
        
        self.biome_label = tk.Label(
            env_frame,
            text="Biome: --",
            font=("Consolas", 8),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.biome_label.pack(side=tk.LEFT, padx=10)
        
        self.time_label = tk.Label(
            env_frame,
            text="Time: --",
            font=("Consolas", 8),
            foreground=DarkTheme.FG_PRIMARY,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.time_label.pack(side=tk.LEFT)
    
    def _create_quick_actions_section(self):
        """Create quick action buttons"""
        action_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Quick Actions",
            style="Dark.TLabelframe"
        )
        action_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        btn_frame = ttk.Frame(action_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Action buttons
        actions = [
            ("🛑 Stop", lambda: self._execute_command("stop_movement", [])),
            ("🪵 Get Wood", lambda: self._execute_command("gather_resource", ["oak_log", 5])),
            ("🪨 Get Stone", lambda: self._execute_command("gather_resource", ["stone", 10])),
            ("📊 Status", lambda: self._refresh_status()),
        ]
        
        for text, command in actions:
            btn = ttk.Button(
                btn_frame,
                text=text,
                command=command,
                width=12
            )
            btn.pack(side=tk.LEFT, padx=2)
    
    def _create_command_section(self):
        """Create custom command section"""
        cmd_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Custom Command",
            style="Dark.TLabelframe"
        )
        cmd_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Command selector
        selector_frame = ttk.Frame(cmd_frame)
        selector_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(
            selector_frame,
            text="Command:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.command_var = tk.StringVar()
        command_combo = ttk.Combobox(
            selector_frame,
            textvariable=self.command_var,
            values=[
                'gather_resource',
                'goto_location',
                'move_direction',
                'attack_entity',
                'stop_movement',
                'follow',
                'craft_item',
                'use_item',
                'chat',
                'build'
            ],
            font=("Consolas", 9),
            state='readonly',
            width=20
        )
        command_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Arguments entry
        args_frame = ttk.Frame(cmd_frame)
        args_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(
            args_frame,
            text="Args:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.args_entry = tk.Entry(
            args_frame,
            font=("Consolas", 9),
            bg=DarkTheme.BG_DARK,
            fg=DarkTheme.FG_PRIMARY,
            insertbackground=DarkTheme.FG_PRIMARY,
            relief="solid",
            borderwidth=1
        )
        self.args_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.args_entry.insert(0, "comma, separated, values")
        self.args_entry.bind('<FocusIn>', self._clear_placeholder)
        self.args_entry.bind('<Return>', lambda e: self._execute_custom())
        
        # Execute button
        exec_btn = ttk.Button(
            args_frame,
            text="▶ Execute",
            command=self._execute_custom,
            width=12
        )
        exec_btn.pack(side=tk.LEFT)
    
    def _create_info_section(self):
        """Create information display section"""
        info_container = ttk.Frame(self.panel_frame)
        info_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Left column - Threats & Inventory
        left_column = ttk.Frame(info_container)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 3))
        
        # Threats
        threats_frame = ttk.LabelFrame(
            left_column,
            text="⚠️ Nearby Threats",
            style="Dark.TLabelframe"
        )
        threats_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 3))
        
        self.threats_text = tk.Text(
            threats_frame,
            height=4,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 8),
            bg=DarkTheme.BG_DARK,
            fg=DarkTheme.ACCENT_RED,
            insertbackground=DarkTheme.FG_PRIMARY,
            borderwidth=0
        )
        self.threats_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Inventory
        inv_frame = ttk.LabelFrame(
            left_column,
            text="🎒 Inventory",
            style="Dark.TLabelframe"
        )
        inv_frame.pack(fill=tk.BOTH, expand=True)
        
        self.inventory_text = tk.Text(
            inv_frame,
            height=4,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 8),
            bg=DarkTheme.BG_DARK,
            fg=DarkTheme.FG_PRIMARY,
            insertbackground=DarkTheme.FG_PRIMARY,
            borderwidth=0
        )
        self.inventory_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Right column - Blocks
        blocks_frame = ttk.LabelFrame(
            info_container,
            text="🧱 Nearby Blocks",
            style="Dark.TLabelframe"
        )
        blocks_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(3, 0))
        
        self.blocks_text = tk.Text(
            blocks_frame,
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 8),
            bg=DarkTheme.BG_DARK,
            fg=DarkTheme.FG_SECONDARY,
            insertbackground=DarkTheme.FG_PRIMARY,
            borderwidth=0
        )
        self.blocks_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
    
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
    
    def _clear_placeholder(self, event):
        """Clear placeholder text on focus"""
        if self.args_entry.get() == "comma, separated, values":
            self.args_entry.delete(0, tk.END)
    
    def _execute_custom(self):
        """Execute custom command"""
        command = self.command_var.get()
        if not command:
            self._add_log("No command selected", 'error')
            return
        
        args_text = self.args_entry.get()
        if args_text == "comma, separated, values" or not args_text:
            args = []
        else:
            # Parse arguments
            args = [a.strip() for a in args_text.split(',')]
            # Convert numeric strings to numbers
            args = [
                float(a) if a.replace('.', '').replace('-', '').isdigit() 
                else int(a) if a.replace('-', '').isdigit()
                else a 
                for a in args
            ]
        
        self._execute_command(command, args)
        
        # Clear args
        self.args_entry.delete(0, tk.END)
        self.args_entry.insert(0, "comma, separated, values")
    
    def _execute_command(self, command: str, args: list):
        """Execute Minecraft command"""
        self.minecraft_tool = self._get_minecraft_tool()
        
        if not self.minecraft_tool:
            self._add_log("Minecraft tool not available", 'error')
            return
        
        if not self.minecraft_tool.is_available():
            self._add_log("Bot not connected", 'error')
            return
        
        self._add_log(f"Executing: {command} {args}", 'cmd')
        
        # Execute via AI Core
        if self.ai_core.main_loop:
            import asyncio
            
            async def execute_async():
                result = await self.minecraft_tool.execute(command, args)
                
                if result.get('success'):
                    message = result.get('content', 'Success')
                    self._add_log(message, 'success')
                else:
                    error = result.get('content', 'Command failed')
                    self._add_log(error, 'error')
            
            asyncio.run_coroutine_threadsafe(execute_async(), self.ai_core.main_loop)
    
    def _refresh_status(self):
        """Force status refresh"""
        self._add_log("Refreshing status...", 'info')
        self._update_status()
    
    def _update_status(self):
        """Update all status displays"""
        self.minecraft_tool = self._get_minecraft_tool()
        
        if not self.minecraft_tool:
            self._update_status_disconnected()
            return
        
        # Check connection
        if not self.minecraft_tool.is_available():
            self._update_status_disconnected()
            return
        
        # Connected - update displays
        self._update_status_connected()
        self._update_vision_data()
    
    def _update_status_disconnected(self):
        """Update UI for disconnected state"""
        self.connected = False
        
        self.status_label.config(
            text="⚫ Not Connected",
            foreground=DarkTheme.FG_MUTED
        )
        
        self.health_label.config(text="❤ --/20", foreground=DarkTheme.FG_MUTED)
        self.food_label.config(text="🍖 --/20", foreground=DarkTheme.FG_MUTED)
        self.position_label.config(text="Position: --, --, --")
        self.biome_label.config(text="Biome: --")
        self.time_label.config(text="Time: --")
        
        self._clear_text_widget(self.threats_text, "Not connected")
        self._clear_text_widget(self.blocks_text, "Not connected")
        self._clear_text_widget(self.inventory_text, "Not connected")
    
    def _update_status_connected(self):
        """Update UI for connected state"""
        self.connected = True
        
        self.status_label.config(
            text="🟢 Connected",
            foreground=DarkTheme.ACCENT_GREEN
        )
    
    def _update_vision_data(self):
        """Update vision data displays"""
        if not self.minecraft_tool:
            return
        
        try:
            # Get vision data from tool
            api_base = self.minecraft_tool.api_base
            response = requests.get(f"{api_base}/api/vision", timeout=2.0)
            
            if response.status_code != 200:
                return
            
            data = response.json()
            if data.get('status') != 'success':
                return
            
            vision = data.get('vision', {})
            self.last_vision = vision
            
            # Update health & food
            health = vision.get('health', 0)
            food = vision.get('food', 0)
            
            health_color = DarkTheme.ACCENT_RED if health < 10 else DarkTheme.ACCENT_GREEN
            food_color = DarkTheme.ACCENT_RED if food < 6 else DarkTheme.ACCENT_GREEN
            
            self.health_label.config(text=f"❤ {health}/20", foreground=health_color)
            self.food_label.config(text=f"🍖 {food}/20", foreground=food_color)
            
            # Update position
            pos = vision.get('position', {})
            self.position_label.config(
                text=f"Position: {pos.get('x', 0):.1f}, {pos.get('y', 0):.1f}, {pos.get('z', 0):.1f}"
            )
            
            # Update biome
            biome = vision.get('biome', 'unknown').replace('_', ' ').title()
            self.biome_label.config(text=f"Biome: {biome}")
            
            # Update time
            time_info = vision.get('time', {})
            phase = time_info.get('phase', 'unknown').title()
            self.time_label.config(text=f"Time: {phase}")
            
            # Update threats
            self._update_threats(vision.get('entitiesInSight', []))
            
            # Update blocks
            self._update_blocks(vision.get('blocksInSight', []))
            
            # Update inventory
            self._update_inventory(vision.get('inventory', {}))
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"[Minecraft GUI] Error updating vision: {e}")
    
    def _update_threats(self, entities: list):
        """Update threats display"""
        hostile = [e for e in entities if e.get('isHostile')]
        
        self._clear_text_widget(self.threats_text, "")
        
        if not hostile:
            self._set_text_widget(self.threats_text, "No threats detected", DarkTheme.ACCENT_GREEN)
            return
        
        self.threats_text.config(state=tk.NORMAL)
        
        for mob in hostile[:5]:  # Show top 5 threats
            threat = mob.get('threatLevel', 5)
            threat_str = "[HIGH]" if threat >= 8 else "[MED]" if threat >= 6 else "[LOW]"
            
            text = (
                f"{threat_str} {mob.get('type', 'unknown')} - "
                f"{mob.get('distance', 0):.1f}m {mob.get('direction', '')}\n"
            )
            
            self.threats_text.insert(tk.END, text)
        
        self.threats_text.config(state=tk.DISABLED)
    
    def _update_blocks(self, blocks: list):
        """Update blocks display"""
        self._clear_text_widget(self.blocks_text, "")
        
        if not blocks:
            self._set_text_widget(self.blocks_text, "No blocks in sight")
            return
        
        # Sort by distance
        blocks_sorted = sorted(blocks, key=lambda b: b.get('distance', 999))
        
        self.blocks_text.config(state=tk.NORMAL)
        
        for block in blocks_sorted[:10]:  # Show top 10
            pos = block.get('position', {})
            text = (
                f"{block.get('name', 'unknown')} - {block.get('distance', 0):.1f}m\n"
                f"  ({pos.get('x', 0)}, {pos.get('y', 0)}, {pos.get('z', 0)})\n"
            )
            self.blocks_text.insert(tk.END, text)
        
        self.blocks_text.config(state=tk.DISABLED)
    
    def _update_inventory(self, inventory: dict):
        """Update inventory display"""
        self._clear_text_widget(self.inventory_text, "")
        
        self.inventory_text.config(state=tk.NORMAL)
        
        # Item in hand
        hand = inventory.get('itemInHand')
        if hand:
            holding = f"Holding: {hand.get('name', 'unknown')}"
            if hand.get('count', 1) > 1:
                holding += f" x{hand['count']}"
            self.inventory_text.insert(tk.END, f"{holding}\n")
        else:
            self.inventory_text.insert(tk.END, "Holding: empty\n")
        
        # Total items
        total = inventory.get('totalItems', 0)
        self.inventory_text.insert(tk.END, f"Total: {total} items\n\n")
        
        # Categories
        categories = inventory.get('categories', {})
        for cat in ['tools', 'weapons', 'food', 'ores']:
            items = categories.get(cat, [])
            if items:
                items_str = ', '.join([f"{i['name']} x{i['count']}" for i in items[:3]])
                self.inventory_text.insert(tk.END, f"{cat.title()}: {items_str}\n")
        
        self.inventory_text.config(state=tk.DISABLED)
    
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
        
        # Limit log size
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > 100:
            self.log_text.delete('1.0', '51.0')
        
        self.log_text.config(state=tk.DISABLED)
    
    def _schedule_status_update(self):
        """Schedule periodic status updates"""
        if self.panel_frame and self.panel_frame.winfo_exists():
            self._update_status()
            # Update every 3 seconds (less frequent than context loop)
            self.update_job = self.panel_frame.after(3000, self._schedule_status_update)
    
    def _get_minecraft_tool(self):
        """Get Minecraft tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'minecraft' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('minecraft')
    
    def cleanup(self):
        """Cleanup component resources"""
        # Cancel scheduled updates
        if self.update_job:
            try:
                self.panel_frame.after_cancel(self.update_job)
            except:
                pass
        
        if self.logger:
            self.logger.system("[Minecraft] Component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        MinecraftComponent instance
    """
    return MinecraftComponent(parent_gui, ai_core, logger)
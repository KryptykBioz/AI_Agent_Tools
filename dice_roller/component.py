# Filename: BASE/tools/installed/dice_roller/component.py
"""
Dice Roller Tool - GUI Component
Interactive GUI panel for dice rolling with quick actions and history
"""
import tkinter as tk
from tkinter import ttk
from BASE.interface.gui_themes import DarkTheme
from datetime import datetime
import asyncio


class DiceRollerComponent:
    """
    GUI component for Dice Roller tool
    Provides interface for rolling dice, viewing history, and quick actions
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        """
        Initialize Dice Roller component
        
        Args:
            parent_gui: Main GUI instance
            ai_core: AI Core instance
            logger: Logger instance
        """
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        
        # Tool instance
        self.dice_tool = None
        
        # GUI elements
        self.panel_frame = None
        self.status_label = None
        self.last_roll_label = None
        self.history_text = None
        self.log_text = None
        
        # Roll controls
        self.dice_count_var = None
        self.dice_type_var = None
        self.modifier_var = None
        self.notation_var = None
        
        # State
        self.update_job = None
        self.last_result = None
    
    def create_panel(self, parent_frame):
        """
        Create the Dice Roller control panel
        
        Args:
            parent_frame: Parent frame to add panel to
        """
        # Main panel frame
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="🎲 Dice Roller",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Create sections
        self._create_status_section()
        self._create_quick_roll_section()
        self._create_custom_roll_section()
        self._create_advanced_section()
        self._create_history_section()
        self._create_log_section()
        
        # Start status updates
        self._schedule_status_update()
        
        return self.panel_frame
    
    def _create_status_section(self):
        """Create status display section"""
        status_frame = ttk.Frame(self.panel_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Tool status
        self.status_label = tk.Label(
            status_frame,
            text="⚫ Not Active",
            font=("Segoe UI", 9, "bold"),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Last roll result (big display)
        self.last_roll_label = tk.Label(
            status_frame,
            text="--",
            font=("Segoe UI", 24, "bold"),
            foreground=DarkTheme.ACCENT_PURPLE,
            background=DarkTheme.BG_DARKER,
            width=8
        )
        self.last_roll_label.pack(side=tk.RIGHT, padx=10)
    
    def _create_quick_roll_section(self):
        """Create quick roll buttons for common dice"""
        quick_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Quick Rolls",
            style="Dark.TLabelframe"
        )
        quick_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Standard dice buttons
        btn_frame1 = ttk.Frame(quick_frame)
        btn_frame1.pack(fill=tk.X, padx=5, pady=5)
        
        dice_types = [
            ("d4", "1d4"),
            ("d6", "1d6"),
            ("d8", "1d8"),
            ("d10", "1d10"),
            ("d12", "1d12"),
            ("d20", "1d20"),
            ("d100", "1d100")
        ]
        
        for label, notation in dice_types:
            btn = ttk.Button(
                btn_frame1,
                text=label,
                command=lambda n=notation: self._quick_roll(n),
                width=6
            )
            btn.pack(side=tk.LEFT, padx=2)
        
        # Common roll combinations
        btn_frame2 = ttk.Frame(quick_frame)
        btn_frame2.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        common_rolls = [
            ("3d6 (Stats)", "3d6"),
            ("2d20 (Adv)", "advantage"),
            ("2d20 (Dis)", "disadvantage"),
            ("1d20+5", "1d20+5")
        ]
        
        for label, action in common_rolls:
            btn = ttk.Button(
                btn_frame2,
                text=label,
                command=lambda a=action: self._quick_roll(a),
                width=12
            )
            btn.pack(side=tk.LEFT, padx=2)
    
    def _create_custom_roll_section(self):
        """Create custom roll builder section"""
        custom_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Custom Roll",
            style="Dark.TLabelframe"
        )
        custom_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Builder controls
        builder_frame = ttk.Frame(custom_frame)
        builder_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Dice count
        ttk.Label(
            builder_frame,
            text="Count:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.dice_count_var = tk.StringVar(value="1")
        count_spin = ttk.Spinbox(
            builder_frame,
            from_=1,
            to=100,
            textvariable=self.dice_count_var,
            width=5,
            font=("Consolas", 9)
        )
        count_spin.pack(side=tk.LEFT, padx=(0, 10))
        
        # Dice type
        ttk.Label(
            builder_frame,
            text="Die:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.dice_type_var = tk.StringVar(value="d20")
        dice_combo = ttk.Combobox(
            builder_frame,
            textvariable=self.dice_type_var,
            values=['d4', 'd6', 'd8', 'd10', 'd12', 'd20', 'd100'],
            font=("Consolas", 9),
            state='readonly',
            width=8
        )
        dice_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Modifier
        ttk.Label(
            builder_frame,
            text="Modifier:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.modifier_var = tk.StringVar(value="0")
        modifier_spin = ttk.Spinbox(
            builder_frame,
            from_=-100,
            to=100,
            textvariable=self.modifier_var,
            width=5,
            font=("Consolas", 9)
        )
        modifier_spin.pack(side=tk.LEFT, padx=(0, 10))
        
        # Roll button
        roll_btn = ttk.Button(
            builder_frame,
            text="🎲 Roll",
            command=self._custom_roll,
            width=10
        )
        roll_btn.pack(side=tk.LEFT, padx=5)
        
        # Direct notation input
        notation_frame = ttk.Frame(custom_frame)
        notation_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(
            notation_frame,
            text="Notation:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.notation_var = tk.StringVar(value="1d20+5")
        notation_entry = ttk.Entry(
            notation_frame,
            textvariable=self.notation_var,
            font=("Consolas", 9)
        )
        notation_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        notation_entry.bind('<Return>', lambda e: self._notation_roll())
        
        notation_btn = ttk.Button(
            notation_frame,
            text="Roll Notation",
            command=self._notation_roll,
            width=15
        )
        notation_btn.pack(side=tk.LEFT)
    
    def _create_advanced_section(self):
        """Create advanced features section"""
        adv_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Advanced",
            style="Dark.TLabelframe"
        )
        adv_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        btn_frame = ttk.Frame(adv_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Advanced buttons
        ttk.Button(
            btn_frame,
            text="📊 Stats",
            command=self._show_stats,
            width=12
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="📜 History",
            command=self._show_history,
            width=12
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="🗑️ Clear History",
            command=self._clear_history,
            width=12
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="🔄 Refresh",
            command=self._refresh_status,
            width=12
        ).pack(side=tk.LEFT, padx=2)
    
    def _create_history_section(self):
        """Create roll history display"""
        history_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Recent Rolls",
            style="Dark.TLabelframe"
        )
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # History text widget
        history_scroll = ttk.Scrollbar(history_frame)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_text = tk.Text(
            history_frame,
            height=6,
            width=40,
            font=("Consolas", 9),
            background=DarkTheme.BG_DARK,
            foreground=DarkTheme.FG_PRIMARY,
            insertbackground=DarkTheme.FG_PRIMARY,
            wrap=tk.WORD,
            state=tk.DISABLED,
            yscrollcommand=history_scroll.set
        )
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        history_scroll.config(command=self.history_text.yview)
        
        # Configure tags
        self.history_text.tag_config('result', foreground=DarkTheme.ACCENT_PURPLE, font=("Consolas", 9, "bold"))
        self.history_text.tag_config('notation', foreground=DarkTheme.ACCENT_BLUE)
        self.history_text.tag_config('advantage', foreground=DarkTheme.ACCENT_GREEN)
        self.history_text.tag_config('disadvantage', foreground=DarkTheme.ACCENT_RED)
    
    def _create_log_section(self):
        """Create activity log section"""
        log_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Activity Log",
            style="Dark.TLabelframe"
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Log text widget
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(
            log_frame,
            height=5,
            width=40,
            font=("Consolas", 8),
            background=DarkTheme.BG_DARK,
            foreground=DarkTheme.FG_MUTED,
            insertbackground=DarkTheme.FG_PRIMARY,
            wrap=tk.WORD,
            state=tk.DISABLED,
            yscrollcommand=log_scroll.set
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        log_scroll.config(command=self.log_text.yview)
        
        # Configure tags
        self.log_text.tag_config('info', foreground=DarkTheme.FG_PRIMARY)
        self.log_text.tag_config('success', foreground=DarkTheme.ACCENT_GREEN)
        self.log_text.tag_config('error', foreground=DarkTheme.ACCENT_RED)
        self.log_text.tag_config('warning', foreground=DarkTheme.ACCENT_YELLOW)
    
    # ========================================================================
    # ROLL ACTIONS
    # ========================================================================
    
    def _quick_roll(self, notation_or_action: str):
        """Execute a quick roll"""
        self._add_log(f"Quick roll: {notation_or_action}", 'info')
        
        if notation_or_action == "advantage":
            self._execute_command("advantage", [])
        elif notation_or_action == "disadvantage":
            self._execute_command("disadvantage", [])
        else:
            # Standard roll
            self._execute_command("roll", [notation_or_action])
    
    def _custom_roll(self):
        """Execute custom roll from builder"""
        try:
            count = int(self.dice_count_var.get())
            dice_type = self.dice_type_var.get().replace('d', '')
            modifier = int(self.modifier_var.get())
            
            # Build notation
            notation = f"{count}d{dice_type}"
            if modifier != 0:
                notation += f"{modifier:+d}"
            
            self._add_log(f"Custom roll: {notation}", 'info')
            self._execute_command("roll", [notation])
        
        except ValueError as e:
            self._add_log(f"Invalid input: {e}", 'error')
    
    def _notation_roll(self):
        """Execute roll from notation entry"""
        notation = self.notation_var.get().strip()
        if not notation:
            self._add_log("Empty notation", 'warning')
            return
        
        self._add_log(f"Notation roll: {notation}", 'info')
        
        # Check if it's advantage/disadvantage
        if notation.lower() in ['advantage', 'adv']:
            self._execute_command("advantage", [])
        elif notation.lower() in ['disadvantage', 'dis', 'disadv']:
            self._execute_command("disadvantage", [])
        else:
            self._execute_command("roll", [notation])
    
    def _show_stats(self):
        """Show statistics for current notation"""
        notation = self.notation_var.get().strip()
        if not notation:
            notation = f"{self.dice_count_var.get()}{self.dice_type_var.get()}"
            modifier = int(self.modifier_var.get())
            if modifier != 0:
                notation += f"{modifier:+d}"
        
        self._add_log(f"Calculating stats for: {notation}", 'info')
        self._execute_command("stats", [notation])
    
    def _show_history(self):
        """Show roll history"""
        self._add_log("Fetching roll history", 'info')
        self._execute_command("history", [10])
    
    def _clear_history(self):
        """Clear roll history"""
        self._add_log("Clearing roll history", 'warning')
        self._execute_command("clear_history", [])
    
    def _refresh_status(self):
        """Refresh tool status"""
        self._update_status()
        self._add_log("Status refreshed", 'success')
    
    # ========================================================================
    # COMMAND EXECUTION
    # ========================================================================
    
    def _execute_command(self, command: str, args: list):
        """
        Execute dice roller command asynchronously
        
        Args:
            command: Command name
            args: Command arguments
        """
        tool = self._get_dice_tool()
        if not tool:
            self._add_log("Dice roller not active", 'error')
            return
        
        # Execute command asynchronously
        try:
            # Get event loop from AI core
            if hasattr(self.ai_core, 'event_loop'):
                loop = self.ai_core.event_loop
            else:
                loop = asyncio.get_event_loop()
            
            # Schedule command execution
            future = asyncio.run_coroutine_threadsafe(
                tool.execute(command, args),
                loop
            )
            
            # Wait for result (with timeout)
            result = future.result(timeout=5.0)
            
            # Handle result
            self._handle_command_result(command, result)
        
        except Exception as e:
            self._add_log(f"Command failed: {e}", 'error')
            if self.logger:
                self.logger.error(f"[Dice Roller GUI] Command error: {e}")
    
    def _handle_command_result(self, command: str, result: dict):
        """
        Handle command execution result
        
        Args:
            command: Command that was executed
            result: Result dictionary from tool
        """
        if not result.get('success'):
            # Error result
            self._add_log(f"Error: {result.get('content', 'Unknown error')}", 'error')
            return
        
        content = result.get('content', '')
        metadata = result.get('metadata', {})
        
        # Update last roll display for roll commands
        if command in ['roll', 'advantage', 'disadvantage']:
            total = metadata.get('total')
            if total is not None:
                self.last_roll_label.config(text=str(total))
                self.last_result = result
        
        # Log success
        self._add_log(content.split('\n')[0], 'success')
        
        # Update history display
        if command == 'history':
            self._update_history_display(content)
        elif command in ['roll', 'advantage', 'disadvantage']:
            # Add to history display
            self._add_to_history_display(command, content, metadata)
        elif command == 'stats':
            # Show stats in log
            for line in content.split('\n'):
                self._add_log(line.strip(), 'info')
    
    def _add_to_history_display(self, command: str, content: str, metadata: dict):
        """Add roll to history display"""
        self.history_text.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format based on command type
        if command == 'advantage':
            self.history_text.insert(tk.END, f"[{timestamp}] ", 'info')
            self.history_text.insert(tk.END, "Advantage ", 'advantage')
            total = metadata.get('total', '?')
            self.history_text.insert(tk.END, f"= {total}\n", 'result')
        elif command == 'disadvantage':
            self.history_text.insert(tk.END, f"[{timestamp}] ", 'info')
            self.history_text.insert(tk.END, "Disadvantage ", 'disadvantage')
            total = metadata.get('total', '?')
            self.history_text.insert(tk.END, f"= {total}\n", 'result')
        else:
            notation = metadata.get('notation', '?')
            total = metadata.get('total', '?')
            self.history_text.insert(tk.END, f"[{timestamp}] ", 'info')
            self.history_text.insert(tk.END, f"{notation} ", 'notation')
            self.history_text.insert(tk.END, f"= {total}\n", 'result')
        
        self.history_text.see(tk.END)
        
        # Limit history size
        lines = int(self.history_text.index('end-1c').split('.')[0])
        if lines > 50:
            self.history_text.delete('1.0', '26.0')
        
        self.history_text.config(state=tk.DISABLED)
    
    def _update_history_display(self, history_text: str):
        """Update history display with full history"""
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete("1.0", tk.END)
        
        # Parse and colorize history
        lines = history_text.split('\n')
        for line in lines:
            if '→ Kept' in line:
                # Advantage/Disadvantage
                if 'Advantage' in line:
                    self.history_text.insert(tk.END, line + '\n', 'advantage')
                else:
                    self.history_text.insert(tk.END, line + '\n', 'disadvantage')
            elif '=' in line and not line.startswith('**'):
                # Standard roll
                parts = line.split('=')
                self.history_text.insert(tk.END, parts[0], 'notation')
                if len(parts) > 1:
                    self.history_text.insert(tk.END, '=' + parts[1] + '\n', 'result')
            else:
                # Header or other
                self.history_text.insert(tk.END, line + '\n')
        
        self.history_text.config(state=tk.DISABLED)
    
    # ========================================================================
    # STATUS UPDATES
    # ========================================================================
    
    def _update_status(self):
        """Update tool status display"""
        tool = self._get_dice_tool()
        
        if not tool:
            self._update_status_inactive()
            return
        
        if not tool.is_available():
            self._update_status_inactive()
            return
        
        self._update_status_active()
    
    def _update_status_inactive(self):
        """Update UI for inactive state"""
        self.status_label.config(
            text="⚫ Not Active",
            foreground=DarkTheme.FG_MUTED
        )
    
    def _update_status_active(self):
        """Update UI for active state"""
        self.status_label.config(
            text="🟢 Active",
            foreground=DarkTheme.ACCENT_GREEN
        )
    
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
    
    def _get_dice_tool(self):
        """Get Dice Roller tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'dice_roller' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('dice_roller')
    
    def cleanup(self):
        """Cleanup component resources"""
        # Cancel scheduled updates
        if self.update_job:
            try:
                self.panel_frame.after_cancel(self.update_job)
            except:
                pass
        
        if self.logger:
            self.logger.system("[Dice Roller] Component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        DiceRollerComponent instance
    """
    return DiceRollerComponent(parent_gui, ai_core, logger)
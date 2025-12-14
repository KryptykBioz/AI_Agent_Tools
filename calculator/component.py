# Filename: BASE/tools/installed/calculator/component.py
"""
Calculator Tool - GUI Component
Interactive calculator interface with expression input and history
"""
import tkinter as tk
from tkinter import ttk, messagebox
from BASE.interface.gui_themes import DarkTheme


class CalculatorComponent:
    """
    GUI component for Calculator tool
    Provides interface for calculations, conversions, and more
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        """
        Initialize calculator component
        
        Args:
            parent_gui: Main GUI instance
            ai_core: AI Core instance
            logger: Logger instance
        """
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        
        # Tool instance
        self.calculator_tool = None
        
        # GUI elements
        self.panel_frame = None
        self.mode_var = None
        self.input_entry = None
        self.result_display = None
        self.history_display = None
        
        # History tracking
        self.calculation_history = []
    
    def create_panel(self, parent_frame):
        """
        Create the calculator panel
        
        Args:
            parent_frame: Parent frame to add panel to
        """
        # Main panel frame
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="🔢 Calculator",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Mode selector
        self._create_mode_section()
        
        # Input section
        self._create_input_section()
        
        # Quick buttons
        self._create_quick_buttons()
        
        # Result display
        self._create_result_section()
        
        # History display
        self._create_history_section()
        
        return self.panel_frame
    
    def _create_mode_section(self):
        """Create mode selector"""
        mode_frame = ttk.Frame(self.panel_frame)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(
            mode_frame,
            text="Mode:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.mode_var = tk.StringVar(value="calculate")
        
        modes = [
            ("Calculate", "calculate"),
            ("Convert", "convert"),
            ("Solve", "solve"),
            ("Statistics", "statistics")
        ]
        
        for text, value in modes:
            ttk.Radiobutton(
                mode_frame,
                text=text,
                variable=self.mode_var,
                value=value,
                command=self._on_mode_changed
            ).pack(side=tk.LEFT, padx=(0, 10))
    
    def _create_input_section(self):
        """Create input section"""
        input_frame = ttk.Frame(self.panel_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Input label
        self.input_label = ttk.Label(
            input_frame,
            text="Expression:",
            style="TLabel"
        )
        self.input_label.pack(anchor=tk.W, pady=(0, 3))
        
        # Input entry with execute button
        entry_container = ttk.Frame(input_frame)
        entry_container.pack(fill=tk.X)
        
        self.input_entry = ttk.Entry(
            entry_container,
            font=("Consolas", 10)
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_entry.bind("<Return>", lambda e: self._execute_calculation())
        
        ttk.Button(
            entry_container,
            text="=",
            command=self._execute_calculation,
            width=5
        ).pack(side=tk.RIGHT)
    
    def _create_quick_buttons(self):
        """Create quick action buttons"""
        button_frame = ttk.Frame(self.panel_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Calculator buttons
        calc_buttons = [
            ("7", "7"), ("8", "8"), ("9", "9"), ("+", "+"),
            ("4", "4"), ("5", "5"), ("6", "6"), ("-", "-"),
            ("1", "1"), ("2", "2"), ("3", "3"), ("*", "*"),
            ("0", "0"), (".", "."), ("^", "^"), ("/", "/"),
        ]
        
        # Create grid
        for i, (text, value) in enumerate(calc_buttons):
            row = i // 4
            col = i % 4
            
            btn = tk.Button(
                button_frame,
                text=text,
                command=lambda v=value: self._insert_text(v),
                bg=DarkTheme.BG_DARK,
                fg=DarkTheme.FG_PRIMARY,
                font=("Consolas", 10),
                relief="solid",
                borderwidth=1,
                padx=10,
                pady=5,
                cursor="hand2"
            )
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
        
        # Configure grid weights
        for i in range(4):
            button_frame.grid_columnconfigure(i, weight=1)
        
        # Function buttons row
        func_frame = ttk.Frame(self.panel_frame)
        func_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        functions = [
            ("sqrt", "sqrt("),
            ("sin", "sin("),
            ("cos", "cos("),
            ("log", "log("),
            ("(", "("),
            (")", ")"),
            ("Clear", "clear")
        ]
        
        for text, value in functions:
            if value == "clear":
                btn = ttk.Button(
                    func_frame,
                    text=text,
                    command=self._clear_input,
                    width=8
                )
            else:
                btn = tk.Button(
                    func_frame,
                    text=text,
                    command=lambda v=value: self._insert_text(v),
                    bg=DarkTheme.BG_DARKER,
                    fg=DarkTheme.ACCENT_PURPLE,
                    font=("Consolas", 9),
                    relief="solid",
                    borderwidth=1,
                    padx=5,
                    pady=3,
                    cursor="hand2"
                )
            btn.pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
    
    def _create_result_section(self):
        """Create result display"""
        result_frame = ttk.Frame(self.panel_frame)
        result_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(
            result_frame,
            text="Result:",
            style="TLabel"
        ).pack(anchor=tk.W, pady=(0, 3))
        
        self.result_display = tk.Label(
            result_frame,
            text="Ready",
            font=("Consolas", 12, "bold"),
            foreground=DarkTheme.ACCENT_GREEN,
            background=DarkTheme.BG_DARK,
            anchor=tk.W,
            padx=10,
            pady=8,
            relief="solid",
            borderwidth=1
        )
        self.result_display.pack(fill=tk.X)
    
    def _create_history_section(self):
        """Create history display"""
        history_frame = ttk.Frame(self.panel_frame)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Header with clear button
        header_frame = ttk.Frame(history_frame)
        header_frame.pack(fill=tk.X, pady=(0, 3))
        
        ttk.Label(
            header_frame,
            text="History:",
            style="TLabel"
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            header_frame,
            text="Clear History",
            command=self._clear_history,
            width=12
        ).pack(side=tk.RIGHT)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient='vertical')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # History display
        self.history_display = tk.Text(
            history_frame,
            height=6,
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
        self.history_display.pack(fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.history_display.yview)
        
        # Configure tags
        self.history_display.tag_configure(
            "input",
            foreground=DarkTheme.FG_MUTED
        )
        self.history_display.tag_configure(
            "result",
            foreground=DarkTheme.ACCENT_GREEN,
            font=("Consolas", 9, "bold")
        )
        self.history_display.tag_configure(
            "error",
            foreground=DarkTheme.ACCENT_RED
        )
    
    def _on_mode_changed(self):
        """Handle mode selection change"""
        mode = self.mode_var.get()
        
        # Update input label based on mode
        labels = {
            'calculate': 'Expression:',
            'convert': 'Value, From Unit, To Unit:',
            'solve': 'Equation, Variable:',
            'statistics': 'Numbers (comma-separated):'
        }
        
        self.input_label.config(text=labels.get(mode, 'Input:'))
        
        # Update placeholder
        placeholders = {
            'calculate': '2 + 2 * 3',
            'convert': '100, celsius, fahrenheit',
            'solve': '2*x + 5 = 15, x',
            'statistics': '1, 2, 3, 4, 5'
        }
        
        self.input_entry.delete(0, tk.END)
        self.result_display.config(text="Ready", foreground=DarkTheme.ACCENT_GREEN)
    
    def _insert_text(self, text: str):
        """Insert text at cursor position"""
        current_pos = self.input_entry.index(tk.INSERT)
        self.input_entry.insert(current_pos, text)
        self.input_entry.focus()
    
    def _clear_input(self):
        """Clear input field"""
        self.input_entry.delete(0, tk.END)
        self.input_entry.focus()
    
    def _execute_calculation(self):
        """Execute calculation based on mode"""
        mode = self.mode_var.get()
        input_text = self.input_entry.get().strip()
        
        if not input_text:
            messagebox.showwarning("Empty Input", "Please enter a value")
            return
        
        self.calculator_tool = self._get_calculator_tool()
        
        if not self.calculator_tool:
            self._show_error("Calculator tool not available")
            return
        
        # Parse input based on mode
        try:
            if mode == 'calculate':
                args = [input_text]
                command = 'calculate'
            
            elif mode == 'convert':
                parts = [p.strip() for p in input_text.split(',')]
                if len(parts) != 3:
                    self._show_error("Format: value, from_unit, to_unit")
                    return
                args = [float(parts[0]), parts[1], parts[2]]
                command = 'convert'
            
            elif mode == 'solve':
                parts = [p.strip() for p in input_text.split(',')]
                if len(parts) != 2:
                    self._show_error("Format: equation, variable")
                    return
                args = parts
                command = 'solve'
            
            elif mode == 'statistics':
                numbers = [float(n.strip()) for n in input_text.split(',')]
                args = [numbers]
                command = 'statistics'
            
            else:
                self._show_error("Unknown mode")
                return
            
            # Execute via tool
            if self.ai_core.main_loop:
                import asyncio
                
                async def execute_async():
                    result = await self.calculator_tool.execute(command, args)
                    
                    if result.get('success'):
                        content = result.get('content', '')
                        self._show_result(content, input_text)
                        self.logger.tool(f"[Calculator] {input_text} → {content}")
                    else:
                        error = result.get('content', 'Unknown error')
                        self._show_error(error)
                
                asyncio.run_coroutine_threadsafe(execute_async(), self.ai_core.main_loop)
        
        except ValueError as e:
            self._show_error(f"Invalid input: {e}")
        except Exception as e:
            self._show_error(str(e))
    
    def _show_result(self, result: str, input_text: str):
        """Display result"""
        # Update result display (first line only for display)
        display_text = result.split('\n')[0]
        if len(display_text) > 50:
            display_text = display_text[:47] + "..."
        
        self.result_display.config(
            text=display_text,
            foreground=DarkTheme.ACCENT_GREEN
        )
        
        # Add to history
        self._add_to_history(input_text, result, is_error=False)
    
    def _show_error(self, error: str):
        """Display error"""
        self.result_display.config(
            text=f"Error: {error}",
            foreground=DarkTheme.ACCENT_RED
        )
        
        # Add to history
        input_text = self.input_entry.get().strip()
        self._add_to_history(input_text, f"Error: {error}", is_error=True)
    
    def _add_to_history(self, input_text: str, result: str, is_error: bool = False):
        """Add calculation to history"""
        self.calculation_history.append({
            'input': input_text,
            'result': result,
            'error': is_error
        })
        
        # Update history display
        self.history_display.config(state=tk.NORMAL)
        
        # Add input
        self.history_display.insert(tk.END, f"► {input_text}\n", "input")
        
        # Add result
        tag = "error" if is_error else "result"
        # For multi-line results, only show first line in history
        result_display = result.split('\n')[0]
        if len(result.split('\n')) > 1:
            result_display += " ..."
        self.history_display.insert(tk.END, f"  {result_display}\n\n", tag)
        
        self.history_display.config(state=tk.DISABLED)
        self.history_display.see(tk.END)
        
        # Limit history to last 50 entries
        if len(self.calculation_history) > 50:
            self.calculation_history = self.calculation_history[-50:]
            self._rebuild_history_display()
    
    def _clear_history(self):
        """Clear calculation history"""
        self.calculation_history.clear()
        self.history_display.config(state=tk.NORMAL)
        self.history_display.delete("1.0", tk.END)
        self.history_display.config(state=tk.DISABLED)
        self.logger.system("[Calculator] History cleared")
    
    def _rebuild_history_display(self):
        """Rebuild history display from history list"""
        self.history_display.config(state=tk.NORMAL)
        self.history_display.delete("1.0", tk.END)
        
        for entry in self.calculation_history:
            self.history_display.insert(tk.END, f"► {entry['input']}\n", "input")
            tag = "error" if entry['error'] else "result"
            result_display = entry['result'].split('\n')[0]
            if len(entry['result'].split('\n')) > 1:
                result_display += " ..."
            self.history_display.insert(tk.END, f"  {result_display}\n\n", tag)
        
        self.history_display.config(state=tk.DISABLED)
        self.history_display.see(tk.END)
    
    def _get_calculator_tool(self):
        """Get calculator tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        if 'calculator' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('calculator')
    
    def cleanup(self):
        """Cleanup component resources"""
        self.logger.system("[Calculator] Component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        CalculatorComponent instance
    """
    return CalculatorComponent(parent_gui, ai_core, logger)
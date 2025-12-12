# Filename: BASE/tools/installed/coding_VS_Code/component.py
"""
Coding Tool (VS Code) - GUI Component
Dynamic GUI panel for VS Code integration
"""
import tkinter as tk
from tkinter import ttk
from BASE.interface.gui_themes import DarkTheme


class CodingToolComponent:
    """
    GUI component for Coding (VS Code) tool
    Provides interface for VS Code extension control and monitoring
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        """
        Initialize coding tool component
        
        Args:
            parent_gui: Main GUI instance
            ai_core: AI Core instance
            logger: Logger instance
        """
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        
        # Tool instance (will be set when available)
        self.coding_tool = None
        
        # GUI elements
        self.panel_frame = None
        self.status_label = None
        self.test_button = None
        self.open_files_display = None
        self.instruction_entry = None
        self.send_button = None
        
        # Update timer
        self.update_job = None
    
    def create_panel(self, parent_frame):
        """
        Create the coding tool panel
        
        Args:
            parent_frame: Parent frame to add panel to
        """
        # Main panel frame
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="VS Code Integration",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Status section
        self._create_status_section()
        
        # Control section
        self._create_control_section()
        
        # Open files display
        self._create_files_section()
        
        # Manual instruction section
        self._create_instruction_section()
        
        # Start status updates
        self._schedule_status_update()
        
        return self.panel_frame
    
    def _create_status_section(self):
        """Create status display section"""
        status_frame = ttk.Frame(self.panel_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Status icon and text
        self.status_label = tk.Label(
            status_frame,
            text="⚫ Not Connected",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Info icon with tooltip
        info_label = tk.Label(
            status_frame,
            text="ℹ️",
            font=("Segoe UI", 10),
            foreground=DarkTheme.ACCENT_PURPLE,
            background=DarkTheme.BG_DARKER,
            cursor="hand2"
        )
        info_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        self._create_tooltip(
            info_label,
            "VS Code Extension Status:\n\n"
            "🟢 Connected: Extension responding\n"
            "⚫ Not Connected: Extension not running\n\n"
            "Requirements:\n"
            "- VS Code with Ollama Code Editor extension\n"
            "- Extension server on localhost:3000\n"
            "- Press F5 in VS Code to activate"
        )
    
    def _create_control_section(self):
        """Create control buttons section"""
        control_frame = ttk.Frame(self.panel_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Test connection button
        self.test_button = ttk.Button(
            control_frame,
            text="🔍 Test Connection",
            command=self._test_connection,
            width=20
        )
        self.test_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Refresh button
        refresh_button = ttk.Button(
            control_frame,
            text="🔄 Refresh Status",
            command=self._refresh_status,
            width=20
        )
        refresh_button.pack(side=tk.LEFT)
    
    def _create_files_section(self):
        """Create open files display section"""
        files_frame = ttk.Frame(self.panel_frame)
        files_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Label
        ttk.Label(
            files_frame,
            text="Open Files in VS Code:",
            style="TLabel"
        ).pack(anchor=tk.W, pady=(0, 3))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(files_frame, orient='vertical')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Files display
        self.open_files_display = tk.Text(
            files_frame,
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
        self.open_files_display.pack(fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.open_files_display.yview)
        
        # Configure tags
        self.open_files_display.tag_configure(
            "active",
            foreground=DarkTheme.ACCENT_GREEN,
            font=("Consolas", 9, "bold")
        )
        self.open_files_display.tag_configure(
            "inactive",
            foreground=DarkTheme.FG_MUTED
        )
    
    def _create_instruction_section(self):
        """Create manual instruction section"""
        instruction_frame = ttk.LabelFrame(
            self.panel_frame,
            text="Manual Edit Instruction",
            style="Dark.TLabelframe"
        )
        instruction_frame.pack(fill=tk.X, padx=5, pady=(5, 5))
        
        # Instruction label
        ttk.Label(
            instruction_frame,
            text="Coding Instruction:",
            style="TLabel"
        ).pack(anchor=tk.W, padx=5, pady=(5, 2))
        
        # Instruction entry
        self.instruction_entry = tk.Text(
            instruction_frame,
            height=3,
            wrap=tk.WORD,
            font=("Segoe UI", 9),
            bg=DarkTheme.BG_LIGHTER,
            fg=DarkTheme.FG_PRIMARY,
            insertbackground=DarkTheme.FG_PRIMARY,
            borderwidth=0,
            highlightthickness=0
        )
        self.instruction_entry.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Send button
        self.send_button = ttk.Button(
            instruction_frame,
            text="📤 Send to VS Code",
            command=self._send_instruction,
            width=20
        )
        self.send_button.pack(pady=(0, 5))
        
        # Example text
        example_label = tk.Label(
            instruction_frame,
            text="Example: 'Add error handling to the main function'",
            font=("Segoe UI", 8, "italic"),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER
        )
        example_label.pack(pady=(0, 5))
    
    def _test_connection(self):
        """Test VS Code extension connection"""
        self.coding_tool = self._get_coding_tool()
        
        if not self.coding_tool:
            self._show_error("Coding tool not initialized")
            return
        
        self.logger.tool("Testing VS Code extension connection...")
        self.test_button.config(state=tk.DISABLED)
        
        # Check availability
        if self.coding_tool.is_available():
            self.logger.success("✅ Connection test successful!")
            self._update_status_connected()
            self._update_open_files()
        else:
            self.logger.error("❌ Connection test failed - server not responding")
            self._update_status_disconnected()
        
        self.test_button.config(state=tk.NORMAL)
    
    def _send_instruction(self):
        """Send manual coding instruction to VS Code"""
        self.coding_tool = self._get_coding_tool()
        
        if not self.coding_tool:
            self._show_error("Coding tool not initialized")
            return
        
        if not self.instruction_entry:
            self._show_error("Instruction entry not available")
            return
        
        instruction = self.instruction_entry.get("1.0", tk.END).strip()
        
        if not instruction:
            self._show_error("Please enter an instruction")
            return
        
        if not self.coding_tool.is_available():
            self._show_error("VS Code not connected")
            return
        
        self.logger.tool(f"📤 Sending instruction: {instruction}")
        self.send_button.config(state=tk.DISABLED)
        
        # Execute edit command via AI Core event loop
        if self.ai_core.main_loop:
            import asyncio
            
            async def send_async():
                result = await self.coding_tool.execute('edit', [instruction])
                if result.get('success'):
                    self.logger.success(f"✅ {result.get('content', 'Instruction sent')}")
                    # Clear instruction entry
                    self.instruction_entry.delete("1.0", tk.END)
                else:
                    error = result.get('content', 'Unknown error')
                    self._show_error(f"Failed: {error}")
            
            asyncio.run_coroutine_threadsafe(send_async(), self.ai_core.main_loop)
        else:
            self._show_error("AI Core event loop not available")
        
        self.send_button.config(state=tk.NORMAL)
    
    def _refresh_status(self):
        """Refresh status display"""
        self._update_status()
    
    def _update_status(self):
        """Update status display based on tool state"""
        self.coding_tool = self._get_coding_tool()
        
        if not self.coding_tool:
            self._update_status_not_available()
            return
        
        if self.coding_tool.is_available():
            self._update_status_connected()
            self._update_open_files()
        else:
            self._update_status_disconnected()
    
    def _update_status_not_available(self):
        """Update UI for tool not available"""
        self.status_label.config(
            text="⚫ Tool Not Available",
            foreground=DarkTheme.FG_MUTED
        )
        self.test_button.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        
        # Clear files display
        self.open_files_display.config(state=tk.NORMAL)
        self.open_files_display.delete("1.0", tk.END)
        self.open_files_display.insert(tk.END, "Tool not available - enable USE_CODING in controls")
        self.open_files_display.config(state=tk.DISABLED)
    
    def _update_status_connected(self):
        """Update UI for connected state"""
        self.status_label.config(
            text="🟢 Connected to VS Code",
            foreground=DarkTheme.ACCENT_GREEN
        )
        self.test_button.config(state=tk.NORMAL)
        self.send_button.config(state=tk.NORMAL)
    
    def _update_status_disconnected(self):
        """Update UI for disconnected state"""
        self.status_label.config(
            text="⚫ VS Code Not Responding",
            foreground=DarkTheme.ACCENT_RED
        )
        self.test_button.config(state=tk.NORMAL)
        self.send_button.config(state=tk.DISABLED)
        
        # Clear files display
        self.open_files_display.config(state=tk.NORMAL)
        self.open_files_display.delete("1.0", tk.END)
        self.open_files_display.insert(
            tk.END,
            "VS Code extension not responding\n\n"
            "Troubleshooting:\n"
            "• Ensure VS Code is running\n"
            "• Press F5 in VS Code to activate extension\n"
            "• Check port 3000 is not blocked\n"
            "• Extension server: http://localhost:3000"
        )
        self.open_files_display.config(state=tk.DISABLED)
    
    def _update_open_files(self):
        """Update open files display"""
        if not self.coding_tool or not self.coding_tool.is_available():
            return
        
        try:
            # Get open files via internal method
            files_result = self.coding_tool._get_open_files()
            
            if not files_result.get('success'):
                return
            
            files = files_result.get('files', [])
            active_file = files_result.get('activeFile')
            
            # Update display
            self.open_files_display.config(state=tk.NORMAL)
            self.open_files_display.delete("1.0", tk.END)
            
            if not files:
                self.open_files_display.insert(tk.END, "No files open in VS Code")
            else:
                self.open_files_display.insert(tk.END, f"Open files ({len(files)}):\n\n")
                
                for i, file_info in enumerate(files, 1):
                    file_name = file_info.get('fileName', 'Unknown')
                    file_path = file_info.get('filePath', '')
                    is_active = file_path == active_file
                    
                    marker = "▶ " if is_active else "  "
                    line_text = f"{marker}{i}. {file_name}\n"
                    
                    tag = "active" if is_active else "inactive"
                    self.open_files_display.insert(tk.END, line_text, tag)
            
            self.open_files_display.config(state=tk.DISABLED)
        
        except Exception as e:
            self.logger.warning(f"Error updating open files: {e}")
    
    def _schedule_status_update(self):
        """Schedule periodic status updates"""
        if self.panel_frame and self.panel_frame.winfo_exists():
            self._update_status()
            # Schedule next update in 3 seconds
            self.update_job = self.panel_frame.after(3000, self._schedule_status_update)
    
    def _get_coding_tool(self):
        """Get coding tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'coding' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('coding')
    
    def _show_error(self, message: str):
        """Show error message"""
        self.status_label.config(
            text=f"❌ {message}",
            foreground=DarkTheme.ACCENT_RED
        )
        self.logger.error(f"[Coding] {message}")
    
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
        
        self.logger.tool("Coding component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        CodingToolComponent instance
    """
    return CodingToolComponent(parent_gui, ai_core, logger)
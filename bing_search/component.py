# Filename: BASE/tools/installed/bing_search/component.py
"""
Bing Search Tool - GUI Component
Dynamic GUI panel for Bing web search
"""
import tkinter as tk
from tkinter import ttk
from BASE.interface.gui_themes import DarkTheme


class BingSearchComponent:
    """
    GUI component for Bing Search tool
    Provides interface for web search queries
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        """
        Initialize Bing search component
        
        Args:
            parent_gui: Main GUI instance
            ai_core: AI Core instance
            logger: Logger instance
        """
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        
        # Tool instance
        self.bing_tool = None
        
        # GUI elements
        self.panel_frame = None
        self.status_label = None
        self.query_var = None
        self.results_display = None
        self.search_button = None
        self.clear_button = None
        
        # State
        self.last_query = ""
        self.search_history = []
    
    def create_panel(self, parent_frame):
        """
        Create the Bing search panel
        
        Args:
            parent_frame: Parent frame to add panel to
        """
        # Main panel frame
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="🔍 Bing Web Search",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Search section
        self._create_search_section()
        
        # Status section
        self._create_status_section()
        
        # Results display section
        self._create_results_section()
        
        # Update initial status
        self._update_status()
        
        return self.panel_frame
    
    def _create_search_section(self):
        """Create search input section"""
        search_frame = ttk.Frame(self.panel_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Query label
        ttk.Label(
            search_frame,
            text="Search Query:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Query entry
        self.query_var = tk.StringVar()
        query_entry = ttk.Entry(
            search_frame,
            textvariable=self.query_var,
            font=("Segoe UI", 10)
        )
        query_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Bind Enter key to search
        query_entry.bind('<Return>', lambda e: self._perform_search())
        
        # Search button
        self.search_button = ttk.Button(
            search_frame,
            text="🔍 Search",
            command=self._perform_search,
            width=12
        )
        self.search_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Clear button
        self.clear_button = ttk.Button(
            search_frame,
            text="🗑️ Clear",
            command=self._clear_results,
            width=10
        )
        self.clear_button.pack(side=tk.LEFT)
    
    def _create_status_section(self):
        """Create status display section"""
        status_frame = ttk.Frame(self.panel_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Status label
        self.status_label = tk.Label(
            status_frame,
            text="⚫ Checking availability...",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Info button
        info_button = tk.Label(
            status_frame,
            text="ℹ️",
            font=("Segoe UI", 10),
            foreground=DarkTheme.ACCENT_PURPLE,
            background=DarkTheme.BG_DARKER,
            cursor="hand2"
        )
        info_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Tooltip
        self._create_tooltip(
            info_button,
            "Bing Web Search:\n\n"
            "• Returns top 5 most relevant results\n"
            "• Best for current events and news\n"
            "• Use concise queries (1-6 words)\n"
            "• Requires API key in config.json\n\n"
            "Example queries:\n"
            "- 'Python latest features'\n"
            "- 'AI news today'\n"
            "- 'weather forecast'"
        )
    
    def _create_results_section(self):
        """Create results display section"""
        results_frame = ttk.Frame(self.panel_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Label
        ttk.Label(
            results_frame,
            text="Search Results:",
            style="TLabel"
        ).pack(anchor=tk.W, pady=(0, 3))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient='vertical')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Results display
        self.results_display = tk.Text(
            results_frame,
            height=15,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Segoe UI", 9),
            bg=DarkTheme.BG_DARK,
            fg=DarkTheme.FG_PRIMARY,
            insertbackground=DarkTheme.FG_PRIMARY,
            selectbackground=DarkTheme.ACCENT_PURPLE,
            selectforeground=DarkTheme.FG_PRIMARY,
            borderwidth=1,
            relief="solid",
            yscrollcommand=scrollbar.set
        )
        self.results_display.pack(fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.results_display.yview)
        
        # Configure text tags
        self.results_display.tag_configure(
            "title",
            foreground=DarkTheme.ACCENT_PURPLE,
            font=("Segoe UI", 10, "bold")
        )
        self.results_display.tag_configure(
            "snippet",
            foreground=DarkTheme.FG_PRIMARY
        )
        self.results_display.tag_configure(
            "url",
            foreground=DarkTheme.ACCENT_BLUE,
            font=("Segoe UI", 8)
        )
        self.results_display.tag_configure(
            "separator",
            foreground=DarkTheme.FG_MUTED
        )
    
    def _perform_search(self):
        """Perform Bing search"""
        query = self.query_var.get().strip()
        
        if not query:
            self._show_error("Please enter a search query")
            return
        
        # Get tool instance
        self.bing_tool = self._get_bing_tool()
        
        if not self.bing_tool:
            self._show_error("Bing tool not initialized")
            return
        
        if not self.bing_tool.is_available():
            self._show_error("Bing search unavailable - check API key configuration")
            return
        
        # Update status
        self.status_label.config(
            text="🔄 Searching...",
            foreground=DarkTheme.ACCENT_BLUE
        )
        self.search_button.config(state=tk.DISABLED)
        
        # Store query
        self.last_query = query
        if query not in self.search_history:
            self.search_history.append(query)
        
        # Perform search asynchronously
        if self.ai_core.main_loop:
            import asyncio
            
            async def search_async():
                try:
                    result = await self.bing_tool.execute('search', [query])
                    
                    # Update UI on main thread
                    self.panel_frame.after(0, lambda: self._handle_search_result(result))
                
                except Exception as e:
                    self.panel_frame.after(0, lambda: self._show_error(f"Search failed: {e}"))
                    self.logger.error(f"[Bing] Search error: {e}")
            
            asyncio.run_coroutine_threadsafe(search_async(), self.ai_core.main_loop)
        
        self.logger.tool(f"[Bing] Searching: {query}")
    
    def _handle_search_result(self, result: dict):
        """Handle search result"""
        self.search_button.config(state=tk.NORMAL)
        
        if result.get('success'):
            content = result.get('content', '')
            result_count = result.get('metadata', {}).get('result_count', 0)
            
            # Display results
            self._display_results(content)
            
            # Update status
            self.status_label.config(
                text=f"✅ Found {result_count} result(s)",
                foreground=DarkTheme.ACCENT_GREEN
            )
            
            self.logger.success(f"[Bing] Search completed: {result_count} results")
        
        else:
            error_msg = result.get('content', 'Search failed')
            self._show_error(error_msg)
            self.logger.warning(f"[Bing] Search failed: {error_msg}")
    
    def _display_results(self, results: str):
        """Display formatted search results"""
        self.results_display.config(state=tk.NORMAL)
        self.results_display.delete("1.0", tk.END)
        
        if not results:
            self.results_display.insert(tk.END, "No results found")
            self.results_display.config(state=tk.DISABLED)
            return
        
        # Parse and format results
        result_blocks = results.split('\n\n')
        
        for i, block in enumerate(result_blocks):
            if not block.strip():
                continue
            
            lines = block.split('\n')
            
            # First line is title (numbered)
            if lines:
                title_line = lines[0]
                # Remove number prefix if present
                if '. ' in title_line:
                    title = title_line.split('. ', 1)[1]
                else:
                    title = title_line
                
                self.results_display.insert(tk.END, f"{title}\n", "title")
            
            # Middle lines are snippet
            if len(lines) > 1:
                snippet = '\n'.join(lines[1:-1])
                self.results_display.insert(tk.END, f"{snippet}\n", "snippet")
            
            # Last line is URL
            if len(lines) > 1:
                url_line = lines[-1]
                if url_line.startswith('Source: '):
                    url = url_line.replace('Source: ', '')
                    self.results_display.insert(tk.END, f"🔗 {url}\n", "url")
            
            # Add separator between results
            if i < len(result_blocks) - 1:
                self.results_display.insert(tk.END, "\n" + "─" * 80 + "\n\n", "separator")
        
        self.results_display.config(state=tk.DISABLED)
        self.results_display.see("1.0")  # Scroll to top
    
    def _clear_results(self):
        """Clear results display"""
        self.results_display.config(state=tk.NORMAL)
        self.results_display.delete("1.0", tk.END)
        self.results_display.config(state=tk.DISABLED)
        
        self.query_var.set("")
        self._update_status()
        
        self.logger.tool("[Bing] Cleared results")
    
    def _update_status(self):
        """Update status display"""
        self.bing_tool = self._get_bing_tool()
        
        if not self.bing_tool:
            self.status_label.config(
                text="⚫ Tool Not Available",
                foreground=DarkTheme.FG_MUTED
            )
            self.search_button.config(state=tk.DISABLED)
            return
        
        if self.bing_tool.is_available():
            self.status_label.config(
                text="🟢 Ready - Enter query and press Search",
                foreground=DarkTheme.ACCENT_GREEN
            )
            self.search_button.config(state=tk.NORMAL)
        else:
            self.status_label.config(
                text="⚠️ No API Key - Configure in config.json",
                foreground=DarkTheme.ACCENT_ORANGE
            )
            self.search_button.config(state=tk.DISABLED)
    
    def _get_bing_tool(self):
        """Get Bing tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'bing' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('bing')
    
    def _show_error(self, message: str):
        """Show error message"""
        self.status_label.config(
            text=f"❌ {message}",
            foreground=DarkTheme.ACCENT_RED
        )
        self.search_button.config(state=tk.NORMAL)
    
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
                wraplength=350,
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
        self.logger.tool("[Bing] Component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        BingSearchComponent instance
    """
    return BingSearchComponent(parent_gui, ai_core, logger)
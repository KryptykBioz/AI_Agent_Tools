# Filename: BASE/tools/installed/wiki_search/component.py
"""
Wikipedia Search Tool - GUI Component
Dynamic GUI panel for Wikipedia encyclopedia search
"""
import tkinter as tk
from tkinter import ttk
from BASE.interface.gui_themes import DarkTheme


class WikiSearchComponent:
    """
    GUI component for Wikipedia Search tool
    Provides interface for encyclopedic information lookup
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        """
        Initialize Wikipedia search component
        
        Args:
            parent_gui: Main GUI instance
            ai_core: AI Core instance
            logger: Logger instance
        """
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        
        # Tool instance
        self.wiki_tool = None
        
        # GUI elements
        self.panel_frame = None
        self.status_label = None
        self.query_var = None
        self.max_results_var = None
        self.results_display = None
        self.search_button = None
        self.clear_button = None
        self.position_label = None
        
        # State
        self.last_query = ""
        self.search_count = 0
        self.current_article = None
    
    def create_panel(self, parent_frame):
        """
        Create the Wikipedia search panel
        
        Args:
            parent_frame: Parent frame to add panel to
        """
        # Main panel frame
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="📚 Wikipedia Search",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Search section
        self._create_search_section()
        
        # Options section
        self._create_options_section()
        
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
            text="Search Topic:",
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
    
    def _create_options_section(self):
        """Create search options section"""
        options_frame = ttk.Frame(self.panel_frame)
        options_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Max results label
        ttk.Label(
            options_frame,
            text="Max Results:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Max results spinbox
        self.max_results_var = tk.IntVar(value=5)
        max_results_spin = ttk.Spinbox(
            options_frame,
            from_=1,
            to=10,
            textvariable=self.max_results_var,
            width=5,
            font=("Segoe UI", 9)
        )
        max_results_spin.pack(side=tk.LEFT, padx=(0, 10))
        
        # Position tracking info
        self.position_label = tk.Label(
            options_frame,
            text="📍 Position tracking: Varied results on repeat searches",
            font=("Segoe UI", 8, "italic"),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER
        )
        self.position_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _create_status_section(self):
        """Create status display section"""
        status_frame = ttk.Frame(self.panel_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Status label
        self.status_label = tk.Label(
            status_frame,
            text="🟢 Ready - Wikipedia is always available",
            font=("Segoe UI", 9),
            foreground=DarkTheme.ACCENT_GREEN,
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
            "Wikipedia Search Features:\n\n"
            "• Returns 500-character chunks from articles\n"
            "• Position tracking for varied results\n"
            "• Repeat searches show different sections\n"
            "• Best for factual, encyclopedic info\n"
            "• No API key required\n\n"
            "Example topics:\n"
            "- 'Quantum Computing'\n"
            "- 'Ancient Rome'\n"
            "- 'Marie Curie'\n"
            "- 'Machine Learning'\n\n"
            "Tip: Use 1-3 word queries for best results"
        )
    
    def _create_results_section(self):
        """Create results display section"""
        results_frame = ttk.Frame(self.panel_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Label
        ttk.Label(
            results_frame,
            text="Article Content:",
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
            font=("Segoe UI", 11, "bold")
        )
        self.results_display.tag_configure(
            "url",
            foreground=DarkTheme.ACCENT_BLUE,
            font=("Segoe UI", 8)
        )
        self.results_display.tag_configure(
            "header",
            foreground=DarkTheme.ACCENT_GREEN,
            font=("Segoe UI", 9, "bold")
        )
        self.results_display.tag_configure(
            "chunk_number",
            foreground=DarkTheme.ACCENT_ORANGE,
            font=("Segoe UI", 9, "bold")
        )
        self.results_display.tag_configure(
            "content",
            foreground=DarkTheme.FG_PRIMARY
        )
        self.results_display.tag_configure(
            "separator",
            foreground=DarkTheme.FG_MUTED
        )
    
    def _perform_search(self):
        """Perform Wikipedia search"""
        query = self.query_var.get().strip()
        
        if not query:
            self._show_error("Please enter a search topic")
            return
        
        # Get tool instance
        self.wiki_tool = self._get_wiki_tool()
        
        if not self.wiki_tool:
            self._show_error("Wikipedia tool not initialized")
            return
        
        # Get max results
        max_results = self.max_results_var.get()
        
        # Update status
        self.status_label.config(
            text="🔄 Searching Wikipedia...",
            foreground=DarkTheme.ACCENT_BLUE
        )
        self.search_button.config(state=tk.DISABLED)
        
        # Track repeat searches on same topic
        if query.lower() == self.last_query.lower():
            self.search_count += 1
        else:
            self.search_count = 1
            self.last_query = query
        
        # Perform search asynchronously
        if self.ai_core.main_loop:
            import asyncio
            
            async def search_async():
                try:
                    result = await self.wiki_tool.execute('search', [query, max_results])
                    
                    # Update UI on main thread
                    self.panel_frame.after(0, lambda: self._handle_search_result(result))
                
                except Exception as e:
                    self.panel_frame.after(0, lambda: self._show_error(f"Search failed: {e}"))
                    self.logger.error(f"[Wiki] Search error: {e}")
            
            asyncio.run_coroutine_threadsafe(search_async(), self.ai_core.main_loop)
        
        self.logger.tool(f"[Wiki] Searching: {query}")
    
    def _handle_search_result(self, result: dict):
        """Handle search result"""
        self.search_button.config(state=tk.NORMAL)
        
        if result.get('success'):
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            article = metadata.get('article', 'Unknown')
            chunks = metadata.get('chunks', 0)
            position = metadata.get('position', 0)
            
            # Store current article
            self.current_article = article
            
            # Display results
            self._display_results(content, metadata)
            
            # Update status with position info
            if self.search_count > 1:
                status_text = f"✅ Found {chunks} chunk(s) - Search #{self.search_count} (different section)"
            else:
                status_text = f"✅ Found {chunks} chunk(s) from '{article}'"
            
            self.status_label.config(
                text=status_text,
                foreground=DarkTheme.ACCENT_GREEN
            )
            
            # Update position label
            self.position_label.config(
                text=f"📍 Article position #{position} • Search again for different content",
                foreground=DarkTheme.ACCENT_PURPLE
            )
            
            self.logger.success(f"[Wiki] Retrieved {chunks} chunks (position #{position})")
        
        else:
            error_msg = result.get('content', 'Search failed')
            self._show_error(error_msg)
            self.logger.warning(f"[Wiki] Search failed: {error_msg}")
    
    def _display_results(self, results: str, metadata: dict):
        """Display formatted search results"""
        self.results_display.config(state=tk.NORMAL)
        self.results_display.delete("1.0", tk.END)
        
        if not results:
            self.results_display.insert(tk.END, "No results found")
            self.results_display.config(state=tk.DISABLED)
            return
        
        # Parse results
        lines = results.split('\n')
        
        # Extract title and URL
        title = ""
        url = ""
        content_started = False
        
        for i, line in enumerate(lines):
            if line.startswith('**') and line.endswith('** (Wikipedia)'):
                # Extract title
                title = line.replace('**', '').replace(' (Wikipedia)', '')
                self.results_display.insert(tk.END, f"{title}\n", "title")
                self.results_display.insert(tk.END, "Wikipedia Article\n\n", "header")
            
            elif line.startswith('URL: '):
                url = line.replace('URL: ', '')
                self.results_display.insert(tk.END, f"🔗 {url}\n", "url")
                self.results_display.insert(tk.END, "\n" + "─" * 80 + "\n\n", "separator")
            
            elif line.startswith('Content:'):
                content_started = True
                self.results_display.insert(tk.END, "Content Excerpts:\n\n", "header")
            
            elif content_started and line.strip():
                # Parse chunks: [1] content, [2] content, etc.
                if line.startswith('[') and ']' in line:
                    # Split chunk number and content
                    bracket_end = line.index(']')
                    chunk_num = line[:bracket_end + 1]
                    content = line[bracket_end + 1:].strip()
                    
                    self.results_display.insert(tk.END, f"\n{chunk_num} ", "chunk_number")
                    self.results_display.insert(tk.END, f"{content}\n", "content")
                else:
                    # Continuation of previous chunk
                    self.results_display.insert(tk.END, f"{line}\n", "content")
        
        self.results_display.config(state=tk.DISABLED)
        self.results_display.see("1.0")  # Scroll to top
    
    def _clear_results(self):
        """Clear results display"""
        self.results_display.config(state=tk.NORMAL)
        self.results_display.delete("1.0", tk.END)
        self.results_display.config(state=tk.DISABLED)
        
        self.query_var.set("")
        self.last_query = ""
        self.search_count = 0
        self.current_article = None
        
        self.position_label.config(
            text="📍 Position tracking: Varied results on repeat searches",
            foreground=DarkTheme.FG_MUTED
        )
        
        self._update_status()
        
        self.logger.tool("[Wiki] Cleared results")
    
    def _update_status(self):
        """Update status display"""
        self.wiki_tool = self._get_wiki_tool()
        
        if not self.wiki_tool:
            self.status_label.config(
                text="⚫ Tool Not Available",
                foreground=DarkTheme.FG_MUTED
            )
            self.search_button.config(state=tk.DISABLED)
            return
        
        # Wikipedia is always available (no API key needed)
        self.status_label.config(
            text="🟢 Ready - Wikipedia is always available",
            foreground=DarkTheme.ACCENT_GREEN
        )
        self.search_button.config(state=tk.NORMAL)
    
    def _get_wiki_tool(self):
        """Get Wikipedia tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'wiki_search' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('wiki_search')
    
    def _show_error(self, message: str):
        """Show error message"""
        self.status_label.config(
            text=f"❌ {message}",
            foreground=DarkTheme.ACCENT_RED
        )
        self.search_button.config(state=tk.NORMAL)
        
        self.position_label.config(
            text="📍 Position tracking: Varied results on repeat searches",
            foreground=DarkTheme.FG_MUTED
        )
    
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
        self.logger.tool("[Wiki] Component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        WikiSearchComponent instance
    """
    return WikiSearchComponent(parent_gui, ai_core, logger)
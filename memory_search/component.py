# Filename: BASE/tools/installed/memory_search/component.py
"""
Memory Search Tool - GUI Component
Dynamic GUI panel for searching internal memory
"""
import tkinter as tk
from tkinter import ttk
from BASE.interface.gui_themes import DarkTheme


class MemorySearchComponent:
    """
    GUI component for Memory Search tool
    Provides interface for searching internal memory tiers
    All searches return exactly 5 results
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        """
        Initialize memory search component
        
        Args:
            parent_gui: Main GUI instance
            ai_core: AI Core instance
            logger: Logger instance
        """
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        
        # Tool instance
        self.memory_tool = None
        
        # GUI elements
        self.panel_frame = None
        self.status_label = None
        self.query_var = None
        self.tier_var = None
        self.date_var = None  # Changed from max_results_var
        self.results_display = None
        self.search_button = None
        self.clear_button = None
        # Removed yesterday_button
        self.stats_label = None
        
        # State
        self.last_query = ""
        self.search_count = 0
    
    def create_panel(self, parent_frame):
        """
        Create the memory search panel
        
        Args:
            parent_frame: Parent frame to add panel to
        """
        # Main panel frame
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="🧠 Memory Search",
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
            text="Search Memory:",
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
        
        # Clear button (yesterday button removed)
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
        
        # Tier selection
        ttk.Label(
            options_frame,
            text="Memory Tier:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.tier_var = tk.StringVar(value="all")
        tier_combo = ttk.Combobox(
            options_frame,
            textvariable=self.tier_var,
            values=["all", "short", "medium", "long", "base"],
            state="readonly",
            width=10,
            font=("Segoe UI", 9)
        )
        tier_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Date filter (replaced max results spinner)
        ttk.Label(
            options_frame,
            text="Date Filter:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.date_var = tk.StringVar(value="")
        date_entry = ttk.Entry(
            options_frame,
            textvariable=self.date_var,
            width=12,
            font=("Segoe UI", 9)
        )
        date_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Info about usage
        info_label = tk.Label(
            options_frame,
            text="💡 Tip: Use specific terms like 'minecraft' or 'favorite game' • Date: YYYY-MM-DD (optional)",
            font=("Segoe UI", 8, "italic"),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER
        )
        info_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _create_status_section(self):
        """Create status display section"""
        status_frame = ttk.Frame(self.panel_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Status label
        self.status_label = tk.Label(
            status_frame,
            text="⚫ Initializing...",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_MUTED,
            background=DarkTheme.BG_DARKER,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Stats label
        self.stats_label = tk.Label(
            status_frame,
            text="",
            font=("Segoe UI", 8),
            foreground=DarkTheme.ACCENT_BLUE,
            background=DarkTheme.BG_DARKER,
            anchor=tk.E
        )
        self.stats_label.pack(side=tk.RIGHT, padx=(5, 0))
        
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
            "Memory Search Features:\n\n"
            "Memory Tiers:\n"
            "• Short: Recent conversation (last ~10 messages)\n"
            "• Medium: Earlier today (embedded, searchable)\n"
            "• Long: Past days (daily summaries)\n"
            "• Base: Personality & reference documents\n"
            "• All: Search all tiers automatically\n\n"
            "Search Tips:\n"
            "• Use specific terms: 'minecraft', 'favorite game'\n"
            "• Avoid general terms: 'gaming topics', 'anime discussions'\n"
            "• All searches return exactly 5 results\n"
            "• Date filter: YYYY-MM-DD (optional, for medium/long)\n\n"
            "Examples:\n"
            "• Query: 'VTubers' → searches all tiers\n"
            "• Query: 'minecraft', Date: '2025-12-20' → searches that date\n"
            "• Query: 'humor style', Tier: 'base' → personality search"
        )
    
    def _create_results_section(self):
        """Create results display section"""
        results_frame = ttk.Frame(self.panel_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Text display
        self.results_display = tk.Text(
            results_frame,
            wrap=tk.WORD,
            height=20,
            font=("Consolas", 9),
            background=DarkTheme.BG_DARK,
            foreground=DarkTheme.FG_PRIMARY,
            insertbackground=DarkTheme.ACCENT_BLUE,
            selectbackground=DarkTheme.ACCENT_PURPLE,
            yscrollcommand=scrollbar.set,
            state=tk.DISABLED
        )
        self.results_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.results_display.yview)
        
        # Configure text tags for formatting
        self.results_display.tag_config(
            "section_header",
            font=("Segoe UI", 11, "bold"),
            foreground=DarkTheme.ACCENT_BLUE
        )
        self.results_display.tag_config(
            "separator",
            foreground=DarkTheme.FG_MUTED
        )
        self.results_display.tag_config(
            "role",
            font=("Segoe UI", 9, "bold"),
            foreground=DarkTheme.ACCENT_GREEN
        )
        self.results_display.tag_config(
            "timestamp",
            font=("Consolas", 8),
            foreground=DarkTheme.FG_MUTED
        )
        self.results_display.tag_config(
            "content",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_PRIMARY
        )
        self.results_display.tag_config(
            "relevance",
            font=("Consolas", 8, "italic"),
            foreground=DarkTheme.ACCENT_ORANGE
        )
    
    def _perform_search(self):
        """Perform memory search"""
        query = self.query_var.get().strip()
        
        if not query:
            self.logger.warning("[Memory] No search query provided")
            return
        
        tier = self.tier_var.get()
        date_filter = self.date_var.get().strip()  # Changed from max_results
        
        # Disable buttons during search
        self.search_button.config(state=tk.DISABLED)
        
        # Update status
        search_desc = f"'{query}' in {tier} memory"
        if date_filter:
            search_desc += f" (date: {date_filter})"
        
        self.status_label.config(
            text=f"🔄 Searching {search_desc}...",
            foreground=DarkTheme.ACCENT_BLUE
        )
        
        # Get tool instance
        self.memory_tool = self._get_memory_tool()
        
        if not self.memory_tool or not self.memory_tool.is_available():
            self._show_error("Memory search tool not available")
            self.search_button.config(state=tk.NORMAL)
            return
        
        # Prepare args based on tier
        # Args: [query, date] for search/medium/long, [query] for short/base
        if tier == 'all':
            command = 'search'
            args = [query, date_filter] if date_filter else [query]
        elif tier == 'short':
            command = 'search_short'
            args = [query]  # No date filter for short
        elif tier == 'medium':
            command = 'search_medium'
            args = [query, date_filter] if date_filter else [query]
        elif tier == 'long':
            command = 'search_long'
            args = [query, date_filter] if date_filter else [query]
        elif tier == 'base':
            command = 'search_base'
            args = [query]  # No date filter for base
        else:
            command = 'search'
            args = [query, date_filter] if date_filter else [query]
        
        # Execute search asynchronously
        import asyncio
        
        async def search_async():
            result = await self.memory_tool.execute(command, args)
            # Handle result on main thread
            self.parent_gui.root.after(0, lambda: self._handle_search_result(result))
        
        if hasattr(self.ai_core, 'main_loop'):
            asyncio.run_coroutine_threadsafe(search_async(), self.ai_core.main_loop)
        
        self.last_query = query
        self.search_count += 1
        
        self.logger.tool(f"[Memory] Searching: {search_desc}")
    
    def _handle_search_result(self, result: dict):
        """Handle search result"""
        self.search_button.config(state=tk.NORMAL)
        
        if result.get('success'):
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            
            # Display results
            self._display_results(content, metadata)
            
            # Update status
            tier = metadata.get('tier', 'unknown')
            date_filter = metadata.get('date_filter')
            
            if 'tiers_searched' in metadata:
                status_text = f"✅ Found results in {metadata['tiers_searched']} tier(s)"
            elif 'results' in metadata:
                status_text = f"✅ Found {metadata['results']} result(s) in {tier} memory"
            else:
                status_text = f"✅ Retrieved {tier} memory"
            
            if date_filter:
                status_text += f" (date: {date_filter})"
            
            self.status_label.config(
                text=status_text,
                foreground=DarkTheme.ACCENT_GREEN
            )
            
            self.logger.success(f"[Memory] {status_text}")
        
        else:
            error_msg = result.get('content', 'Search failed')
            self._show_error(error_msg)
            self.logger.warning(f"[Memory] Search failed: {error_msg}")
    
    def _display_results(self, results: str, metadata: dict):
        """Display formatted search results"""
        self.results_display.config(state=tk.NORMAL)
        self.results_display.delete("1.0", tk.END)
        
        if not results:
            self.results_display.insert(tk.END, "No results found")
            self.results_display.config(state=tk.DISABLED)
            return
        
        # Add metadata header
        query = metadata.get('query', 'N/A')
        date_filter = metadata.get('date_filter')
        
        header = f"Search Query: '{query}'\n"
        if date_filter:
            header += f"Date Filter: {date_filter}\n"
        header += f"Results: Top 5 most relevant matches\n\n"
        
        self.results_display.insert(tk.END, header, "timestamp")
        self.results_display.insert(tk.END, "─" * 80 + "\n\n", "separator")
        
        # Parse and format results
        lines = results.split('\n')
        
        for line in lines:
            if not line.strip():
                self.results_display.insert(tk.END, "\n")
                continue
            
            # Section headers (## Header)
            if line.startswith('##'):
                header = line.replace('##', '').strip()
                self.results_display.insert(tk.END, f"\n{header}\n", "section_header")
                self.results_display.insert(tk.END, "─" * 80 + "\n\n", "separator")
            
            # Bold headers (**Header**)
            elif line.startswith('**') and line.endswith('**'):
                header = line.replace('**', '').strip()
                self.results_display.insert(tk.END, f"{header}\n", "role")
            
            # Timestamps [timestamp]
            elif line.startswith('[') and ']' in line:
                bracket_end = line.index(']')
                timestamp = line[:bracket_end + 1]
                rest = line[bracket_end + 1:].strip()
                
                self.results_display.insert(tk.END, timestamp + " ", "timestamp")
                
                # Parse role and content
                if ':' in rest:
                    role, content = rest.split(':', 1)
                    self.results_display.insert(tk.END, role + ": ", "role")
                    self.results_display.insert(tk.END, content.strip() + "\n", "content")
                else:
                    self.results_display.insert(tk.END, rest + "\n", "content")
            
            # Relevance scores (relevance: 0.85)
            elif line.strip().startswith('(relevance:'):
                self.results_display.insert(tk.END, f"  {line.strip()}\n", "relevance")
            
            # Regular content
            else:
                self.results_display.insert(tk.END, line + "\n", "content")
        
        self.results_display.config(state=tk.DISABLED)
        self.results_display.see("1.0")  # Scroll to top
    
    def _clear_results(self):
        """Clear results display"""
        self.results_display.config(state=tk.NORMAL)
        self.results_display.delete("1.0", tk.END)
        self.results_display.config(state=tk.DISABLED)
        
        self.query_var.set("")
        self.date_var.set("")  # Clear date filter
        self.last_query = ""
        self.search_count = 0
        
        self._update_status()
        
        self.logger.tool("[Memory] Cleared results")
    
    def _update_status(self):
        """Update status display"""
        self.memory_tool = self._get_memory_tool()
        
        if not self.memory_tool or not self.memory_tool.is_available():
            self.status_label.config(
                text="⚫ Tool Not Available",
                foreground=DarkTheme.FG_MUTED
            )
            self.search_button.config(state=tk.DISABLED)
            self.stats_label.config(text="")
            return
        
        # Get memory stats
        try:
            if hasattr(self.ai_core, 'memory_manager'):
                stats = self.ai_core.memory_manager.get_stats()
                
                total_entries = (
                    stats['short_memory_entries'] + 
                    stats['medium_memory_entries']
                )
                
                self.status_label.config(
                    text="🟢 Ready - Memory system online (returns 5 results per search)",
                    foreground=DarkTheme.ACCENT_GREEN
                )
                
                self.stats_label.config(
                    text=f"📊 {total_entries} entries | {stats['long_memory_summaries']} summaries | "
                         f"{stats['base_knowledge_chunks']} base chunks"
                )
                
                self.search_button.config(state=tk.NORMAL)
            else:
                self.status_label.config(
                    text="⚠️ Memory manager not found",
                    foreground=DarkTheme.ACCENT_ORANGE
                )
                self.stats_label.config(text="")
        except Exception as e:
            self.logger.warning(f"[Memory] Status update error: {e}")
            self.status_label.config(
                text="⚠️ Status unavailable",
                foreground=DarkTheme.ACCENT_ORANGE
            )
            self.stats_label.config(text="")
    
    def _get_memory_tool(self):
        """Get memory search tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'memory_search' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('memory_search')
    
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
                wraplength=400,
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
        self.logger.tool("[Memory] Component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        MemorySearchComponent instance
    """
    return MemorySearchComponent(parent_gui, ai_core, logger)
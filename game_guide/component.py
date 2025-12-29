# Filename: BASE/tools/installed/game_guide/component.py
"""
Game Guide Tool - GUI Component
Dynamic GUI panel for searching game guides
"""
import tkinter as tk
from tkinter import ttk
from BASE.interface.gui_themes import DarkTheme


class GameGuideComponent:
    """
    GUI component for Game Guide tool
    Provides interface for searching embedded game guides
    All searches return exactly 5 results
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        """
        Initialize game guide component
        
        Args:
            parent_gui: Main GUI instance
            ai_core: AI Core instance
            logger: Logger instance
        """
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        
        # Tool instance
        self.guide_tool = None
        
        # GUI elements
        self.panel_frame = None
        self.status_label = None
        self.query_var = None
        self.game_filter_var = None
        self.results_display = None
        self.search_button = None
        self.list_games_button = None
        self.clear_button = None
        self.stats_label = None
        
        # State
        self.last_query = ""
        self.search_count = 0
        self.available_games = []
    
    def create_panel(self, parent_frame):
        """
        Create the game guide panel
        
        Args:
            parent_frame: Parent frame to add panel to
        """
        # Main panel frame
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="🎮 Game Guide Search",
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
            text="Search Guides:",
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
        
        # List games button
        self.list_games_button = ttk.Button(
            search_frame,
            text="📋 List Games",
            command=self._list_games,
            width=12
        )
        self.list_games_button.pack(side=tk.LEFT, padx=(0, 5))
        
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
        
        # Game filter
        ttk.Label(
            options_frame,
            text="Filter by Game:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.game_filter_var = tk.StringVar(value="all")
        game_combo = ttk.Combobox(
            options_frame,
            textvariable=self.game_filter_var,
            values=["all"],  # Will be updated when games load
            state="readonly",
            width=15,
            font=("Segoe UI", 9)
        )
        game_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Info about usage
        info_label = tk.Label(
            options_frame,
            text="💡 Tip: Search for gameplay mechanics like 'crafting', 'boss fight', or 'building' • Returns top 5 results",
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
            "Game Guide Features:\n\n"
            "Search Commands:\n"
            "• General search: Search all guides\n"
            "• Filter by game: Narrow results to specific game\n"
            "• List games: See all available guides\n"
            "• All searches return exactly 5 results\n\n"
            "Search Tips:\n"
            "• Use specific gameplay terms: 'crafting', 'enchanting', 'farming'\n"
            "• Search strategies: 'boss fight', 'speedrun', 'early game'\n"
            "• Filter by game for more precise results\n\n"
            "Examples:\n"
            "• Query: 'crafting recipes' → searches all guides\n"
            "• Query: 'enchanting', Game: 'minecraft' → precise results\n"
            "• Query: 'boss strategies', Game: 'elden ring' → targeted search\n\n"
            "Adding Guides:\n"
            "1. Add .md files to personality/base_memory/game_guides/\n"
            "2. Run: python BASE/memory/embed_document.py --game-guides\n"
            "3. Restart AI to load new guides"
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
            font=("Segoe UI", 12, "bold"),
            foreground=DarkTheme.ACCENT_BLUE,
            spacing3=5  # Space after
        )
        self.results_display.tag_config(
            "separator",
            foreground=DarkTheme.FG_MUTED
        )
        self.results_display.tag_config(
            "game_name",
            font=("Segoe UI", 10, "bold"),
            foreground=DarkTheme.ACCENT_GREEN,
            spacing1=3  # Space before
        )
        self.results_display.tag_config(
            "source",
            font=("Consolas", 8),
            foreground=DarkTheme.FG_MUTED,
            spacing3=3  # Space after
        )
        self.results_display.tag_config(
            "content",
            font=("Segoe UI", 9),
            foreground=DarkTheme.FG_PRIMARY,
            spacing1=2,  # Space before
            lmargin1=10,  # Left margin for readability
            lmargin2=10   # Left margin for wrapped lines
        )
        self.results_display.tag_config(
            "relevance",
            font=("Consolas", 8, "italic"),
            foreground=DarkTheme.ACCENT_ORANGE,
            spacing3=8  # Extra space after for separation
        )
    
    def _perform_search(self):
        """Perform game guide search"""
        query = self.query_var.get().strip()
        
        if not query:
            self.logger.warning("[GameGuide] No search query provided")
            return
        
        game_filter = self.game_filter_var.get()
        
        # Disable buttons during search
        self.search_button.config(state=tk.DISABLED)
        self.list_games_button.config(state=tk.DISABLED)
        
        # Update status
        search_desc = f"'{query}'"
        if game_filter != "all":
            search_desc += f" in {game_filter}"
        
        self.status_label.config(
            text=f"🔄 Searching {search_desc}...",
            foreground=DarkTheme.ACCENT_BLUE
        )
        
        # Get tool instance
        self.guide_tool = self._get_guide_tool()
        
        if not self.guide_tool or not self.guide_tool.is_available():
            self._show_error("Game guide tool not available")
            self.search_button.config(state=tk.NORMAL)
            self.list_games_button.config(state=tk.NORMAL)
            return
        
        # Prepare args
        if game_filter == "all":
            command = 'search'
            args = [query]
        else:
            command = 'search_game'
            args = [game_filter, query]
        
        # Execute search asynchronously
        import asyncio
        
        async def search_async():
            result = await self.guide_tool.execute(command, args)
            # Handle result on main thread
            self.parent_gui.root.after(0, lambda: self._handle_search_result(result))
        
        if hasattr(self.ai_core, 'main_loop'):
            asyncio.run_coroutine_threadsafe(search_async(), self.ai_core.main_loop)
        
        self.last_query = query
        self.search_count += 1
        
        self.logger.tool(f"[GameGuide] Searching: {search_desc}")
    
    def _handle_search_result(self, result: dict):
        """Handle search result"""
        self.search_button.config(state=tk.NORMAL)
        self.list_games_button.config(state=tk.NORMAL)
        
        if result.get('success'):
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            
            # Display results
            self._display_results(content, metadata)
            
            # Update status
            results_count = metadata.get('results', 0)
            game_filter = metadata.get('game_filter') or metadata.get('game')
            
            if game_filter:
                status_text = f"✅ Found {results_count} result(s) in {game_filter}"
            else:
                status_text = f"✅ Found {results_count} result(s)"
            
            self.status_label.config(
                text=status_text,
                foreground=DarkTheme.ACCENT_GREEN
            )
            
            self.logger.success(f"[GameGuide] {status_text}")
        
        else:
            error_msg = result.get('content', 'Search failed')
            self._show_error(error_msg)
            self.logger.warning(f"[GameGuide] Search failed: {error_msg}")
    
    def _list_games(self):
        """List all available game guides"""
        # Disable buttons during operation
        self.search_button.config(state=tk.DISABLED)
        self.list_games_button.config(state=tk.DISABLED)
        
        self.status_label.config(
            text="🔄 Loading game list...",
            foreground=DarkTheme.ACCENT_BLUE
        )
        
        # Get tool instance
        self.guide_tool = self._get_guide_tool()
        
        if not self.guide_tool or not self.guide_tool.is_available():
            self._show_error("Game guide tool not available")
            self.search_button.config(state=tk.NORMAL)
            self.list_games_button.config(state=tk.NORMAL)
            return
        
        # Execute list_games asynchronously
        import asyncio
        
        async def list_async():
            result = await self.guide_tool.execute('list_games', [])
            # Handle result on main thread
            self.parent_gui.root.after(0, lambda: self._handle_list_result(result))
        
        if hasattr(self.ai_core, 'main_loop'):
            asyncio.run_coroutine_threadsafe(list_async(), self.ai_core.main_loop)
        
        self.logger.tool("[GameGuide] Listing available games")
    
    def _handle_list_result(self, result: dict):
        """Handle list games result"""
        self.search_button.config(state=tk.NORMAL)
        self.list_games_button.config(state=tk.NORMAL)
        
        if result.get('success'):
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            
            # Update available games for dropdown
            games = metadata.get('games', [])
            if games:
                self.available_games = games
                
                # Update combo box
                current_filter = self.game_filter_var.get()
                game_values = ["all"] + [g for g in games]
                
                # Find the combo box widget and update it
                for widget in self.panel_frame.winfo_children():
                    if isinstance(widget, ttk.Frame):
                        for child in widget.winfo_children():
                            if isinstance(child, ttk.Combobox):
                                child.config(values=game_values)
                                if current_filter not in game_values:
                                    self.game_filter_var.set("all")
                                break
            
            # Display results
            self._display_results(content, metadata)
            
            # Update status
            game_count = metadata.get('total_games', len(games))
            status_text = f"✅ Found {game_count} game guide(s)"
            
            self.status_label.config(
                text=status_text,
                foreground=DarkTheme.ACCENT_GREEN
            )
            
            self.logger.success(f"[GameGuide] {status_text}")
        
        else:
            error_msg = result.get('content', 'List operation failed')
            self._show_error(error_msg)
            self.logger.warning(f"[GameGuide] List failed: {error_msg}")
    
    def _display_results(self, results: str, metadata: dict):
        """Display formatted search results"""
        self.results_display.config(state=tk.NORMAL)
        self.results_display.delete("1.0", tk.END)
        
        if not results:
            self.results_display.insert(tk.END, "No results found")
            self.results_display.config(state=tk.DISABLED)
            return
        
        # Add metadata header if search query
        if 'query' in metadata:
            query = metadata.get('query', 'N/A')
            game_filter = metadata.get('game_filter') or metadata.get('game')
            
            header = f"Search Query: '{query}'\n"
            if game_filter:
                header += f"Game Filter: {game_filter}\n"
            header += "Results: Top 5 most relevant matches\n\n"
            
            self.results_display.insert(tk.END, header, "source")
            self.results_display.insert(tk.END, "─" * 80 + "\n\n", "separator")
        
        # Parse and format results
        lines = results.split('\n')
        
        in_content_block = False
        
        for line in lines:
            if not line.strip():
                self.results_display.insert(tk.END, "\n")
                continue
            
            # Section headers (## Header)
            if line.startswith('##'):
                in_content_block = False
                header = line.replace('##', '').strip()
                self.results_display.insert(tk.END, f"\n{header}\n", "section_header")
                self.results_display.insert(tk.END, "─" * 80 + "\n\n", "separator")
            
            # Result headers [Result N]
            elif line.startswith('**[Result') and '**' in line:
                in_content_block = False
                # Clean the bold markers and display
                header = line.replace('**', '').strip()
                self.results_display.insert(tk.END, f"\n{header}\n", "game_name")
            
            # Source lines
            elif line.startswith('Source:'):
                in_content_block = False
                self.results_display.insert(tk.END, f"  {line}\n", "source")
            
            # Relevance scores (relevance: 0.85)
            elif line.strip().startswith('(relevance:'):
                in_content_block = False
                self.results_display.insert(tk.END, f"  {line.strip()}\n\n", "relevance")
            
            # Numbered lists (for game list)
            elif line.strip() and line.strip()[0].isdigit() and '.' in line[:5]:
                in_content_block = False
                self.results_display.insert(tk.END, line + "\n", "game_name")
            
            # List items (• or →)
            elif line.strip().startswith(('• ', '→ ')):
                in_content_block = True
                self.results_display.insert(tk.END, f"  {line}\n", "content")
            
            # Regular content (with better spacing)
            else:
                in_content_block = True
                # Add proper indentation for content blocks
                if line.strip():
                    self.results_display.insert(tk.END, f"{line}\n", "content")
        
        self.results_display.config(state=tk.DISABLED)
        self.results_display.see("1.0")  # Scroll to top
    
    def _clear_results(self):
        """Clear results display"""
        self.results_display.config(state=tk.NORMAL)
        self.results_display.delete("1.0", tk.END)
        self.results_display.config(state=tk.DISABLED)
        
        self.query_var.set("")
        self.game_filter_var.set("all")
        self.last_query = ""
        self.search_count = 0
        
        self._update_status()
        
        self.logger.tool("[GameGuide] Cleared results")
    
    def _update_status(self):
        """Update status display"""
        self.guide_tool = self._get_guide_tool()
        
        if not self.guide_tool or not self.guide_tool.is_available():
            self.status_label.config(
                text="⚫ Tool Not Available - Add game guides and embed them",
                foreground=DarkTheme.FG_MUTED
            )
            self.search_button.config(state=tk.DISABLED)
            self.list_games_button.config(state=tk.DISABLED)
            self.stats_label.config(text="")
            return
        
        # Get tool stats
        try:
            if hasattr(self.guide_tool, 'games_index'):
                game_count = len(self.guide_tool.games_index)
                chunk_count = len(self.guide_tool.game_guides)
                
                self.status_label.config(
                    text="🟢 Ready - Game guides loaded (returns 5 results per search)",
                    foreground=DarkTheme.ACCENT_GREEN
                )
                
                self.stats_label.config(
                    text=f"📊 {game_count} game(s) | {chunk_count} total sections"
                )
                
                self.search_button.config(state=tk.NORMAL)
                self.list_games_button.config(state=tk.NORMAL)
                
                # Update game dropdown
                if game_count > 0:
                    games = sorted(self.guide_tool.games_index.keys())
                    self.available_games = games
                    
                    # Update combo box values
                    for widget in self.panel_frame.winfo_children():
                        if isinstance(widget, ttk.Frame):
                            for child in widget.winfo_children():
                                if isinstance(child, ttk.Combobox):
                                    game_values = ["all"] + [g for g in games]
                                    child.config(values=game_values)
                                    break
            else:
                self.status_label.config(
                    text="⚠️ Game guides structure unavailable",
                    foreground=DarkTheme.ACCENT_ORANGE
                )
                self.stats_label.config(text="")
        except Exception as e:
            self.logger.warning(f"[GameGuide] Status update error: {e}")
            self.status_label.config(
                text="⚠️ Status unavailable",
                foreground=DarkTheme.ACCENT_ORANGE
            )
            self.stats_label.config(text="")
    
    def _get_guide_tool(self):
        """Get game guide tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'game_guide' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('game_guide')
    
    def _show_error(self, message: str):
        """Show error message"""
        self.status_label.config(
            text=f"❌ {message}",
            foreground=DarkTheme.ACCENT_RED
        )
        self.search_button.config(state=tk.NORMAL)
        self.list_games_button.config(state=tk.NORMAL)
    
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
        self.logger.tool("[GameGuide] Component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        GameGuideComponent instance
    """
    return GameGuideComponent(parent_gui, ai_core, logger)
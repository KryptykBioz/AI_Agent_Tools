# Filename: BASE/tools/installed/web_fetch/component.py
"""
Web Fetch Tool - GUI Component
Dynamic GUI panel for safe webpage retrieval
"""
import tkinter as tk
from tkinter import ttk
from BASE.interface.gui_themes import DarkTheme


class WebFetchComponent:
    """
    GUI component for Web Fetch tool
    Provides interface for webpage retrieval with format selection
    """
    
    def __init__(self, parent_gui, ai_core, logger):
        """
        Initialize web fetch component
        
        Args:
            parent_gui: Main GUI instance
            ai_core: AI Core instance
            logger: Logger instance
        """
        self.parent_gui = parent_gui
        self.ai_core = ai_core
        self.logger = logger
        
        # Tool instance
        self.web_fetch_tool = None
        
        # GUI elements
        self.panel_frame = None
        self.status_label = None
        self.url_var = None
        self.format_var = None
        self.results_display = None
        self.fetch_button = None
        self.clear_button = None
        self.domains_button = None
        self.approved_domains = []
        
        # State
        self.last_url = ""
        self.fetch_count = 0
    
    def create_panel(self, parent_frame):
        """
        Create the web fetch panel
        
        Args:
            parent_frame: Parent frame to add panel to
        """
        # Main panel frame
        self.panel_frame = ttk.LabelFrame(
            parent_frame,
            text="🌐 Web Fetch",
            style="Dark.TLabelframe"
        )
        self.panel_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # URL input section
        self._create_url_section()
        
        # Format options section
        self._create_options_section()
        
        # Status section
        self._create_status_section()
        
        # Results display section
        self._create_results_section()
        
        # Update initial status
        self._update_status()
        
        return self.panel_frame
    
    def _create_url_section(self):
        """Create URL input section"""
        url_frame = ttk.Frame(self.panel_frame)
        url_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # URL label
        ttk.Label(
            url_frame,
            text="URL:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # URL entry
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(
            url_frame,
            textvariable=self.url_var,
            font=("Segoe UI", 10)
        )
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Bind Enter key to fetch
        url_entry.bind('<Return>', lambda e: self._perform_fetch())
        
        # Fetch button
        self.fetch_button = ttk.Button(
            url_frame,
            text="🔍 Fetch",
            command=self._perform_fetch,
            width=12
        )
        self.fetch_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Clear button
        self.clear_button = ttk.Button(
            url_frame,
            text="🗑️ Clear",
            command=self._clear_results,
            width=10
        )
        self.clear_button.pack(side=tk.LEFT)
    
    def _create_options_section(self):
        """Create format options section"""
        options_frame = ttk.Frame(self.panel_frame)
        options_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Format label
        ttk.Label(
            options_frame,
            text="Format:",
            style="TLabel"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Format dropdown
        self.format_var = tk.StringVar(value="text")
        format_combo = ttk.Combobox(
            options_frame,
            textvariable=self.format_var,
            values=["text", "markdown", "pdf"],
            state="readonly",
            width=10,
            font=("Segoe UI", 9)
        )
        format_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Domains button
        self.domains_button = ttk.Button(
            options_frame,
            text="📋 Approved Domains",
            command=self._show_domains,
            width=18
        )
        self.domains_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Info label
        info_label = tk.Label(
            options_frame,
            text="ℹ️ Only approved domains can be fetched",
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
            text="🟢 Ready - Web fetch available",
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
            "Web Fetch Features:\n\n"
            "• Retrieve pages from approved domains\n"
            "• Multiple output formats (text, markdown, PDF)\n"
            "• Safe domain whitelist\n"
            "• Automatic content cleaning\n"
            "• Max size: 10MB per page\n\n"
            "Supported formats:\n"
            "- text: Clean plain text extraction\n"
            "- markdown: Preserve structure and links\n"
            "- pdf: Visual rendering (requires playwright)\n\n"
            "Use 'Approved Domains' to see full list"
        )
    
    def _create_results_section(self):
        """Create results display section"""
        results_frame = ttk.Frame(self.panel_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Label
        ttk.Label(
            results_frame,
            text="Retrieved Content:",
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
            "content",
            foreground=DarkTheme.FG_PRIMARY
        )
        self.results_display.tag_configure(
            "separator",
            foreground=DarkTheme.FG_MUTED
        )
    
    def _perform_fetch(self):
        """Perform web fetch"""
        url = self.url_var.get().strip()
        
        if not url:
            self._show_error("Please enter a URL")
            return
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            self._show_error("URL must start with http:// or https://")
            return
        
        # Get tool instance
        self.web_fetch_tool = self._get_web_fetch_tool()
        
        if not self.web_fetch_tool:
            self._show_error("Web fetch tool not initialized")
            return
        
        # Get format
        output_format = self.format_var.get()
        
        # Update status
        self.status_label.config(
            text=f"🔄 Fetching {url}...",
            foreground=DarkTheme.ACCENT_BLUE
        )
        self.fetch_button.config(state=tk.DISABLED)
        
        # Track fetch
        self.last_url = url
        self.fetch_count += 1
        
        # Perform fetch asynchronously
        if self.ai_core.main_loop:
            import asyncio
            
            async def fetch_async():
                try:
                    result = await self.web_fetch_tool.execute(
                        'fetch', [url, output_format]
                    )
                    
                    # Update UI on main thread
                    self.panel_frame.after(0, lambda: self._handle_fetch_result(result))
                
                except Exception as e:
                    self.panel_frame.after(0, lambda: self._show_error(f"Fetch failed: {e}"))
                    self.logger.error(f"[WebFetch] Fetch error: {e}")
            
            asyncio.run_coroutine_threadsafe(fetch_async(), self.ai_core.main_loop)
        
        self.logger.tool(f"[WebFetch] Fetching: {url} ({output_format})")
    
    def _handle_fetch_result(self, result: dict):
        """Handle fetch result"""
        self.fetch_button.config(state=tk.NORMAL)
        
        if result.get('success'):
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            
            # Display results
            self._display_results(content, metadata)
            
            # Update status
            size = metadata.get('size', 0)
            domain = metadata.get('domain', 'unknown')
            
            status_text = f"✅ Retrieved {size:,} chars from {domain}"
            
            self.status_label.config(
                text=status_text,
                foreground=DarkTheme.ACCENT_GREEN
            )
            
            self.logger.success(f"[WebFetch] Retrieved {size:,} characters")
        
        else:
            error_msg = result.get('content', 'Fetch failed')
            self._show_error(error_msg)
            self.logger.warning(f"[WebFetch] Fetch failed: {error_msg}")
    
    def _display_results(self, results: str, metadata: dict):
        """Display formatted fetch results"""
        self.results_display.config(state=tk.NORMAL)
        self.results_display.delete("1.0", tk.END)
        
        if not results:
            self.results_display.insert(tk.END, "No content retrieved")
            self.results_display.config(state=tk.DISABLED)
            return
        
        # Parse and format results
        lines = results.split('\n')
        
        for line in lines:
            if line.startswith('**') and line.endswith('**'):
                # Title
                title = line.replace('**', '')
                self.results_display.insert(tk.END, f"{title}\n", "title")
            
            elif line.startswith('URL:'):
                # URL
                self.results_display.insert(tk.END, f"{line}\n", "url")
            
            elif line.startswith('Format:') or line.startswith('Size:'):
                # Metadata
                self.results_display.insert(tk.END, f"{line}\n", "header")
            
            elif line.startswith('---'):
                # Separator
                self.results_display.insert(tk.END, f"{line}\n", "separator")
            
            else:
                # Content
                self.results_display.insert(tk.END, f"{line}\n", "content")
        
        self.results_display.config(state=tk.DISABLED)
        self.results_display.see("1.0")  # Scroll to top
    
    def _show_domains(self):
        """Show approved domains list"""
        # Get tool instance
        self.web_fetch_tool = self._get_web_fetch_tool()
        
        if not self.web_fetch_tool:
            self._show_error("Web fetch tool not initialized")
            return
        
        # Update status
        self.status_label.config(
            text="📋 Retrieving approved domains...",
            foreground=DarkTheme.ACCENT_BLUE
        )
        
        # Get domains asynchronously
        if self.ai_core.main_loop:
            import asyncio
            
            async def get_domains_async():
                try:
                    result = await self.web_fetch_tool.execute('list_domains', [])
                    
                    # Update UI on main thread
                    self.panel_frame.after(0, lambda: self._handle_domains_result(result))
                
                except Exception as e:
                    self.panel_frame.after(0, lambda: self._show_error(f"Failed to get domains: {e}"))
                    self.logger.error(f"[WebFetch] Domains error: {e}")
            
            asyncio.run_coroutine_threadsafe(get_domains_async(), self.ai_core.main_loop)
        
        self.logger.tool("[WebFetch] Listing approved domains")
    
    def _handle_domains_result(self, result: dict):
        """Handle domains list result"""
        if result.get('success'):
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            
            # Display domains
            self._display_results(content, metadata)
            
            # Update status
            domain_count = metadata.get('domain_count', 0)
            self.status_label.config(
                text=f"📋 {domain_count} approved domains listed",
                foreground=DarkTheme.ACCENT_GREEN
            )
            
            self.logger.success(f"[WebFetch] Listed {domain_count} domains")
        else:
            error_msg = result.get('content', 'Failed to get domains')
            self._show_error(error_msg)
    
    def _clear_results(self):
        """Clear results display"""
        self.results_display.config(state=tk.NORMAL)
        self.results_display.delete("1.0", tk.END)
        self.results_display.config(state=tk.DISABLED)
        
        self.url_var.set("")
        self.last_url = ""
        
        self._update_status()
        
        self.logger.tool("[WebFetch] Cleared results")
    
    def _update_status(self):
        """Update status display"""
        self.web_fetch_tool = self._get_web_fetch_tool()
        
        if not self.web_fetch_tool:
            self.status_label.config(
                text="⚫ Tool Not Available",
                foreground=DarkTheme.FG_MUTED
            )
            self.fetch_button.config(state=tk.DISABLED)
            self.domains_button.config(state=tk.DISABLED)
            return
        
        # Web fetch is always available (no API key needed)
        self.status_label.config(
            text="🟢 Ready - Web fetch available",
            foreground=DarkTheme.ACCENT_GREEN
        )
        self.fetch_button.config(state=tk.NORMAL)
        self.domains_button.config(state=tk.NORMAL)
    
    def _get_web_fetch_tool(self):
        """Get web fetch tool instance from AI Core"""
        if not hasattr(self.ai_core, 'tool_manager'):
            return None
        
        tool_manager = self.ai_core.tool_manager
        
        # Check if tool is active
        if 'web_fetch' not in tool_manager._active_tools:
            return None
        
        return tool_manager._active_tools.get('web_fetch')
    
    def _show_error(self, message: str):
        """Show error message"""
        self.status_label.config(
            text=f"❌ {message}",
            foreground=DarkTheme.ACCENT_RED
        )
        self.fetch_button.config(state=tk.NORMAL)
    
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
        self.logger.tool("[WebFetch] Component cleaned up")


# Factory function for dynamic loading
def create_component(parent_gui, ai_core, logger):
    """
    Factory function called by GUI system
    
    Args:
        parent_gui: Main GUI instance
        ai_core: AI Core instance
        logger: Logger instance
        
    Returns:
        WebFetchComponent instance
    """
    return WebFetchComponent(parent_gui, ai_core, logger)
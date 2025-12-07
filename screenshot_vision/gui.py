#!/usr/bin/env python3
"""
Vision Tool GUI - Lightweight dark theme
Optimized for speed and minimal resource usage
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import asyncio
import threading
from typing import Optional
import sys
import os

# Add BASE to path if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from BASE.tools.installed.screenshot_vision.tool import ScreenshotVisionTool
from BASE.handlers.base_tool import BaseConfig


class VisionGUI:
    """Minimal dark-theme GUI for vision tool"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Vision Tool")
        self.root.geometry("900x700")
        
        # Dark theme colors
        self.bg = "#1e1e1e"
        self.fg = "#d4d4d4"
        self.input_bg = "#2d2d2d"
        self.button_bg = "#0e639c"
        self.button_hover = "#1177bb"
        self.success = "#4ec9b0"
        self.error = "#f48771"
        
        self.root.configure(bg=self.bg)
        
        # Initialize tool
        self.tool = None
        self.loop = asyncio.new_event_loop()
        self.running = False
        
        self._setup_ui()
        self._start_async_loop()
        self._init_tool()
    
    def _setup_ui(self):
        """Build UI components"""
        # Header
        hdr = tk.Frame(self.root, bg=self.bg)
        hdr.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        tk.Label(hdr, text="Vision Tool", font=("Segoe UI", 16, "bold"),
                bg=self.bg, fg=self.fg).pack(side=tk.LEFT)
        
        self.status_lbl = tk.Label(hdr, text="⚫ Initializing", font=("Segoe UI", 10),
                                   bg=self.bg, fg="#888")
        self.status_lbl.pack(side=tk.RIGHT)
        
        # Query input
        input_frm = tk.Frame(self.root, bg=self.bg)
        input_frm.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(input_frm, text="Query:", bg=self.bg, fg=self.fg,
                font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.query_var = tk.StringVar()
        self.query_entry = tk.Entry(input_frm, textvariable=self.query_var,
                                    bg=self.input_bg, fg=self.fg, font=("Consolas", 10),
                                    insertbackground=self.fg, relief=tk.FLAT,
                                    highlightthickness=1, highlightcolor=self.button_bg,
                                    highlightbackground="#333")
        self.query_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.query_entry.bind('<Return>', lambda e: self._analyze())
        
        # Buttons
        btn_frm = tk.Frame(self.root, bg=self.bg)
        btn_frm.pack(fill=tk.X, padx=10, pady=5)
        
        self.screenshot_btn = self._create_btn(btn_frm, "📸 Screenshot", self._screenshot)
        self.screenshot_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.analyze_btn = self._create_btn(btn_frm, "🔍 Analyze", self._analyze)
        self.analyze_btn.pack(side=tk.LEFT)
        
        self.clear_btn = self._create_btn(btn_frm, "🗑 Clear", self._clear, bg="#555")
        self.clear_btn.pack(side=tk.RIGHT)
        
        # Output
        output_frm = tk.Frame(self.root, bg=self.bg)
        output_frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(output_frm, text="Output:", bg=self.bg, fg=self.fg,
                font=("Segoe UI", 10)).pack(anchor=tk.W, pady=(0, 5))
        
        self.output_txt = scrolledtext.ScrolledText(output_frm, wrap=tk.WORD,
                                                    bg=self.input_bg, fg=self.fg,
                                                    font=("Consolas", 10), relief=tk.FLAT,
                                                    highlightthickness=1, highlightcolor=self.button_bg,
                                                    highlightbackground="#333", insertbackground=self.fg)
        self.output_txt.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags
        self.output_txt.tag_config("success", foreground=self.success)
        self.output_txt.tag_config("error", foreground=self.error)
        self.output_txt.tag_config("info", foreground="#888")
    
    def _create_btn(self, parent, text, cmd, bg=None):
        """Create styled button"""
        btn = tk.Button(parent, text=text, command=cmd, bg=bg or self.button_bg,
                       fg=self.fg, font=("Segoe UI", 10), relief=tk.FLAT,
                       cursor="hand2", padx=15, pady=5, borderwidth=0)
        btn.bind('<Enter>', lambda e: e.widget.config(bg=self.button_hover if not bg else "#666"))
        btn.bind('<Leave>', lambda e: e.widget.config(bg=bg or self.button_bg))
        return btn
    
    def _start_async_loop(self):
        """Start async event loop in background thread"""
        def run_loop():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.running = True
        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()
    
    def _init_tool(self):
        """Initialize vision tool"""
        def init():
            cfg = BaseConfig()
            self.tool = ScreenshotVisionTool(cfg, logger=None)
            
            async def init_async():
                success = await self.tool.initialize()
                status = self.tool.get_status()
                
                self.root.after(0, lambda: self._update_status(success, status))
            
            asyncio.run_coroutine_threadsafe(init_async(), self.loop)
        
        threading.Thread(target=init, daemon=True).start()
    
    def _update_status(self, success, status):
        """Update status display"""
        if success and status.get('available'):
            monitors = status.get('monitors', 0)
            self.status_lbl.config(text=f"🟢 Ready ({monitors} monitor{'s' if monitors != 1 else ''})",
                                  fg=self.success)
        else:
            self.status_lbl.config(text="🔴 Not Available", fg=self.error)
            self._log("Vision tool not available. Install: pip install pyautogui screeninfo pillow\n", "error")
    
    def _screenshot(self):
        """Execute screenshot command"""
        if not self.tool:
            return
        
        self._log("Capturing screenshot...\n", "info")
        self._disable_btns()
        
        async def run():
            result = await self.tool.execute('screenshot', [])
            self.root.after(0, lambda: self._handle_result(result))
        
        asyncio.run_coroutine_threadsafe(run(), self.loop)
    
    def _analyze(self):
        """Execute analyze command"""
        if not self.tool:
            return
        
        query = self.query_var.get().strip()
        if not query:
            self._log("Please enter a query\n", "error")
            return
        
        self._log(f"Analyzing: {query}\n", "info")
        self._disable_btns()
        
        async def run():
            result = await self.tool.execute('analyze', [query])
            self.root.after(0, lambda: self._handle_result(result))
        
        asyncio.run_coroutine_threadsafe(run(), self.loop)
    
    def _handle_result(self, result):
        """Handle command result"""
        self._enable_btns()
        
        if result.get('success'):
            data = result.get('data', '')
            self._log(f"{data}\n\n", "success")
        else:
            error = result.get('error', 'Unknown error')
            self._log(f"Error: {error}\n\n", "error")
    
    def _clear(self):
        """Clear output"""
        self.output_txt.delete('1.0', tk.END)
        self.query_var.set('')
    
    def _log(self, msg, tag=""):
        """Append to output"""
        self.output_txt.insert(tk.END, msg, tag)
        self.output_txt.see(tk.END)
    
    def _disable_btns(self):
        """Disable buttons during execution"""
        self.screenshot_btn.config(state=tk.DISABLED)
        self.analyze_btn.config(state=tk.DISABLED)
    
    def _enable_btns(self):
        """Enable buttons"""
        self.screenshot_btn.config(state=tk.NORMAL)
        self.analyze_btn.config(state=tk.NORMAL)
    
    def run(self):
        """Start GUI"""
        try:
            self.root.mainloop()
        finally:
            self.loop.call_soon_threadsafe(self.loop.stop)
            if self.tool:
                asyncio.run_coroutine_threadsafe(self.tool.cleanup(), self.loop)


if __name__ == "__main__":
    gui = VisionGUI()
    gui.run()
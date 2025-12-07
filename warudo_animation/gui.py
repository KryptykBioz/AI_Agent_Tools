import tkinter as tk
from tkinter import ttk
import threading
import queue
from typing import Optional
import sys
import os

# Add BASE to path if running standalone
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from animate_avatar import WarudoManager

class WarudoGUI:
    """Minimal high-performance Warudo controller GUI"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Warudo Control")
        self.root.geometry("400x550")
        self.root.resizable(False, False)
        
        # Apply dark theme
        self._apply_dark_theme()
        
        # Manager and state
        self.manager: Optional[WarudoManager] = None
        self.ws_url = tk.StringVar(value="ws://127.0.0.1:19190")
        self.status = tk.StringVar(value="Disconnected")
        self.last_cmd = tk.StringVar(value="None")
        
        # Lock-free message queue for GUI updates
        self.msg_queue = queue.Queue(maxsize=50)
        
        # Build UI
        self._build_ui()
        
        # Start queue processor (50ms polling - minimal overhead)
        self._process_queue()
    
    def _apply_dark_theme(self):
        """Apply dark theme - cached style configuration"""
        bg = '#1e1e1e'
        fg = '#e0e0e0'
        select_bg = '#2d2d30'
        border = '#3e3e42'
        
        self.root.configure(bg=bg)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles - batch for performance
        style.configure('TFrame', background=bg)
        style.configure('TLabel', background=bg, foreground=fg)
        style.configure('TLabelframe', background=bg, foreground=fg, bordercolor=border)
        style.configure('TLabelframe.Label', background=bg, foreground=fg)
        style.configure('TButton', background=select_bg, foreground=fg, bordercolor=border, 
                       focuscolor=select_bg, lightcolor=select_bg, darkcolor=border)
        style.map('TButton', background=[('active', '#3e3e42'), ('pressed', '#4e4e52')])
        style.configure('TEntry', fieldbackground=select_bg, foreground=fg, 
                       bordercolor=border, insertcolor=fg)
    
    def _build_ui(self):
        """Build minimal UI - optimized layout"""
        # Connection frame
        conn_frame = ttk.LabelFrame(self.root, text="Connection", padding=10)
        conn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(conn_frame, text="WebSocket URL:").pack(anchor=tk.W)
        ttk.Entry(conn_frame, textvariable=self.ws_url, width=40).pack(fill=tk.X, pady=(0,5))
        
        btn_frame = ttk.Frame(conn_frame)
        btn_frame.pack(fill=tk.X)
        
        self.conn_btn = ttk.Button(btn_frame, text="Connect", command=self._connect)
        self.conn_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        
        ttk.Button(btn_frame, text="Disconnect", command=self._disconnect).pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Status
        self.status_label = ttk.Label(conn_frame, textvariable=self.status, foreground="#ff6b6b")
        self.status_label.pack(pady=(5,0))
        
        # Emotions frame
        emo_frame = ttk.LabelFrame(self.root, text="Emotions", padding=10)
        emo_frame.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)
        
        emotions = ['happy', 'angry', 'sad', 'relaxed', 'surprised']
        for i, emo in enumerate(emotions):
            btn = ttk.Button(emo_frame, text=emo.capitalize(), 
                           command=lambda e=emo: self._send_emotion(e))
            btn.grid(row=i//2, column=i%2, sticky=tk.EW, padx=2, pady=2)
        
        emo_frame.columnconfigure(0, weight=1)
        emo_frame.columnconfigure(1, weight=1)
        
        # Animations frame
        anim_frame = ttk.LabelFrame(self.root, text="Animations", padding=10)
        anim_frame.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)
        
        animations = ['nod', 'laugh', 'shrug', 'upset', 'wave', 'cat', 
                     'confused', 'shy', 'swing', 'stretch', 'yay', 'taunt',
                     'bow', 'scare', 'refuse', 'snap']
        
        for i, anim in enumerate(animations):
            btn = ttk.Button(anim_frame, text=anim.capitalize(),
                           command=lambda a=anim: self._send_animation(a))
            btn.grid(row=i//4, column=i%4, sticky=tk.EW, padx=2, pady=2)
        
        for j in range(4):
            anim_frame.columnconfigure(j, weight=1)
        
        # Status frame
        status_frame = ttk.LabelFrame(self.root, text="Last Command", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(status_frame, textvariable=self.last_cmd).pack()
    
    def _connect(self):
        """Connect in background thread - non-blocking"""
        if self.manager and self.manager.controller.ws_connected:
            self._queue_msg("Already connected")
            return
        
        self.conn_btn.config(state=tk.DISABLED)
        self._queue_msg("Connecting...")
        
        def _connect_thread():
            try:
                self.manager = WarudoManager(
                    websocket_url=self.ws_url.get(),
                    auto_connect=False,
                    timeout=3.0,
                    gui_logger=self._log_callback
                )
                
                if self.manager.connect(timeout=3.0):
                    self._queue_msg("✓ Connected")
                    self.status.set("Connected")
                    self.root.after(0, lambda: self.status_label.configure(foreground="#51cf66"))
                else:
                    self._queue_msg("✗ Connection failed")
                    self.status.set("Connection failed")
            except Exception as e:
                self._queue_msg(f"✗ Error: {e}")
                self.status.set("Error")
            finally:
                self.root.after(0, lambda: self.conn_btn.config(state=tk.NORMAL))
        
        threading.Thread(target=_connect_thread, daemon=True).start()
    
    def _disconnect(self):
        """Disconnect WebSocket"""
        if self.manager:
            self.manager.controller.shutdown()
            self.manager = None
            self.status.set("Disconnected")
            self.root.after(0, lambda: self.status_label.configure(foreground="#ff6b6b"))
            self._queue_msg("Disconnected")
    
    def _send_emotion(self, emotion: str):
        """Send emotion command - fast path"""
        if not self.manager or not self.manager.controller.ws_connected:
            self._queue_msg("✗ Not connected")
            return
        
        def _send():
            if self.manager.send_emotion(emotion):
                self._queue_msg(f"✓ Emotion: {emotion}")
                self.last_cmd.set(f"emotion: {emotion}")
            else:
                self._queue_msg(f"✗ Failed: {emotion}")
        
        threading.Thread(target=_send, daemon=True).start()
    
    def _send_animation(self, animation: str):
        """Send animation command - fast path"""
        if not self.manager or not self.manager.controller.ws_connected:
            self._queue_msg("✗ Not connected")
            return
        
        def _send():
            if self.manager.send_animation(animation):
                self._queue_msg(f"✓ Animation: {animation}")
                self.last_cmd.set(f"animation: {animation}")
            else:
                self._queue_msg(f"✗ Failed: {animation}")
        
        threading.Thread(target=_send, daemon=True).start()
    
    def _log_callback(self, msg: str):
        """Logger callback - queue messages for GUI thread"""
        self._queue_msg(msg)
    
    def _queue_msg(self, msg: str):
        """Queue message for GUI update - lock-free"""
        try:
            self.msg_queue.put_nowait(msg)
        except queue.Full:
            pass  # Drop message if queue full
    
    def _process_queue(self):
        """Process message queue - minimal overhead polling"""
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                print(f"[Warudo] {msg}")  # Console output
        except queue.Empty:
            pass
        
        # Re-schedule (50ms = 20Hz, minimal CPU usage)
        self.root.after(50, self._process_queue)
    
    def cleanup(self):
        """Cleanup on exit"""
        if self.manager:
            self.manager.controller.shutdown()


def main():
    root = tk.Tk()
    gui = WarudoGUI(root)
    
    # Cleanup on close
    def on_close():
        gui.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
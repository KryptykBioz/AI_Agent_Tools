#!/usr/bin/env python3
"""
Twitch Chat Monitor GUI
Lightweight dark-theme interface optimized for performance
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import time
from datetime import datetime
from typing import Optional, Dict, List
import socket
import re

# Dark theme colors
BG = "#1e1e1e"
FG = "#e0e0e0"
BG_INPUT = "#2d2d2d"
BG_BUTTON = "#3c3c3c"
BG_BUTTON_ACTIVE = "#4a4a4a"
ACCENT = "#8b5cf6"
SUCCESS = "#22c55e"
ERROR = "#ef4444"
WARNING = "#f59e0b"

class TwitchIRC:
    """Optimized Twitch IRC handler"""

    __slots__ = (
        'channel', 'oauth', 'nick', 'sock', 'running', 'thread',
        'msg_queue', 'status_queue'
    )
    
    def __init__(self, channel: str, oauth: str = "", nick: str = ""):
        self.channel = channel.lower().strip().lstrip('#')
        self.oauth = oauth
        self.nick = nick if nick else f"justinfan{int(time.time())%100000}"
        self.sock: Optional[socket.socket] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.msg_queue = queue.Queue(maxsize=1000)
        self.status_queue = queue.Queue(maxsize=100)
        
    def _parse(self, line: str) -> Optional[Dict]:
        """Fast IRC message parser"""
        try:
            if line.startswith("PING"):
                return {"type": "ping", "data": line.split(":", 1)[1].strip()}
            if "PRIVMSG" not in line:
                return None
            m = re.search(r':([^!]+)!', line)
            if not m:
                return None
            user = m.group(1)
            parts = line.split('PRIVMSG', 1)[1]
            if ':' not in parts:
                return None
            text = parts.split(':', 1)[1].strip()
            return {"type": "msg", "user": user, "text": text, "time": time.time()}
        except:
            return None
    
    def connect(self) -> bool:
        """Connect to Twitch IRC"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)
            self.sock.connect(("irc.chat.twitch.tv", 6667))
            
            if self.oauth and self.nick:
                self.sock.send(f"PASS {self.oauth}\r\n".encode())
            else:
                self.sock.send(b"PASS SCHMOOPIIE\r\n")
            
            self.sock.send(f"NICK {self.nick}\r\n".encode())
            time.sleep(0.5)
            self.sock.send(f"JOIN #{self.channel}\r\n".encode())
            time.sleep(0.5)
            
            self.status_queue.put(("success", f"Connected to #{self.channel}"))
            return True
        except Exception as e:
            self.status_queue.put(("error", f"Connection failed: {e}"))
            return False
    
    def start(self):
        """Start monitoring"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
    
    def _loop(self):
        """Main IRC loop"""
        if not self.connect():
            self.running = False
            return
        
        buf = ""
        self.sock.settimeout(1)
        
        while self.running:
            try:
                data = self.sock.recv(4096).decode('utf-8', errors='ignore')
                if not data:
                    break
                buf += data
                
                while '\r\n' in buf:
                    line, buf = buf.split('\r\n', 1)
                    parsed = self._parse(line)
                    
                    if parsed:
                        if parsed["type"] == "ping":
                            self.sock.send(f"PONG :{parsed['data']}\r\n".encode())
                        elif parsed["type"] == "msg":
                            try:
                                self.msg_queue.put_nowait(parsed)
                            except queue.Full:
                                pass
            except socket.timeout:
                continue
            except Exception as e:
                self.status_queue.put(("error", f"Error: {e}"))
                break
        
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.status_queue.put(("warning", "Disconnected"))
    
    def send(self, msg: str) -> bool:
        """Send message"""
        if not self.running or not self.sock or not self.oauth:
            return False
        try:
            self.sock.send(f"PRIVMSG #{self.channel} :{msg}\r\n".encode())
            return True
        except:
            return False
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

class TwitchGUI:
    """High-performance dark-theme GUI"""

    __slots__ = (
        'root', 'irc', 'connected', 'msg_count', 'last_update',
        'update_interval', 'user_colors', 'channel_entry', 'connect_btn',
        'status_label', 'count_label', 'chat_text', 'msg_entry',
        'send_btn', 'oauth_frame', 'oauth_entry', 'nick_entry'
    )
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Twitch Chat Monitor")
        self.root.geometry("400x800")
        self.root.configure(bg=BG)
        
        self.irc: Optional[TwitchIRC] = None
        self.connected = False
        self.msg_count = 0
        self.last_update = 0
        self.update_interval = 100  # ms
        self.user_colors = {}  # Map usernames to persistent colors
        
        self._build_ui()
        self._schedule_update()
        
    def _build_ui(self):
        """Build optimized UI"""
        # Top bar
        top = tk.Frame(self.root, bg=BG, pady=10)
        top.pack(fill=tk.X, padx=10)
        
        tk.Label(top, text="Channel:", bg=BG, fg=FG, font=("Arial", 10)).pack(side=tk.LEFT, padx=(0,5))
        
        self.channel_entry = tk.Entry(top, bg=BG_INPUT, fg=FG, insertbackground=FG, 
                                      relief=tk.FLAT, font=("Arial", 10), width=20)
        self.channel_entry.pack(side=tk.LEFT, padx=5)
        self.channel_entry.insert(0, "vedal987")
        
        self.connect_btn = tk.Button(top, text="Connect", bg=ACCENT, fg="#fff", 
                                     relief=tk.FLAT, font=("Arial", 10, "bold"),
                                     activebackground=BG_BUTTON_ACTIVE, 
                                     cursor="hand2", command=self._toggle_connect)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_label = tk.Label(top, text="●", bg=BG, fg=ERROR, font=("Arial", 16))
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.count_label = tk.Label(top, text="Messages: 0", bg=BG, fg=FG, font=("Arial", 9))
        self.count_label.pack(side=tk.RIGHT)
        
        # Chat display
        chat_frame = tk.Frame(self.root, bg=BG)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        
        self.chat_text = scrolledtext.ScrolledText(
            chat_frame, bg=BG_INPUT, fg=FG, insertbackground=FG,
            relief=tk.FLAT, font=("Consolas", 20), wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure base tags
        self.chat_text.tag_config("system", foreground=WARNING, font=("Consolas", 9, "italic"))
        
        # Bottom input
        bottom = tk.Frame(self.root, bg=BG, pady=10)
        bottom.pack(fill=tk.X, padx=10)
        
        self.msg_entry = tk.Entry(bottom, bg=BG_INPUT, fg=FG, insertbackground=FG,
                                  relief=tk.FLAT, font=("Arial", 10), state=tk.DISABLED)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        self.msg_entry.bind("<Return>", lambda e: self._send_msg())
        
        self.send_btn = tk.Button(bottom, text="Send", bg=BG_BUTTON, fg=FG,
                                 relief=tk.FLAT, font=("Arial", 10),
                                 state=tk.DISABLED, command=self._send_msg)
        self.send_btn.pack(side=tk.LEFT)
        
        # Optional OAuth frame (collapsed by default)
        self.oauth_frame = tk.Frame(self.root, bg=BG)
        
        tk.Label(self.oauth_frame, text="OAuth (optional):", bg=BG, fg=FG, 
                font=("Arial", 9)).pack(side=tk.LEFT, padx=(0,5))
        self.oauth_entry = tk.Entry(self.oauth_frame, bg=BG_INPUT, fg=FG, 
                                    show="*", width=30, font=("Arial", 9))
        self.oauth_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.oauth_frame, text="Nick:", bg=BG, fg=FG, 
                font=("Arial", 9)).pack(side=tk.LEFT, padx=(10,5))
        self.nick_entry = tk.Entry(self.oauth_frame, bg=BG_INPUT, fg=FG, 
                                   width=15, font=("Arial", 9))
        self.nick_entry.pack(side=tk.LEFT)
        
        toggle_btn = tk.Button(top, text="⚙", bg=BG_BUTTON, fg=FG, relief=tk.FLAT,
                              font=("Arial", 10), command=self._toggle_oauth)
        toggle_btn.pack(side=tk.RIGHT, padx=5)
    
    def _toggle_oauth(self):
        """Toggle OAuth input visibility"""
        if self.oauth_frame.winfo_ismapped():
            self.oauth_frame.pack_forget()
        else:
            self.oauth_frame.pack(fill=tk.X, padx=10, pady=(0,10), before=self.chat_text.master)
    
    def _toggle_connect(self):
        """Toggle connection"""
        if self.connected:
            self._disconnect()
        else:
            self._connect()
    
    def _connect(self):
        """Connect to Twitch"""
        channel = self.channel_entry.get().strip()
        if not channel:
            self._log_system("Enter a channel name")
            return
        
        oauth = self.oauth_entry.get().strip()
        nick = self.nick_entry.get().strip()
        
        self.irc = TwitchIRC(channel, oauth, nick)
        self.irc.start()
        
        self.connected = True
        self.connect_btn.config(text="Disconnect", bg=ERROR)
        self.channel_entry.config(state=tk.DISABLED)
        self.status_label.config(fg=SUCCESS)
        
        if oauth and nick:
            self.msg_entry.config(state=tk.NORMAL)
            self.send_btn.config(state=tk.NORMAL)
        
        self._log_system(f"Connecting to #{channel}...")
    
    def _disconnect(self):
        """Disconnect from Twitch"""
        if self.irc:
            self.irc.stop()
            self.irc = None
        
        self.connected = False
        self.connect_btn.config(text="Connect", bg=ACCENT)
        self.channel_entry.config(state=tk.NORMAL)
        self.status_label.config(fg=ERROR)
        self.msg_entry.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)
        
        self._log_system("Disconnected")
    
    def _send_msg(self):
        """Send message to chat"""
        msg = self.msg_entry.get().strip()
        if not msg or not self.irc:
            return
        
        if self.irc.send(msg):
            self.msg_entry.delete(0, tk.END)
            self._log_system(f"[You] {msg}")
        else:
            self._log_system("Failed to send (OAuth required)")
    
    def _log_system(self, msg: str):
        """Log system message"""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, f"[System] {msg}\n", "system")
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def _get_user_color(self, username: str) -> str:
        """Get or generate a persistent color for a username"""
        if username not in self.user_colors:
            # Generate a consistent color based on username hash
            import hashlib
            hash_val = int(hashlib.md5(username.encode()).hexdigest(), 16)
            
            # Generate vibrant colors with good contrast
            hue = hash_val % 360
            # Avoid dark colors by keeping saturation and lightness high
            saturation = 70 + (hash_val % 30)
            lightness = 55 + (hash_val % 20)
            
            # Convert HSL to RGB
            h = hue / 360.0
            s = saturation / 100.0
            l = lightness / 100.0
            
            def hsl_to_rgb(h, s, l):
                if s == 0:
                    r = g = b = l
                else:
                    def hue_to_rgb(p, q, t):
                        if t < 0: t += 1
                        if t > 1: t -= 1
                        if t < 1/6: return p + (q - p) * 6 * t
                        if t < 1/2: return q
                        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
                        return p
                    
                    q = l * (1 + s) if l < 0.5 else l + s - l * s
                    p = 2 * l - q
                    r = hue_to_rgb(p, q, h + 1/3)
                    g = hue_to_rgb(p, q, h)
                    b = hue_to_rgb(p, q, h - 1/3)
                
                return int(r * 255), int(g * 255), int(b * 255)
            
            r, g, b = hsl_to_rgb(h, s, l)
            self.user_colors[username] = f"#{r:02x}{g:02x}{b:02x}"
        
        return self.user_colors[username]
    
    def _update_chat(self, msgs: List[Dict]):
        """Batch update chat display"""
        if not msgs:
            return
        
        self.chat_text.config(state=tk.NORMAL)
        
        for m in msgs:
            username = m['user']
            color = self._get_user_color(username)
            
            # Create or update tag for this user
            tag_name = f"user_{username}"
            self.chat_text.tag_config(tag_name, foreground=color, font=("Consolas", 20, "bold"))
            
            # Insert username with unique color
            self.chat_text.insert(tk.END, f"{username}: ", tag_name)
            self.chat_text.insert(tk.END, f"{m['text']}\n")
            self.msg_count += 1
        
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
        self.count_label.config(text=f"Messages: {self.msg_count}")
    
    def _schedule_update(self):
        """Optimized update loop"""
        # Guard: only process if IRC is initialized
        if self.irc is None:
            self.root.after(self.update_interval, self._schedule_update)
            return
        
        now = time.time()
        
        # Batch process messages
        msgs = []
        try:
            while len(msgs) < 50:  # Process up to 50 msgs per frame
                msgs.append(self.irc.msg_queue.get_nowait())
        except queue.Empty:
            pass
        
        if msgs:
            self._update_chat(msgs)
        
        # Process status updates
        try:
            while True:
                typ, msg = self.irc.status_queue.get_nowait()
                self._log_system(msg)
        except queue.Empty:
            pass
        
        self.root.after(self.update_interval, self._schedule_update)
    
    def run(self):
        """Start GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()
    
    def _on_close(self):
        """Cleanup on close"""
        if self.irc:
            self.irc.stop()
        self.root.destroy()

if __name__ == "__main__":
    gui = TwitchGUI()
    gui.run()
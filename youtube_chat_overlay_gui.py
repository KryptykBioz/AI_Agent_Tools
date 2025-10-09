# Filename: BASE/tools/youtube_chat_overlay.py
"""
YouTube Live Chat Overlay GUI for OBS Studio
Displays live chat messages in a transparent window that can be captured by OBS
"""
import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
import requests
from datetime import datetime
from typing import Optional, List, Dict
import re
from collections import deque
import hashlib
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# from BASE.tools.content_filter import ContentFilter
from personality.controls import ENABLE_CONTENT_FILTER

class YouTubeChatOverlay:
    """GUI overlay for YouTube live chat messages"""
    
    def __init__(self, video_id: str = "", max_displayed_messages: int = 10):
        self.video_id = video_id
        self.max_displayed_messages = max_displayed_messages
        
        # Chat monitoring
        self.live_chat_id = None
        self.next_page_token = None
        self.polling_interval = 2.0
        self.session = None
        self.running = False
        self.shutdown_flag = threading.Event()
        self.monitor_thread = None
        
        # Message storage
        self.message_queue = deque(maxlen=max_displayed_messages)

        # --- 🔍 Content Filtering Integration ---
        # Enable content filter controls
        self.controls = type("Controls", (), {"ENABLE_CONTENT_FILTER": True})()
        try:
            from BASE.tools.content_filter import ContentFilter
            self.content_filter = ContentFilter()
        except ImportError:
            self.content_filter = None
            print("[Warning] ContentFilter module not found. Filtering disabled.")
        # ------------------------------------------------
        
        # Color mapping for usernames
        self.username_colors = {}
        
        # Create GUI
        self.root = tk.Tk()
        self.root.title("YouTube Chat Overlay")
        self.root.geometry("400x600")
        
        # Make window stay on top
        self.root.attributes('-topmost', True)
        
        # Setup GUI components
        self._setup_gui()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_gui(self):
        """Setup GUI components"""
        # Control frame (not transparent - for controls)
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        
        # Video ID input
        ttk.Label(control_frame, text="Video ID:").pack(side=tk.LEFT)
        self.video_id_entry = ttk.Entry(control_frame, width=20)
        self.video_id_entry.pack(side=tk.LEFT, padx=5)
        if self.video_id:
            self.video_id_entry.insert(0, self.video_id)
        
        # Start/Stop button
        self.start_button = ttk.Button(
            control_frame, 
            text="Start", 
            command=self._toggle_monitoring
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Transparent toggle button
        self.transparent_button = ttk.Button(
            control_frame,
            text="Make Transparent",
            command=self._toggle_transparency
        )
        self.transparent_button.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(control_frame, text="Status: Stopped")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Chat display frame
        self.chat_frame = tk.Frame(self.root, bg='#1a1a1a')
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Message labels list
        self.message_labels = []
        for i in range(self.max_displayed_messages):
            # Author label
            author_label = tk.Label(
                self.chat_frame,
                text="",
                font=("Segoe UI", 20, "bold"),
                fg="#FFFFFF",  # Will be set dynamically
                bg="#1a1a1a",
                anchor="w",
                justify=tk.LEFT
            )
            author_label.pack(fill=tk.X, pady=(5, 0))
            
            # Message label
            message_label = tk.Label(
                self.chat_frame,
                text="",
                font=("Segoe UI", 20),
                fg="white",
                bg="#1a1a1a",
                anchor="w",
                justify=tk.LEFT,
                wraplength=380
            )
            message_label.pack(fill=tk.X, pady=(0, 5))
            
            self.message_labels.append((author_label, message_label))
        
        self.is_transparent = False
    
    def _get_username_color(self, username: str) -> str:
        """Generate a consistent, vibrant color for each username"""
        if username not in self.username_colors:
            hash_value = int(hashlib.md5(username.encode()).hexdigest()[:8], 16)
            hue = hash_value % 360
            saturation = 0.7 + (hash_value % 20) / 100
            value = 0.8 + (hash_value % 15) / 100
            h = hue / 60
            c = value * saturation
            x = c * (1 - abs(h % 2 - 1))
            m = value - c
            if h < 1:
                r, g, b = c, x, 0
            elif h < 2:
                r, g, b = x, c, 0
            elif h < 3:
                r, g, b = 0, c, x
            elif h < 4:
                r, g, b = 0, x, c
            elif h < 5:
                r, g, b = x, 0, c
            else:
                r, g, b = c, 0, x
            r, g, b = int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.username_colors[username] = color
        return self.username_colors[username]
    
    def _toggle_transparency(self):
        """Toggle window transparency for OBS"""
        if self.is_transparent:
            self.root.attributes('-alpha', 1.0)
            self.root.config(bg='SystemButtonFace')
            self.chat_frame.config(bg='#1a1a1a')
            self.transparent_button.config(text="Make Transparent")
            self.is_transparent = False
        else:
            self.root.attributes('-alpha', 0.01)
            self.root.config(bg='black')
            self.chat_frame.config(bg='black')
            self.transparent_button.config(text="Make Opaque")
            self.is_transparent = True
            messagebox.showinfo(
                "Transparent Mode",
                "Window is now transparent!\n\n"
                "In OBS Studio:\n"
                "1. Add 'Window Capture' source\n"
                "2. Select this window\n"
                "3. Right-click source → Filters → Add 'Color Key'\n"
                "4. Set Key Color Type to 'Black'\n"
                "5. Adjust Similarity if needed\n\n"
                "To make opaque again, click where the button was."
            )
    
    def _toggle_monitoring(self):
        """Start or stop monitoring"""
        if self.running:
            self._stop_monitoring()
        else:
            video_id = self.video_id_entry.get().strip()
            if not video_id:
                messagebox.showerror("Error", "Please enter a Video ID")
                return
            self.video_id = video_id
            self._start_monitoring()
    
    def _start_monitoring(self):
        """Start monitoring YouTube chat"""
        try:
            self.status_label.config(text="Status: Connecting...")
            self.start_button.config(state=tk.DISABLED)
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            })
            self.live_chat_id = self._extract_live_chat_id()
            if not self.live_chat_id:
                self.status_label.config(text="Status: Failed - No live chat")
                self.start_button.config(state=tk.NORMAL)
                messagebox.showerror(
                    "Error", 
                    "Could not find live chat.\n"
                    "Make sure the stream is live and chat is enabled."
                )
                return
            self.running = True
            self.shutdown_flag.clear()
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True
            )
            self.monitor_thread.start()
            self.status_label.config(text="Status: Connected")
            self.start_button.config(text="Stop", state=tk.NORMAL)
        except Exception as e:
            self.status_label.config(text="Status: Error")
            self.start_button.config(state=tk.NORMAL)
            messagebox.showerror("Error", f"Failed to start monitoring:\n{e}")
    
    def _stop_monitoring(self):
        """Stop monitoring YouTube chat"""
        self.running = False
        self.shutdown_flag.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=3.0)
        if self.session:
            self.session.close()
            self.session = None
        self.status_label.config(text="Status: Stopped")
        self.start_button.config(text="Start", state=tk.NORMAL)
    
    def _extract_live_chat_id(self) -> Optional[str]:
        """Extract live chat ID from video page"""
        try:
            url = f"https://www.youtube.com/watch?v={self.video_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            patterns = [
                r'"liveChatRenderer":\{"continuations":\[\{"reloadContinuationData":\{"continuation":"([^"]+)"',
                r'"conversationBar":\{"liveChatRenderer":\{"continuations":\[\{"reloadContinuationData":\{"continuation":"([^"]+)"',
                r'continuation":"([A-Za-z0-9_-]{100,})"'
            ]
            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    return match.group(1)
            return None
        except Exception as e:
            print(f"Error extracting chat ID: {e}")
            return None
    
    def _fetch_chat_messages(self) -> List[Dict]:
        """Fetch chat messages using continuation token"""
        if not self.live_chat_id:
            return []
        try:
            url = "https://www.youtube.com/youtubei/v1/live_chat/get_live_chat"
            payload = {
                "context": {
                    "client": {
                        "clientName": "WEB",
                        "clientVersion": "2.20231201.00.00"
                    }
                },
                "continuation": self.live_chat_id
            }
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            messages = []
            continuation_contents = data.get("continuationContents", {})
            live_chat_continuation = continuation_contents.get("liveChatContinuation", {})
            actions = live_chat_continuation.get("actions", [])
            for action in actions:
                item = action.get("addChatItemAction", {}).get("item", {})
                text_message = item.get("liveChatTextMessageRenderer", {})
                if text_message:
                    author = text_message.get("authorName", {}).get("simpleText", "Unknown")
                    message_parts = text_message.get("message", {}).get("runs", [])
                    message_text = "".join(part.get("text", "") for part in message_parts)
                    messages.append({
                        'author': author,
                        'message': message_text
                    })
            continuations = live_chat_continuation.get("continuations", [])
            if continuations:
                for cont in continuations:
                    if "invalidationContinuationData" in cont:
                        self.live_chat_id = cont["invalidationContinuationData"]["continuation"]
                        timeout_ms = cont["invalidationContinuationData"].get("timeoutDurationMillis", 2000)
                        self.polling_interval = max(timeout_ms / 1000, 1.0)
                        break
                    elif "timedContinuationData" in cont:
                        self.live_chat_id = cont["timedContinuationData"]["continuation"]
                        timeout_ms = cont["timedContinuationData"].get("timeoutDurationMillis", 2000)
                        self.polling_interval = max(timeout_ms / 1000, 1.0)
                        break
            return messages
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return []
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        consecutive_errors = 0
        max_consecutive_errors = 10
        while not self.shutdown_flag.is_set():
            try:
                if not self.live_chat_id:
                    break
                messages = self._fetch_chat_messages()
                if messages:
                    for msg in messages:
                        message_text = msg['message']

                        # --- 🔍 Apply Content Filter before display ---
                        if self.content_filter and ENABLE_CONTENT_FILTER:
                            filtered_reply, was_filtered, filter_reason = self.content_filter.filter_content(
                                message_text, log_callback=print
                            )
                            if was_filtered:
                                print(f"[Filter] Message from {msg['author']} filtered: {filter_reason}")
                                continue
                            # elif filtered_reply.strip().upper() != "SAFE":
                            #     print(f"[Filter] Message from {msg['author']} blocked (not SAFE)")
                            #     continue



                        # if self.controls.ENABLE_CONTENT_FILTER:
                        #     filtered_reply, was_filtered, filter_reason = self.content_filter.filter_content(
                        #         reply, 
                        #         log_callback=self._log
                        #     )
                        #     if was_filtered:
                        #         print(reply)
                        #         self._log(f"[Filter] Response was filtered due to: {filter_reason}", "system")
                        #         reply = filtered_reply
                        # ------------------------------------------------

                        self.message_queue.append(msg)
                    
                    # Update GUI in main thread
                    self.root.after(0, self._update_display)
                    consecutive_errors = 0
                time.sleep(self.polling_interval)
            except Exception as e:
                consecutive_errors += 1
                print(f"Monitor error ({consecutive_errors}/{max_consecutive_errors}): {e}")
                if consecutive_errors >= max_consecutive_errors:
                    self.root.after(0, lambda: self.status_label.config(text="Status: Error - Too many failures"))
                    break
                time.sleep(min(2.0 ** consecutive_errors, 30.0))
        self.running = False
    
    def _update_display(self):
        """Update the message display"""
        for author_label, message_label in self.message_labels:
            author_label.config(text="")
            message_label.config(text="")
        messages = list(self.message_queue)
        for i, msg in enumerate(messages[-self.max_displayed_messages:]):
            if i < len(self.message_labels):
                author_label, message_label = self.message_labels[i]
                username = msg['author']
                color = self._get_username_color(username)
                author_label.config(text=f"{username}:", fg=color)
                message_label.config(text=msg['message'])
    
    def _on_close(self):
        """Handle window close event"""
        if self.running:
            self._stop_monitoring()
        self.root.destroy()
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()


def main():
    """Main entry point"""
    import sys
    video_id = ""
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
    overlay = YouTubeChatOverlay(video_id=video_id)
    overlay.run()


if __name__ == "__main__":
    main()

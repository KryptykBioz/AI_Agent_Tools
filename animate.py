#!/usr/bin/env python3
"""
Warudo Avatar Animation Script - Robust WarudoManager + WebSocket handling

Revisions:
- Don't exit on import failure; set a flag so callers can detect availability.
- Keep a reference to the running WebSocketApp and allow send() from other threads.
- Safer connection handling and optional reconnect logic.
"""

import time
import json
import threading
from typing import Dict, List

# WebSocket imports
WEBSOCKET_AVAILABLE = True
try:
    import websocket
except Exception as e:
    print("Warning: websocket-client not installed or failed to import.")
    print("Install with: pip install websocket-client")
    WEBSOCKET_AVAILABLE = False

# Keyword mapping: words → Warudo command
animation_keywords = {
    # -------------------------------
    # EMOTIONS
    # -------------------------------
    # Happy
    'happy': 'happy',
    'glad': 'happy',
    'joy': 'happy',
    'joyful': 'happy',
    'cheerful': 'happy',
    'delighted': 'happy',
    'excited': 'happy',
    'overjoyed': 'happy',
    'thrilled': 'happy',
    'ecstatic': 'happy',
    'smile': 'smile',
    'smiling': 'smile',
    'grinning': 'smile',
    'pleased': 'smile',
    'content': 'smile',
    'satisfied': 'smile',

   # Angry
    'angry': 'angry',
    'mad': 'angry',
    'furious': 'angry',
    'irritated': 'angry',
    'annoyed': 'angry',
    'frustrated': 'angry',
    'pissed': 'angry',
    'enraged': 'angry',
    'livid': 'angry',
    'resentful': 'angry',

    # Sad
    'sad': 'sad',
    'upset': 'sad',
    'disappointed': 'sad',
    'unhappy': 'sad',
    'miserable': 'sad',
    'heartbroken': 'sad',
    'tearful': 'sad',
    'cry': 'sad',
    'crying': 'sad',
    'blue': 'sad',
    'gloomy': 'sad',
    'down': 'sad',

    #relaxed
    'relaxed': 'relaxed',
    'chill': 'relaxed',
    'calm': 'relaxed',
    'peaceful': 'relaxed',
    'serene': 'relaxed',
    'tranquil': 'relaxed',
    'laid back': 'relaxed',
    'easygoing': 'relaxed',
    'content': 'relaxed',
    'satisfied': 'relaxed',
    'at ease': 'relaxed',
    'zen': 'relaxed',
    'composed': 'relaxed',
    'unwind': 'relaxed',

    # Surprised
    'surprised': 'surprised',
    'shocked': 'surprised',
    'astonished': 'surprised',
    'amazed': 'surprised',
    'startled': 'surprised',
    'whoa': 'surprised',
    'wow': 'surprised',
    'unbelievable': 'surprised',
    'stunned': 'surprised',

    # # Extra expressions
    # 'wink': 'wink',
    # 'winking': 'wink',
    # 'blink': 'wink',

    # 'neutral': 'neutral',
    # 'calm': 'neutral',
    # 'relaxed': 'neutral',

    # -------------------------------
    # ANIMATIONS
    # -------------------------------

    # Nod
    'nod': 'nod',
    'nodding': 'nod',
    'yes': 'nod',
    'yep': 'nod',
    'sure': 'nod',
    'okay': 'nod',
    'agree': 'nod',
    'alright': 'nod',
    
    # Laugh
    'laugh': 'laugh',
    'laughing': 'laugh',
    'lol': 'laugh',
    'haha': 'laugh',
    'hehe': 'laugh',
    'lmao': 'laugh',
    'rofl': 'laugh',
    'funny': 'laugh',
    'hilarious': 'laugh',
    'giggle': 'laugh',

    # Shrug
    'shrug': 'shrug',
    'shrugging': 'shrug',
    "don't know": 'shrug',
    'dunno': 'shrug',
    'not sure': 'shrug',
    'meh': 'shrug',
    'huh': 'shrug',

    # Upset / sulking animation
    'upset': 'upset',
    'pout': 'upset',
    'sulk': 'upset',
    'grumble': 'upset',
    'hmph': 'upset',

    # Wave
    'wave': 'wave',
    'waving': 'wave',
    'hello': 'wave',
    'hi': 'wave',
    'hey': 'wave',
    'goodbye': 'wave',
    'bye': 'wave',
    'see ya': 'wave',

    # Cat
    'cat': 'cat',
    'kitty': 'cat',
    'meow': 'cat',
    'nya': 'cat',
    'purr': 'cat',
    'neko': 'cat',

    # Confused
    'confused': 'confused',
    'puzzled': 'confused',
    'perplexed': 'confused',
    'unsure': 'confused',
    'lost': 'confused',
    'huh': 'confused',

    # shy
    'shy': 'shy',
    'nervous': 'shy',
    'timid': 'shy',
    'blush': 'shy',
    'blushing': 'shy',
    'embarrassed': 'shy',
    'bashful': 'shy',

    # Shake head
    # 'shake': 'shake_head',
    # 'no': 'shake_head',
    # 'nope': 'shake_head',
    # 'nah': 'shake_head',
    # 'disagree': 'shake_head',
    # 'wrong': 'shake_head',

    # Bow
    # 'bow': 'bow',
    # 'bowing': 'bow',
    # 'thank': 'bow',
    # 'thanks': 'bow',
    # 'arigato': 'bow',
    # 'gratitude': 'bow',
    # 'respect': 'bow',

    # # Dance
    # 'dance': 'dance',
    # 'dancing': 'dance',
    # 'groove': 'dance',
    # 'boogie': 'dance',
    # 'party': 'dance',

    # # Clap
    # 'clap': 'clap',
    # 'clapping': 'clap',
    # 'applaud': 'clap',
    # 'applause': 'clap',
    # 'bravo': 'clap',
    # 'cheer': 'clap',

    # # Point
    # 'point': 'point',
    # 'pointing': 'point',
    # 'look': 'point',
    # 'there': 'point',

    # # Think
    # 'think': 'think',
    # 'thinking': 'think',
    # 'wonder': 'think',
    # 'ponder': 'think',
    # 'consider': 'think',
    # 'hmm': 'think',

    # # Thumbs up
    # 'thumbs up': 'thumbs_up',
    # 'good job': 'thumbs_up',
    # 'well done': 'thumbs_up',
    # 'great': 'thumbs_up',
    # 'awesome': 'thumbs_up',
    # 'nice': 'thumbs_up',
    # 'perfect': 'thumbs_up',

}



class WarudoWebSocketController:
    """Controller for sending commands to Warudo via WebSocket API"""

    def __init__(self, websocket_url: str = "ws://127.0.0.1:19190"):
        self.websocket_url = websocket_url
        self.ws_app = None  # WebSocketApp instance
        self.ws_thread = None
        self.ws_connected = False
        self.connection_lock = threading.Lock()
        self._last_error = None

        self.available_emotions = [
            'smile', 'happy', 'sad', 'angry', 'surprised',
            'wink', 'blush', 'neutral'
        ]
        self.available_animations = [
            'wave', 'nod', 'shake_head', 'bow', 'dance',
            'clap', 'point', 'think', 'thumbs_up', 'shrug',
            'laugh', 'upset', 'cat', 'confused', 'shy'
        ]

    def _on_message(self, ws, message):
        # For debugging — the Warudo server may send useful messages
        print(f"[Warudo WS] Received: {message}")

    def _on_error(self, ws, error):
        print(f"[Warudo WS] Error: {error}")
        self._last_error = error
        self.ws_connected = False

    def _on_close(self, ws, close_status_code, close_msg):
        print("[Warudo WS] Connection closed:", close_status_code, close_msg)
        self.ws_connected = False

    def _on_open(self, ws):
        print("[Warudo WS] Connection opened")
        self.ws_connected = True

    def connect_websocket(self, timeout: float = 5.0) -> bool:
        """Connect to Warudo WebSocket server. Returns True if connected."""
        if not WEBSOCKET_AVAILABLE:
            print("[Warudo WS] websocket-client not available.")
            return False

        with self.connection_lock:
            if self.ws_connected:
                return True
            try:
                self.ws_app = websocket.WebSocketApp(
                    self.websocket_url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )

                # Run the WebSocketApp in a separate daemon thread
                self.ws_thread = threading.Thread(target=self.ws_app.run_forever, daemon=True)
                self.ws_thread.start()

                # Wait until connected or timeout
                start_time = time.time()
                while not self.ws_connected and (time.time() - start_time) < timeout:
                    time.sleep(0.05)

                return self.ws_connected
            except Exception as e:
                print(f"[Warudo WS] Failed to start connection: {e}")
                self._last_error = e
                return False

    def send_websocket_command(self, command: Dict) -> bool:
        """Send JSON command to Warudo. Returns True on assumed success."""
        if not WEBSOCKET_AVAILABLE:
            print("[Warudo WS] websocket-client not installed; cannot send.")
            return False

        if not self.ws_app or not self.ws_connected:
            print("[Warudo WS] Not connected; cannot send.")
            return False

        try:
            message = json.dumps(command)
            # WebSocketApp exposes send(); this will forward to the socket if connected.
            self.ws_app.send(message)
            print(f"[Warudo WS] Sent: {message}")
            return True
        except Exception as e:
            print(f"[Warudo WS] Failed to send command: {e}")
            self._last_error = e
            return False

    def send_single_command(self, command: str) -> bool:
        """Send a single word command (emotion or animation)"""
        command = command.strip().lower()
        if command in self.available_emotions:
            return self.send_websocket_command({'action': 'emotion', 'data': command})
        elif command in self.available_animations:
            return self.send_websocket_command({'action': 'animation', 'data': command})
        else:
            print(f"[Warudo WS] Unknown command: {command}")
            return False

    def get_available_commands(self) -> Dict[str, List[str]]:
        return {'emotions': self.available_emotions, 'animations': self.available_animations}


class WarudoManager:
    """High-level manager for Warudo integration."""

    def __init__(self, websocket_url: str = "ws://127.0.0.1:19190", auto_connect: bool = True, timeout: float = 5.0):
        self.enabled = True
        self.controller = WarudoWebSocketController(websocket_url)
        self.animation_keywords = animation_keywords
        if auto_connect and WEBSOCKET_AVAILABLE:
            self.connect(timeout=timeout)

    def connect(self, timeout: float = 5.0) -> bool:
        success = self.controller.connect_websocket(timeout=timeout)
        if success:
            print("[WarudoManager] Connected successfully.")
        else:
            print("[WarudoManager] Connection failed.")
        return success

    def detect_and_send_animations(self, text: str):
        """Detect animation keywords in text and trigger Warudo commands."""
        if not self.enabled or not self.controller:
            return
        if not text:
            return
        text_lower = text.lower()
        sent = set()
        for keyword, command in self.animation_keywords.items():
            if keyword in text_lower and command not in sent:
                print(f"[WarudoManager] Detected '{keyword}' -> '{command}'")
                if self.controller.send_single_command(command):
                    sent.add(command)
                    # small delay to avoid spamming the avatar too fast
                    time.sleep(0.12)
        if sent:
            print(f"[WarudoManager] Sent animation(s): {', '.join(sent)}")

    def handle_command(self, command: str) -> bool:
        """Handle CLI-like commands for Warudo."""
        cmd = command.lower().strip()
        if cmd == "/warudo_connect":
            return self.connect()
        elif cmd == "/warudo_test":
            test_commands = ['happy', 'wave', 'nod', 'thumbs_up']
            for c in test_commands:
                self.controller.send_single_command(c)
                time.sleep(0.8)
            return True
        elif cmd == "/warudo_commands":
            cmds = self.controller.get_available_commands()
            print("[WarudoManager] Emotions:", ", ".join(cmds['emotions']))
            print("[WarudoManager] Animations:", ", ".join(cmds['animations']))
            return True
        elif cmd.startswith("/warudo_send "):
            c = cmd.split(" ", 1)[1]
            return self.controller.send_single_command(c)
        elif cmd == "/warudo_keywords":
            for k, v in sorted(self.animation_keywords.items()):
                print(f"  '{k}' -> {v}")
            return True
        return False


if __name__ == "__main__":
    if not WEBSOCKET_AVAILABLE:
        print("websocket-client not available; cannot run demo.")
    else:
        wm = WarudoManager("ws://127.0.0.1:19190")
        if wm.connect(timeout=3.0):
            wm.detect_and_send_animations("I am so happy, let's wave and laugh together!")
        else:
            print("Failed to connect to Warudo for demo.")
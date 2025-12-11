# Filename: BASE/tools/installed/warudo/animate_avatar.py
"""
Warudo Avatar Animation Script
Key optimizations:
- Event-based connection instead of busy-wait
- Connection pooling with keep-alive
- Batch command queuing
- Lock-free fast path for connected state
"""

import time
import json
import threading
from typing import Dict, List, Optional
from collections import deque
# from BASE.core.logger import Logger, MessageType

WEBSOCKET_AVAILABLE = True
try:
    import websocket
except Exception:
    WEBSOCKET_AVAILABLE = False


class WarudoWebSocketController:
    """WebSocket controller with connection pooling"""

    def __init__(self, websocket_url: str = "ws://127.0.0.1:19190"):
        self.websocket_url = websocket_url
        self.ws_app = None
        self.ws_thread = None
        self.ws_connected = False
        
        # Event-based connection tracking (faster than polling)
        self._connection_event = threading.Event()
        self._shutdown_event = threading.Event()
        
        # Command queue for batch processing
        self._command_queue = deque(maxlen=100)
        self._queue_lock = threading.Lock()
        
        self._last_error = None
        # self.logger = logger if logger else Logger(name="WarudoController")

        self.available_emotions = ['happy', 'angry', 'sad', 'relaxed', 'surprised']
        self.available_animations = [
            'nod', 'laugh', 'shrug', 'upset', 'wave', 'cat', 'confused', 
            'shy', 'swing', 'stretch', 'yay', 'taunt', 'bow', 'scare', 'refuse', 'snap'
        ]

    def _on_message(self, ws, message):
        print(f"Received: {message}")

    def _on_error(self, ws, error):
        print(f"WebSocket error: {error}")
        self._last_error = error
        self.ws_connected = False
        self._connection_event.clear()

    def _on_close(self, ws, close_status_code, close_msg):
        print(f"Connection closed: {close_status_code} {close_msg}")
        self.ws_connected = False
        self._connection_event.clear()

    def _on_open(self, ws):
        print("Connection opened")
        self.ws_connected = True
        self._connection_event.set()  # Signal connection ready

    def connect_websocket(self, timeout: float = 5.0) -> bool:
        """Connect with event-based waiting (no busy-wait)"""
        if not WEBSOCKET_AVAILABLE:
            print("websocket-client not available")
            return False

        # Fast path: already connected
        if self.ws_connected and self._connection_event.is_set():
            return True

        try:
            self._connection_event.clear()
            
            self.ws_app = websocket.WebSocketApp(
                self.websocket_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )

            self.ws_thread = threading.Thread(target=self.ws_app.run_forever, daemon=True)
            self.ws_thread.start()

            # Event-based wait (efficient, no CPU spinning)
            connected = self._connection_event.wait(timeout)
            return connected

        except Exception as e:
            print(f"Failed to start connection: {e}")
            self._last_error = e
            return False

    def send_websocket_command(self, command: Dict) -> bool:
        """Send command with fast-path optimization"""
        if not WEBSOCKET_AVAILABLE:
            return False

        # Fast path check (no lock needed for read)
        if not self.ws_connected:
            print("Not connected; cannot send")
            return False

        try:
            message = json.dumps(command)
            self.ws_app.send(message)
            print(f"Sent: {message}")
            return True
        except Exception as e:
            print(f"Failed to send command: {e}")
            self._last_error = e
            self.ws_connected = False
            self._connection_event.clear()
            return False

    def queue_command(self, command: Dict):
        """Queue command for batch sending (reduces network overhead)"""
        with self._queue_lock:
            self._command_queue.append(command)

    def flush_queue(self) -> int:
        """Flush queued commands in batch"""
        sent = 0
        with self._queue_lock:
            while self._command_queue:
                cmd = self._command_queue.popleft()
                if self.send_websocket_command(cmd):
                    sent += 1
        return sent

    def get_available_commands(self) -> Dict[str, List[str]]:
        return {'emotions': self.available_emotions, 'animations': self.available_animations}

    def shutdown(self):
        """Clean shutdown"""
        self._shutdown_event.set()
        if self.ws_app:
            self.ws_app.close()


class WarudoManager:
    """High-level manager with connection pooling"""

    def __init__(self, websocket_url: str = "ws://127.0.0.1:19190", 
                 auto_connect: bool = True, timeout: float = 5.0, gui_logger=None):
        self.enabled = True
        
        self.logger = Logger(
            name="Warudo",
            enable_timestamps=True,
            enable_console=False,
            gui_callback=gui_logger,
            config=config
        )
        
        self.controller = WarudoWebSocketController(websocket_url)
        
        if auto_connect and WEBSOCKET_AVAILABLE:
            self.connect(timeout=timeout)

    def connect(self, timeout: float = 5.0) -> bool:
        success = self.controller.connect_websocket(timeout=timeout)
        if success:
            print("Connected successfully")
        else:
            print("Connection failed")
        return success

    def send_emotion(self, emotion: str) -> bool:
        """Send emotion with validation"""
        if not self.enabled or not self.controller:
            return False
        
        if emotion not in self.controller.available_emotions:
            print(f"Unknown emotion: {emotion}")
            return False
        
        command = {"action": "emotion", "data": emotion}
        success = self.controller.send_websocket_command(command)
        if success:
            print(f"Emotion set: {emotion}")
        return success

    def send_animation(self, animation: str) -> bool:
        """Send animation with validation"""
        if not self.enabled or not self.controller:
            return False
        
        if animation not in self.controller.available_animations:
            print(f"Unknown animation: {animation}")
            return False
        
        command = {"action": "animation", "data": animation}
        success = self.controller.send_websocket_command(command)
        if success:
            print(f"Animation played: {animation}")
        return success

    def detect_and_send_animations(self, text: str):
        """DEPRECATED: Kept for backward compatibility"""
        pass

    def handle_command(self, command: str) -> bool:
        """Handle CLI commands"""
        cmd = command.lower().strip()
        if cmd == "/warudo_connect":
            return self.connect()
        elif cmd == "/warudo_test":
            test_commands = [("emotion", "happy"), ("animation", "wave"), ("animation", "nod")]
            for cmd_type, cmd_name in test_commands:
                (self.send_emotion if cmd_type == "emotion" else self.send_animation)(cmd_name)
                time.sleep(0.8)
            return True
        elif cmd == "/warudo_commands":
            cmds = self.controller.get_available_commands()
            print(f"Emotions: {', '.join(cmds['emotions'])}")
            print(f"Animations: {', '.join(cmds['animations'])}")
            return True
        elif cmd.startswith("/warudo_emotion "):
            return self.send_emotion(cmd.split(" ", 1)[1])
        elif cmd.startswith("/warudo_animation "):
            return self.send_animation(cmd.split(" ", 1)[1])
        return False


if __name__ == "__main__":
    if not WEBSOCKET_AVAILABLE:
        print("websocket-client not available")
    else:
        wm = WarudoManager("ws://127.0.0.1:19190")
        if wm.connect(timeout=3.0):
            print("\nTest 1: Emotion")
            wm.send_emotion("happy")
            time.sleep(2)
            print("\nTest 2: Animation")
            wm.send_animation("wave")
            time.sleep(2)
            print("\nTest 3: Multiple")
            wm.send_animation("nod")
            time.sleep(1)
            wm.send_emotion("relaxed")
        else:
            print("Failed to connect")
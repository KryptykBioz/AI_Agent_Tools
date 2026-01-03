# Filename: BASE/tools/installed/warudo/animate_avatar.py
"""
Warudo Avatar Animation Script - FIXED Race Condition
Key improvements:
- Proper connection state synchronization
- Thread-safe event-based waiting
- Reliable connection verification
"""

import time
import json
import threading
from typing import Dict, List, Optional
from collections import deque
from BASE.core.logger import Logger

WEBSOCKET_AVAILABLE = True
WEBSOCKET_ERROR = None
try:
    from websocket import WebSocketApp
    import websocket as ws_module
except ImportError as e:
    WEBSOCKET_AVAILABLE = False
    WEBSOCKET_ERROR = f"websocket-client not installed: {e}"
except AttributeError as e:
    WEBSOCKET_AVAILABLE = False
    WEBSOCKET_ERROR = f"Wrong websocket module installed. Uninstall 'websocket' and install 'websocket-client': {e}"
except Exception as e:
    WEBSOCKET_AVAILABLE = False
    WEBSOCKET_ERROR = f"Failed to import websocket: {e}"


class WarudoWebSocketController:
    """WebSocket controller with fixed race condition handling"""

    def __init__(self, websocket_url: str = "ws://127.0.0.1:19190", agent_name: str = None):
        self.websocket_url = websocket_url
        self.agent_name = (agent_name or "agent").lower()
        self.ws_app = None
        self.ws_thread = None
        self.ws_connected = False
        self.logger = Logger()
        
        # Thread-safe connection tracking
        self._connection_event = threading.Event()
        self._shutdown_event = threading.Event()
        self._connection_lock = threading.Lock()
        
        # Command queue for batch processing
        self._command_queue = deque(maxlen=100)
        self._queue_lock = threading.Lock()
        
        self._last_error = None
        self._connection_start_time = None
        self._connection_ready = False

        self.available_emotions = ['happy', 'angry', 'sad', 'relaxed', 'surprised']
        self.available_animations = [
            'nod', 'laugh', 'shrug', 'upset', 'wave', 'cat', 'confused', 
            'shy', 'swing', 'stretch', 'yay', 'taunt', 'bow', 'scare', 'refuse', 'snap'
        ]
        
        self.logger.warudo(f"[Warudo] Controller initialized for agent: {self.agent_name}")

    def _on_message(self, ws, message):
        """Handle incoming WebSocket message"""
        self.logger.warudo(f"Received: {message}")

    def _on_error(self, ws, error):
        """Handle WebSocket error"""
        error_msg = str(error)
        error_type = type(error).__name__
        
        self.logger.error(
            f"[Warudo] WebSocket error\n"
            f"  Error: {error_msg}\n"
            f"  Type: {error_type}\n"
            f"  Agent: {self.agent_name}\n"
            f"  URL: {self.websocket_url}"
        )
        
        self._last_error = error
        
        with self._connection_lock:
            self.ws_connected = False
            self._connection_ready = False
            self._connection_event.clear()

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        self.logger.warudo(f"Connection closed: {close_status_code} {close_msg}")
        
        with self._connection_lock:
            self.ws_connected = False
            self._connection_ready = False
            self._connection_event.clear()

    def _on_open(self, ws):
        """Handle WebSocket open"""
        self.logger.warudo("Connection opened")
        
        with self._connection_lock:
            self.ws_connected = True
            self._connection_ready = True
            self._connection_start_time = time.time()
            self._connection_event.set()

    def connect_websocket(self, timeout: float = 5.0) -> bool:
        """
        Connect with proper synchronization
        
        FIXED: Reliable event-based waiting with verification
        """
        if not WEBSOCKET_AVAILABLE:
            self.logger.error(f"[Warudo] WebSocket not available: {WEBSOCKET_ERROR}")
            return False

        # Check if already connected and verified
        with self._connection_lock:
            if self.ws_connected and self._connection_ready and self._connection_event.is_set():
                if self._connection_start_time:
                    age = time.time() - self._connection_start_time
                    if age < 300:
                        if self.ws_thread and self.ws_thread.is_alive():
                            return True
                
                self.logger.warudo("[Warudo] Connection stale, reconnecting...")
                self._cleanup_connection_unsafe()

        try:
            self._connection_event.clear()
            self._cleanup_connection()
            
            with self._connection_lock:
                self._connection_ready = False
            
            self.logger.warudo(f"[Warudo] Connecting to {self.websocket_url} for agent '{self.agent_name}'...")
            
            self.ws_app = WebSocketApp(
                self.websocket_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )

            self.ws_thread = threading.Thread(
                target=self._run_websocket,
                daemon=True,
                name="WarudoWebSocket"
            )
            self.ws_thread.start()
            self.logger.warudo("[Warudo] Connection thread started, waiting for connection...")

            connected = self._connection_event.wait(timeout)
            
            if not connected:
                self.logger.error(
                    f"[Warudo] Connection timeout after {timeout}s\n"
                    f"  URL: {self.websocket_url}\n"
                    f"  Agent: {self.agent_name}\n"
                    f"  Last error: {self._last_error or 'None'}"
                )
                self._cleanup_connection()
                return False
            
            time.sleep(0.1)
            
            with self._connection_lock:
                if not self.ws_connected or not self._connection_ready:
                    self.logger.error(
                        f"[Warudo] Connection event fired but state not ready\n"
                        f"  ws_connected: {self.ws_connected}\n"
                        f"  _connection_ready: {self._connection_ready}\n"
                        f"  Last error: {self._last_error or 'None'}"
                    )
                    self._cleanup_connection_unsafe()
                    return False
            
            if not self.ws_thread or not self.ws_thread.is_alive():
                self.logger.error("[Warudo] Connection thread died unexpectedly")
                self._cleanup_connection()
                return False
            
            self.logger.warudo(f"[Warudo] Connection verified and ready for agent '{self.agent_name}'")
            return True

        except Exception as e:
            self.logger.error(f"[Warudo] Failed to start connection: {e}\n  Type: {type(e).__name__}")
            import traceback
            self.logger.error(f"[Warudo] Traceback:\n{traceback.format_exc()}")
            self._last_error = e
            self._cleanup_connection()
            return False
    
    def _run_websocket(self):
        """Run WebSocket connection in thread"""
        try:
            self.logger.warudo(f"[Warudo] WebSocket thread running for agent '{self.agent_name}'...")
            self.ws_app.run_forever()
            self.logger.warudo(f"[Warudo] WebSocket thread exited normally for agent '{self.agent_name}'")
        except Exception as e:
            self.logger.error(
                f"[Warudo] WebSocket thread error\n"
                f"  Error: {e}\n"
                f"  Type: {type(e).__name__}\n"
                f"  Agent: {self.agent_name}"
            )
            import traceback
            self.logger.error(f"[Warudo] Traceback:\n{traceback.format_exc()}")
            
            with self._connection_lock:
                self.ws_connected = False
                self._connection_ready = False
                self._connection_event.clear()
    
    def _cleanup_connection_unsafe(self):
        """
        Cleanup without acquiring lock (caller must hold lock)
        """
        if self.ws_app:
            try:
                self.ws_app.close()
            except:
                pass
            self.ws_app = None
        
        # Note: Don't join thread while holding lock
        self.ws_thread = None
        self.ws_connected = False
        self._connection_ready = False
        self._connection_event.clear()
    
    def _cleanup_connection(self):
        """Clean up existing connection (thread-safe)"""
        with self._connection_lock:
            self._cleanup_connection_unsafe()

    def send_websocket_command(self, command: Dict) -> bool:
        """
        Send command with connection verification
        
        FIXED: Better state checking and error handling
        """
        if not WEBSOCKET_AVAILABLE:
            return False

        # Check connection state with lock
        with self._connection_lock:
            if not self.ws_connected or not self._connection_ready:
                self.logger.warning("Not connected; cannot send")
                return False
            
            if not self.ws_app:
                self.logger.warning("WebSocket app not initialized")
                self.ws_connected = False
                self._connection_ready = False
                return False

        try:
            message = json.dumps(command)
            self.ws_app.send(message)
            self.logger.warudo(f"Sent: {message}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send command: {e}")
            self._last_error = e
            
            # Mark as disconnected
            with self._connection_lock:
                self.ws_connected = False
                self._connection_ready = False
                self._connection_event.clear()
            
            return False

    def queue_command(self, command: Dict):
        """Queue command for batch sending"""
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
                else:
                    # Connection failed, abort remaining
                    break
        return sent

    def get_available_commands(self) -> Dict[str, List[str]]:
        """Get available emotions and animations"""
        return {
            'emotions': self.available_emotions, 
            'animations': self.available_animations
        }

    def shutdown(self):
        """Clean shutdown"""
        self._shutdown_event.set()
        self._cleanup_connection()
        self.logger.warudo("WebSocket controller shutdown")


class WarudoManager:
    """High-level manager with fixed connection handling"""

    def __init__(self, websocket_url: str = "ws://127.0.0.1:19190", 
                agent_name: str = None,
                auto_connect: bool = True, timeout: float = 5.0):
        self.enabled = True
        self.logger = Logger()
        self.agent_name = (agent_name or "agent").lower()
        
        self.logger.warudo(f"[Warudo] Manager initializing for agent: {self.agent_name}")
        
        self.controller = WarudoWebSocketController(websocket_url, agent_name=self.agent_name)
        
        if auto_connect and WEBSOCKET_AVAILABLE:
            success = self.connect(timeout=timeout)
            if not success:
                self.logger.warning(
                    "[Warudo] Auto-connect failed - connection not ready"
                )
                
    def connect(self, timeout: float = 5.0) -> bool:
        """
        Connect to Warudo WebSocket
        
        Returns:
            True if connected successfully, False otherwise
        """
        success = self.controller.connect_websocket(timeout=timeout)
        
        if success:
            self.logger.warudo("Connected successfully")
        else:
            self.logger.warning("Connection failed")
        
        return success

    def send_emotion(self, emotion: str) -> bool:
        """
        Send emotion with validation
        
        Args:
            emotion: Emotion name
            
        Returns:
            True if sent successfully
        """
        if not self.enabled or not self.controller:
            return False
        
        if emotion not in self.controller.available_emotions:
            self.logger.warning(f"Unknown emotion: {emotion}")
            return False
        
        command = {"action": f"{self.agent_name}/emotion", "data": emotion}
        success = self.controller.send_websocket_command(command)
        
        if success:
            self.logger.warudo(f"Emotion set: {emotion}")
        else:
            self.logger.error(f"Failed to send emotion: {emotion}")
        
        return success

    def send_animation(self, animation: str) -> bool:
        """
        Send animation with validation
        
        Args:
            animation: Animation name
            
        Returns:
            True if sent successfully
        """
        if not self.enabled or not self.controller:
            return False
        
        if animation not in self.controller.available_animations:
            self.logger.warning(f"Unknown animation: {animation}")
            return False
        
        command = {"action": f"{self.agent_name}/animation", "data": animation}
        success = self.controller.send_websocket_command(command)
        
        if success:
            self.logger.warudo(f"Animation played: {animation}")
        else:
            self.logger.error(f"Failed to send animation: {animation}")
        
        return success

    def handle_command(self, command: str) -> bool:
        """Handle CLI commands"""
        cmd = command.lower().strip()
        
        if cmd == "/warudo_connect":
            return self.connect()
        
        elif cmd == "/warudo_test":
            if not self.controller.ws_connected:
                self.logger.warning("Not connected - connecting first...")
                if not self.connect():
                    return False
            
            test_commands = [
                ("emotion", "happy"), 
                ("animation", "wave"), 
                ("animation", "nod")
            ]
            
            for cmd_type, cmd_name in test_commands:
                if cmd_type == "emotion":
                    self.send_emotion(cmd_name)
                else:
                    self.send_animation(cmd_name)
                time.sleep(0.8)
            
            return True
        
        elif cmd == "/warudo_commands":
            cmds = self.controller.get_available_commands()
            self.logger.warudo(f"Emotions: {', '.join(cmds['emotions'])}")
            self.logger.warudo(f"Animations: {', '.join(cmds['animations'])}")
            return True
        
        elif cmd.startswith("/warudo_emotion "):
            return self.send_emotion(cmd.split(" ", 1)[1])
        
        elif cmd.startswith("/warudo_animation "):
            return self.send_animation(cmd.split(" ", 1)[1])
        
        return False


if __name__ == "__main__":
    if not WEBSOCKET_AVAILABLE:
        print(f"[Warning] WebSocket not available: {WEBSOCKET_ERROR}")
        print("\nFix:")
        print("  pip uninstall websocket")
        print("  pip install websocket-client")
    else:
        print("Testing Warudo connection...")
        wm = WarudoManager("ws://127.0.0.1:19190", agent_name="test")
        
        if wm.controller.ws_connected and wm.controller._connection_ready:
            print("[Confirmed] Connected successfully")
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
            
            print("\n[Confirmed] All tests completed")
        else:
            print("[Warning] Failed to connect")
            print("\nTroubleshooting:")
            print("1. Is Warudo running?")
            print("2. Is WebSocket server enabled in Warudo?")
            print("   (Settings -> Plugins -> WebSocket API)")
            print("3. Is port 19190 not blocked by firewall?")
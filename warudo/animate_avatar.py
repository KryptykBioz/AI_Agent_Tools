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
try:
    import websocket
except Exception:
    WEBSOCKET_AVAILABLE = False


class WarudoWebSocketController:
    """WebSocket controller with fixed race condition handling"""

    def __init__(self, websocket_url: str = "ws://127.0.0.1:19190"):
        self.websocket_url = websocket_url
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
        self._connection_ready = False  # NEW: Additional ready flag

        self.available_emotions = ['happy', 'angry', 'sad', 'relaxed', 'surprised']
        self.available_animations = [
            'nod', 'laugh', 'shrug', 'upset', 'wave', 'cat', 'confused', 
            'shy', 'swing', 'stretch', 'yay', 'taunt', 'bow', 'scare', 'refuse', 'snap'
        ]

    def _on_message(self, ws, message):
        """Handle incoming WebSocket message"""
        self.logger.warudo(f"Received: {message}")

    def _on_error(self, ws, error):
        """Handle WebSocket error"""
        self.logger.warudo(f"WebSocket error: {error}")
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
            self.logger.warning("websocket-client not available")
            return False

        # Check if already connected and verified
        with self._connection_lock:
            if self.ws_connected and self._connection_ready and self._connection_event.is_set():
                if self._connection_start_time:
                    age = time.time() - self._connection_start_time
                    if age < 300:  # Less than 5 minutes old
                        # Verify connection is still alive by checking thread
                        if self.ws_thread and self.ws_thread.is_alive():
                            return True
                
                # Connection might be stale - reconnect
                self.logger.warudo("Connection stale, reconnecting...")
                self._cleanup_connection_unsafe()  # Already have lock

        try:
            # Clear event before starting new connection
            self._connection_event.clear()
            
            # Clean up any existing connection
            self._cleanup_connection()
            
            # Reset ready flag
            with self._connection_lock:
                self._connection_ready = False
            
            # Create new WebSocket app
            self.ws_app = websocket.WebSocketApp(
                self.websocket_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )

            # Start connection thread
            self.ws_thread = threading.Thread(
                target=self._run_websocket,
                daemon=True,
                name="WarudoWebSocket"
            )
            self.ws_thread.start()

            # Wait for connection with timeout
            connected = self._connection_event.wait(timeout)
            
            if not connected:
                self.logger.warning(
                    f"[Warudo] Connection timeout after {timeout}s"
                )
                self._cleanup_connection()
                return False
            
            # CRITICAL: Additional verification after event fires
            # Give a small grace period for connection to stabilize
            time.sleep(0.1)
            
            with self._connection_lock:
                if not self.ws_connected or not self._connection_ready:
                    self.logger.warning("[Warudo] Connection event fired but state not ready")
                    self._cleanup_connection_unsafe()
                    return False
            
            # Final verification: thread should be alive
            if not self.ws_thread or not self.ws_thread.is_alive():
                self.logger.warning("[Warudo] Connection thread died unexpectedly")
                self._cleanup_connection()
                return False
            
            self.logger.warudo("[Warudo] Connection verified and ready")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start connection: {e}")
            self._last_error = e
            self._cleanup_connection()
            return False
    
    def _run_websocket(self):
        """Run WebSocket connection in thread"""
        try:
            self.ws_app.run_forever()
        except Exception as e:
            self.logger.error(f"WebSocket thread error: {e}")
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
                 auto_connect: bool = True, timeout: float = 5.0):
        self.enabled = True
        self.logger = Logger()
        
        self.controller = WarudoWebSocketController(websocket_url)
        
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
        
        command = {"action": "emotion", "data": emotion}
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
        
        command = {"action": "animation", "data": animation}
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
        print("websocket-client not available")
        print("Install with: pip install websocket-client")
    else:
        print("Testing Warudo connection...")
        wm = WarudoManager("ws://127.0.0.1:19190")
        
        if wm.controller.ws_connected and wm.controller._connection_ready:
            print("✓ Connected successfully")
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
            
            print("\n✓ All tests completed")
        else:
            print("✗ Failed to connect")
            print("\nTroubleshooting:")
            print("1. Is Warudo running?")
            print("2. Is WebSocket server enabled in Warudo?")
            print("   (Settings -> Plugins -> WebSocket API)")
            print("3. Is port 19190 not blocked by firewall?")
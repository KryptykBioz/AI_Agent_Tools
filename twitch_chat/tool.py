# Filename: BASE/tools/installed/twitch_chat/tool.py
"""
Twitch Chat Tool - FIXED Initialization Order
Thought buffer is now captured BEFORE monitor initialization
"""
from typing import List, Dict, Any, Optional, Callable
from BASE.handlers.base_tool import BaseTool
import time
import threading
import socket
from datetime import datetime
import re
import atexit
import weakref


_active_instances = weakref.WeakSet()
_initialization_lock = threading.Lock()


class TwitchChatMonitor:
    """Low-level Twitch IRC chat monitor with batch processing"""
    
    def __init__(
        self, 
        channel: str, 
        oauth_token: str = "",
        nickname: str = "",
        max_messages: int = 10,
        message_callback: Optional[Callable] = None,
        batch_callback: Optional[Callable] = None,
        batch_interval: float = 5.0,
        logger=None
    ):
        """Initialize Twitch IRC monitor with batch processing"""
        self.channel = channel.lower().strip().lstrip('#')
        self.oauth_token = oauth_token
        self.nickname = nickname if nickname else f"justinfan{int(time.time()) % 100000}"
        self.use_auth = bool(oauth_token and nickname)
        self.max_messages = max_messages
        self.message_callback = message_callback
        self.batch_callback = batch_callback
        self.batch_interval = batch_interval
        self.logger = logger
        
        # State
        self.running = False
        self.connected = False
        self.shutdown_flag = threading.Event()
        self.monitor_thread = None
        self.batch_thread = None
        
        # IRC connection
        self.server = "irc.chat.twitch.tv"
        self.port = 6667
        self.irc_socket = None
        
        # Message buffer
        self.chat_buffer: List[Dict] = []
        self.unbatched_messages: List[Dict] = []
        self.buffer_lock = threading.Lock()
        self.start_time = None
        
        _active_instances.add(self)
    
    def _parse_irc_message(self, message: str) -> Optional[Dict]:
        """Parse IRC message to extract username and text"""
        try:
            if message.startswith("PING"):
                return {"type": "ping", "data": message.split(":", 1)[1].strip()}
            
            if "PRIVMSG" in message:
                username_match = re.search(r':([^!]+)!', message)
                if not username_match:
                    return None
                username = username_match.group(1)
                
                if 'PRIVMSG' in message:
                    privmsg_part = message.split('PRIVMSG', 1)[1]
                    if ':' in privmsg_part:
                        text = privmsg_part.split(':', 1)[1].strip()
                    else:
                        return None
                else:
                    return None
                
                if ';' in text and ':' in text:
                    parts = text.rsplit(':', 1)
                    if len(parts) == 2:
                        potential_msg = parts[1].strip()
                        if '=' in parts[0] or ';' in parts[0]:
                            text = potential_msg
                
                return {
                    "type": "message",
                    "author": username,
                    "message": text
                }
            
            return None
        
        except Exception as e:
            if self.logger:
                self.logger.warning(f"[Twitch] IRC parse error: {e}")
            return None
    
    def start(self) -> bool:
        """Start monitoring Twitch chat"""
        with _initialization_lock:
            if self.running:
                return True
            
            for instance in list(_active_instances):
                if instance is not self and instance.running:
                    try:
                        instance._force_stop()
                    except:
                        pass
            
            try:
                self.irc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.irc_socket.settimeout(10.0)
                self.irc_socket.connect((self.server, self.port))
                
                if self.use_auth:
                    self.irc_socket.send(f"PASS {self.oauth_token}\r\n".encode('utf-8'))
                else:
                    self.irc_socket.send(b"PASS SCHMOOPIIE\r\n")
                
                self.irc_socket.send(f"NICK {self.nickname}\r\n".encode('utf-8'))
                time.sleep(1)
                
                self.irc_socket.send(b"CAP REQ :twitch.tv/tags twitch.tv/commands\r\n")
                self.irc_socket.send(f"JOIN #{self.channel}\r\n".encode('utf-8'))
                time.sleep(0.5)
                
                self.running = True
                self.shutdown_flag.clear()
                self.start_time = time.time()
                
                self.monitor_thread = threading.Thread(
                    target=self._monitor_loop,
                    daemon=True,
                    name=f"TwitchChat-{self.channel}"
                )
                self.monitor_thread.start()
                
                if self.batch_callback:
                    self.batch_thread = threading.Thread(
                        target=self._batch_processing_loop,
                        daemon=True,
                        name=f"TwitchBatch-{self.channel}"
                    )
                    self.batch_thread.start()
                
                if self.logger:
                    mode = "authenticated" if self.use_auth else "read-only"
                    batch_status = f"batching every {self.batch_interval}s" if self.batch_callback else "no batching"
                    self.logger.success(f"[Twitch] Connected to #{self.channel} ({mode}, {batch_status})")
                
                return True
            
            except Exception as e:
                if self.logger:
                    self.logger.error(f"[Twitch] Connection failed: {e}")
                self.running = False
                self._cleanup_resources()
                return False
    
    def _monitor_loop(self):
        """Main IRC monitoring loop"""
        buffer = ""
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        initial_timeout = time.time() + 5
        while time.time() < initial_timeout and not self.shutdown_flag.is_set():
            try:
                self.irc_socket.settimeout(1.0)
                data = self.irc_socket.recv(2048).decode('utf-8', errors='ignore')
                if data:
                    buffer += data
                    
                    while '\r\n' in buffer:
                        line, buffer = buffer.split('\r\n', 1)
                        
                        if line.startswith("PING"):
                            pong_data = line.split(":", 1)[1] if ":" in line else ""
                            self.irc_socket.send(f"PONG :{pong_data}\r\n".encode('utf-8'))
                        
                        if "001" in line or "JOIN" in line or "353" in line:
                            self.connected = True
                            break
                    
                    if self.connected:
                        break
            
            except socket.timeout:
                continue
            except Exception:
                break
        
        if not self.connected:
            if self.logger:
                self.logger.error("[Twitch] Connection timeout")
            self.running = False
            return
        
        buffer = ""
        while not self.shutdown_flag.is_set() and self.running:
            try:
                if not self.irc_socket:
                    break
                
                self.irc_socket.settimeout(1.0)
                try:
                    data = self.irc_socket.recv(2048).decode('utf-8', errors='ignore')
                except socket.timeout:
                    continue
                
                if not data:
                    break
                
                buffer += data
                
                while '\r\n' in buffer:
                    line, buffer = buffer.split('\r\n', 1)
                    
                    if not line.strip():
                        continue
                    
                    parsed = self._parse_irc_message(line)
                    
                    if parsed:
                        if parsed["type"] == "ping":
                            self.irc_socket.send(f"PONG :{parsed['data']}\r\n".encode('utf-8'))
                        
                        elif parsed["type"] == "message":
                            msg = {
                                'author': parsed['author'],
                                'message': parsed['message'],
                                'timestamp': int(time.time() * 1000),
                                'datetime': datetime.now(),
                                'user_id': parsed['author']
                            }
                            
                            with self.buffer_lock:
                                self.chat_buffer.append(msg)
                                if len(self.chat_buffer) > self.max_messages:
                                    self.chat_buffer = self.chat_buffer[-self.max_messages:]
                                
                                self.unbatched_messages.append(msg)
                            
                            if self.message_callback:
                                try:
                                    self.message_callback(msg)
                                except Exception as e:
                                    if self.logger:
                                        self.logger.error(f"[Twitch] Callback error: {e}")
                
                consecutive_errors = 0
            
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    if self.logger:
                        self.logger.error(f"[Twitch] Too many errors, disconnecting")
                    break
                time.sleep(min(2.0 ** consecutive_errors, 30.0))
        
        self.running = False
        self.connected = False
    
    def _batch_processing_loop(self):
        """Batch processing loop - sends accumulated messages periodically"""
        if self.logger:
            self.logger.system(f"[Twitch Batch] Started ({self.batch_interval}s interval)")
        
        while not self.shutdown_flag.is_set() and self.running:
            time.sleep(self.batch_interval)
            
            if not self.running:
                break
            
            with self.buffer_lock:
                messages_to_batch = self.unbatched_messages.copy()
                self.unbatched_messages.clear()
            
            if messages_to_batch and self.batch_callback:
                try:
                    self.batch_callback(messages_to_batch)
                    
                    if self.logger:
                        self.logger.tool(f"[Twitch Batch] Sent {len(messages_to_batch)} messages")
                
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"[Twitch Batch] Callback error: {e}")
        
        if self.logger:
            self.logger.system("[Twitch Batch] Stopped")
    
    def send_message(self, message: str) -> bool:
        """Send message to Twitch chat (requires auth)"""
        if not self.running or not self.connected or not self.use_auth:
            return False
        
        try:
            self.irc_socket.send(f"PRIVMSG #{self.channel} :{message}\r\n".encode('utf-8'))
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"[Twitch] Send failed: {e}")
            return False
    
    def get_recent_messages(self) -> List[Dict]:
        """Get recent messages (thread-safe)"""
        with self.buffer_lock:
            return self.chat_buffer.copy()
    
    def get_unbatched_count(self) -> int:
        """Get count of messages waiting to be batched"""
        with self.buffer_lock:
            return len(self.unbatched_messages)
    
    def _force_stop(self):
        """Force stop without locks"""
        self.running = False
        self.connected = False
        self.shutdown_flag.set()
        self._cleanup_resources()
    
    def stop(self):
        """Stop monitoring"""
        with _initialization_lock:
            if not self.running:
                return
            
            self.shutdown_flag.set()
            self.running = False
            self.connected = False
            
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=3.0)
            
            if self.batch_thread and self.batch_thread.is_alive():
                self.batch_thread.join(timeout=3.0)
            
            self._cleanup_resources()
    
    def _cleanup_resources(self):
        """Clean up IRC socket"""
        if self.irc_socket:
            try:
                self.irc_socket.send(f"PART #{self.channel}\r\n".encode('utf-8'))
                time.sleep(0.1)
                self.irc_socket.close()
            except:
                pass
            self.irc_socket = None
    
    def __del__(self):
        if self.running:
            self._force_stop()


class TwitchChatTool(BaseTool):
    """
    Twitch chat tool with batch processing
    FIXED: Proper initialization order ensures thought buffer is captured
    """
    
    @property
    def name(self) -> str:
        return "twitch_chat"
    
    async def start(self, thought_buffer=None, event_loop=None):
        """
        CRITICAL FIX: Override start() to capture thought_buffer FIRST
        This ensures _thought_buffer exists before initialize() is called
        """
        # CAPTURE THOUGHT BUFFER IMMEDIATELY
        self._thought_buffer = thought_buffer
        
        if self._logger and thought_buffer:
            self._logger.system("[Twitch] [SUCCESS] Thought buffer captured before initialization")
        elif self._logger:
            self._logger.warning("[Twitch] [WARNING] No thought buffer - batching will fail")
        
        # Now call parent start() which will call initialize()
        await super().start(thought_buffer, event_loop)
        
    async def initialize(self) -> bool:
        """
        Initialize Twitch chat monitoring
        NOTE: _thought_buffer is already set by start() override
        """
        try:
            from BASE.tools.installed.twitch_chat import config
            
            self.channel = getattr(config, 'TWITCH_CHANNEL', '')
            self.oauth_token = getattr(config, 'TWITCH_OAUTH_TOKEN', '')
            self.nickname = getattr(config, 'TWITCH_NICKNAME', '')
            self.max_context_messages = getattr(config, 'TWITCH_MAX_CONTEXT', 10)
            self.auto_start = getattr(config, 'TWITCH_AUTO_START', False)
            self.batch_interval = getattr(config, 'TWITCH_BATCH_INTERVAL', 5.0)
            self.enable_batching = getattr(config, 'TWITCH_ENABLE_BATCHING', True)
            
        except (ImportError, AttributeError) as e:
            if self._logger:
                self._logger.warning(f"[Twitch] Could not load config: {e}")
            self.channel = ''
            self.oauth_token = ''
            self.nickname = ''
            self.max_context_messages = 10
            self.auto_start = False
            self.batch_interval = 5.0
            self.enable_batching = True
        
        # State
        self.monitor: Optional[TwitchChatMonitor] = None
        self._message_callback = None
        # NOTE: _thought_buffer already set by start() override
        
        # VERIFY THOUGHT BUFFER EXISTS
        if not hasattr(self, '_thought_buffer') or not self._thought_buffer:
            if self._logger:
                self._logger.error(
                    "[Twitch] ✗ CRITICAL: No thought buffer at initialization time. "
                    "Batch processing will not work!"
                )
            return False
        
        if self._logger:
            self._logger.system("[Twitch] [SUCCESS] Thought buffer verified at initialization")
        
        # Initialize monitor if configured
        if self.channel:
            if self.auto_start:
                success = self._start_monitor()
                if self._logger:
                    if success:
                        mode = "authenticated" if self.oauth_token else "read-only"
                        batch_status = f"batching ({self.batch_interval}s)" if self.enable_batching else "no batching"
                        self._logger.success(f"[Twitch] Auto-started #{self.channel} ({mode}, {batch_status})")
                    else:
                        self._logger.warning(f"[Twitch] Auto-start failed for #{self.channel}")
            elif self._logger:
                self._logger.system(f"[Twitch] Initialized (channel: #{self.channel}, manual start)")
        elif self._logger:
            self._logger.warning("[Twitch] No channel configured")
        
        return True
        
    async def cleanup(self):
        """Cleanup Twitch resources"""
        if self.monitor:
            self.monitor.stop()
            self.monitor = None
        
        if self._logger:
            self._logger.system("[Twitch] Cleaned up")
    
    def is_available(self) -> bool:
        """Check if Twitch chat is available"""
        return bool(self.channel) and self.monitor is not None and self.monitor.running
    
    def _on_batch_messages(self, messages: List[Dict]):
        """
        Callback for batched messages
        Formats and injects into thought buffer
        """
        if not messages:
            return
        
        # VERIFY THOUGHT BUFFER
        if not self._thought_buffer:
            if self._logger:
                self._logger.error("[Twitch] Cannot ingest: No thought buffer")
            return
        
        # Format batch
        formatted_lines = []
        from personality.bot_info import botname
        bot_name_lower = botname.lower()
        has_bot_mention = False
        
        for msg in messages:
            author = msg['author']
            content = msg['message']
            
            if bot_name_lower in content.lower():
                has_bot_mention = True
                formatted_lines.append(f"@{author}: {content} [MENTIONED YOU]")
            else:
                formatted_lines.append(f"{author}: {content}")
        
        batch_text = (
            f"## TWITCH CHAT (#{self.channel})\n"
            f"{len(messages)} new messages:\n\n" +
            "\n".join(formatted_lines)
        )
        
        # INJECT INTO THOUGHT BUFFER
        try:
            source = 'chat_direct_mention' if has_bot_mention else 'chat_message'
            self._thought_buffer.ingest_raw_data(source, batch_text)
            
            if self._logger:
                mention_status = " [BOT MENTIONED]" if has_bot_mention else ""
                self._logger.tool(f"[Twitch] [SUCCESS] Batch ingested: {len(messages)} messages{mention_status}")
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Twitch] Failed to ingest: {e}")
                import traceback
                traceback.print_exc()
    
    def _start_monitor(self) -> bool:
        """Start Twitch chat monitoring"""
        if self.monitor:
            self.monitor.stop()
            time.sleep(0.5)
        
        if not self.channel:
            if self._logger:
                self._logger.error("[Twitch] Cannot start: No channel")
            return False
        
        # VERIFY THOUGHT BUFFER BEFORE CREATING MONITOR
        if self.enable_batching and not self._thought_buffer:
            if self._logger:
                self._logger.error(
                    "[Twitch] ✗ Cannot start with batching: No thought buffer. "
                    "Disable batching or ensure thought buffer is injected."
                )
            return False
        
        try:
            # Create batch callback ONLY if thought buffer exists
            batch_callback = self._on_batch_messages if (self.enable_batching and self._thought_buffer) else None
            
            if self._logger:
                if batch_callback:
                    self._logger.system("[Twitch] [SUCCESS] Batch callback enabled")
                else:
                    self._logger.system("[Twitch] Batch callback disabled")
            
            self.monitor = TwitchChatMonitor(
                channel=self.channel,
                oauth_token=self.oauth_token,
                nickname=self.nickname,
                max_messages=self.max_context_messages,
                message_callback=self._on_new_message,
                batch_callback=batch_callback,
                batch_interval=self.batch_interval,
                logger=self._logger
            )
            
            success = self.monitor.start()
            
            if not success and self._logger:
                self._logger.error("[Twitch] Failed to start")
            
            return success
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Twitch] Start error: {e}")
                import traceback
                traceback.print_exc()
            self.monitor = None
            return False
    
    def _on_new_message(self, message: Dict):
        """Internal callback for individual messages"""
        if self._message_callback:
            try:
                self._message_callback(message)
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[Twitch] Callback error: {e}")
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute Twitch command
        
        Commands:
        - start: Start monitoring
        - stop: Stop monitoring  
        - send_message: Send message (requires OAuth)
        - get_context: Get conversation context
        """
        if self._logger:
            self._logger.tool(f"[Twitch] Command: '{command}', args: {args}")
        
        if command == 'start':
            return await self._handle_start()
        elif command == 'stop':
            return await self._handle_stop()
        elif command == 'send_message' or command == '':
            return await self._handle_send_message(args)
        elif command == 'get_context':
            return await self._handle_get_context()
        else:
            return self._error_result(
                f'Unknown command: {command}',
                guidance='Available: start, stop, send_message, get_context'
            )
    
    async def _handle_start(self) -> Dict[str, Any]:
        """Handle start command"""
        if self.is_available():
            return self._success_result(
                f'Already monitoring #{self.channel}',
                metadata={'channel': self.channel}
            )
        
        success = self._start_monitor()
        
        if success:
            mode = "authenticated" if self.oauth_token else "read-only"
            return self._success_result(
                f'Started monitoring #{self.channel}',
                metadata={
                    'channel': self.channel,
                    'mode': mode,
                    'batching': self.enable_batching,
                    'batch_interval': self.batch_interval
                }
            )
        else:
            return self._error_result('Failed to start')
    
    async def _handle_stop(self) -> Dict[str, Any]:
        """Handle stop command"""
        if self.monitor:
            self.monitor.stop()
            self.monitor = None
            return self._success_result('Stopped')
        else:
            return self._success_result('Not running')
    
    async def _handle_send_message(self, args: List[Any]) -> Dict[str, Any]:
        """Handle send_message command"""
        if not self.is_available():
            return self._error_result('Not connected')
        
        if not args:
            return self._error_result('No message provided')
        
        message = str(args[0])
        
        if not self.oauth_token:
            return self._error_result('Read-only mode (no OAuth)')
        
        success = self.monitor.send_message(message)
        
        if success:
            return self._success_result(f'Sent to #{self.channel}')
        else:
            return self._error_result('Failed to send')
    
    async def _handle_get_context(self) -> Dict[str, Any]:
        """Handle get_context command"""
        if not self.is_available():
            return self._error_result('Not connected')
        
        context = self.get_context_for_ai()
        return self._success_result(context if context else 'No context')
    
    def get_context_for_ai(self) -> str:
        """Get formatted context for AI"""
        if not self.monitor or not self.monitor.chat_buffer:
            return ""
        
        lines = [f"{msg['author']}: {msg['message']}" for msg in self.monitor.chat_buffer]
        return "\n".join(lines)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status"""
        status = {
            'available': self.is_available(),
            'channel': self.channel,
            'mode': 'authenticated' if self.oauth_token else 'read-only',
            'connected': False,
            'batching_enabled': self.enable_batching,
            'batch_interval': self.batch_interval,
            'thought_buffer_connected': bool(getattr(self, '_thought_buffer', None)),
            'batch_callback_active': False
        }
        
        if self.monitor and self.monitor.running:
            status['connected'] = True
            status['uptime'] = time.time() - self.monitor.start_time if self.monitor.start_time else 0
            status['buffered'] = len(self.monitor.chat_buffer)
            status['unbatched'] = self.monitor.get_unbatched_count()
            status['batch_callback_active'] = bool(self.monitor.batch_callback)
        
        return status


def cleanup_all_instances():
    """Clean up all IRC instances"""
    for instance in list(_active_instances):
        try:
            if instance.running:
                instance._force_stop()
        except:
            pass


atexit.register(cleanup_all_instances)
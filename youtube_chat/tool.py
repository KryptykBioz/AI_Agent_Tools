# Filename: BASE/tools/installed/youtube_chat/tool.py
"""
YouTube Chat Tool - Simplified Architecture
Single master class for monitoring YouTube live chat
Monitor-only mode using YouTube's internal API with continuation tokens
"""
from typing import List, Dict, Any, Optional, Callable
from BASE.handlers.base_tool import BaseTool
import time
import threading
import requests
from datetime import datetime
import re
import atexit
import weakref


# Track active instances for cleanup
_active_instances = weakref.WeakSet()
_initialization_lock = threading.Lock()


class YouTubeChatMonitor:
    """Low-level YouTube chat monitor using continuation tokens"""
    
    def __init__(
        self,
        video_id: str,
        max_messages: int = 10,
        message_callback: Optional[Callable] = None,
        logger=None
    ):
        """Initialize YouTube chat monitor"""
        self.video_id = video_id
        self.max_messages = max_messages
        self.message_callback = message_callback
        self.logger = logger
        
        # State
        self.running = False
        self.shutdown_flag = threading.Event()
        self.monitor_thread = None
        self.start_time = None
        
        # API state
        self.live_chat_id = None
        self.next_page_token = None
        self.polling_interval = 2.0
        self.session = None
        
        # Message buffer
        self.chat_buffer: List[Dict] = []
        
        _active_instances.add(self)
    
    def _extract_live_chat_id(self) -> Optional[str]:
        """Extract live chat continuation token from video page"""
        try:
            url = f"https://www.youtube.com/watch?v={self.video_id}"
            if self.logger:
                self.logger.tool(f"[YouTube] Fetching video page: {self.video_id}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Look for liveChatRenderer continuation token
            patterns = [
                r'"liveChatRenderer":\{"continuations":\[\{"reloadContinuationData":\{"continuation":"([^"]+)"',
                r'"conversationBar":\{"liveChatRenderer":\{"continuations":\[\{"reloadContinuationData":\{"continuation":"([^"]+)"',
                r'continuation":"([A-Za-z0-9_-]{100,})"'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    continuation = match.group(1)
                    if self.logger:
                        self.logger.success("[YouTube] Found live chat continuation token")
                    return continuation
            
            if self.logger:
                self.logger.error("[YouTube] Could not find live chat - stream may not be live or chat disabled")
            return None
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"[YouTube] Error extracting chat ID: {e}")
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
            
            # Extract messages
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
                    timestamp_usec = text_message.get("timestampUsec", str(int(time.time() * 1000000)))
                    timestamp = int(timestamp_usec) // 1000
                    author_id = text_message.get("authorExternalChannelId", author)
                    
                    messages.append({
                        'author': author,
                        'message': message_text,
                        'timestamp': timestamp,
                        'datetime': datetime.fromtimestamp(timestamp / 1000),
                        'user_id': author_id
                    })
            
            # Get next continuation token
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
        
        except requests.exceptions.RequestException:
            return []
        except Exception as e:
            if self.logger:
                self.logger.warning(f"[YouTube] Error parsing messages: {e}")
            return []
    
    def start(self) -> bool:
        """Start monitoring YouTube live chat"""
        with _initialization_lock:
            if self.running:
                return True
            
            # Stop other instances
            for instance in list(_active_instances):
                if instance is not self and instance.running:
                    try:
                        instance._force_stop()
                    except:
                        pass
            
            try:
                self.session = requests.Session()
                self.session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                })
                
                self.live_chat_id = self._extract_live_chat_id()
                if not self.live_chat_id:
                    return False
                
                self.running = True
                self.shutdown_flag.clear()
                self.start_time = time.time()
                
                self.monitor_thread = threading.Thread(
                    target=self._monitor_loop,
                    daemon=True,
                    name=f"YouTubeChat-{self.video_id}"
                )
                self.monitor_thread.start()
                
                if self.logger:
                    self.logger.success(f"[YouTube] Started monitoring (poll: {self.polling_interval}s)")
                
                return True
            
            except Exception as e:
                if self.logger:
                    self.logger.error(f"[YouTube] Start failed: {e}")
                self.running = False
                self._cleanup_resources()
                return False
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        consecutive_errors = 0
        max_consecutive_errors = 10
        message_count = 0
        first_message_logged = False
        
        while not self.shutdown_flag.is_set():
            try:
                if not self.live_chat_id:
                    break
                
                messages = self._fetch_chat_messages()
                
                if messages:
                    for msg in messages:
                        message_count += 1
                        
                        self.chat_buffer.append(msg)
                        if len(self.chat_buffer) > self.max_messages:
                            self.chat_buffer = self.chat_buffer[-self.max_messages:]
                        
                        if not first_message_logged:
                            if self.logger:
                                self.logger.success(
                                    f"[YouTube] Receiving messages: "
                                    f"{msg['author']}: {msg['message'][:50]}..."
                                )
                            first_message_logged = True
                        
                        if self.message_callback:
                            try:
                                self.message_callback(msg)
                            except Exception as e:
                                if self.logger:
                                    self.logger.error(f"[YouTube] Callback error: {e}")
                    
                    consecutive_errors = 0
                
                time.sleep(self.polling_interval)
            
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    if self.logger:
                        self.logger.error("[YouTube] Too many errors, stopping")
                    break
                time.sleep(min(2.0 ** consecutive_errors, 30.0))
        
        self.running = False
    
    def _force_stop(self):
        """Force stop without locks"""
        self.running = False
        self.shutdown_flag.set()
        self._cleanup_resources()
    
    def stop(self):
        """Stop monitoring"""
        with _initialization_lock:
            if not self.running:
                return
            
            self.shutdown_flag.set()
            self.running = False
            
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=3.0)
            
            self._cleanup_resources()
    
    def _cleanup_resources(self):
        """Clean up session"""
        if self.session:
            try:
                self.session.close()
            except:
                pass
            self.session = None
    
    def get_recent_messages(self) -> List[Dict]:
        """Get recent messages from buffer"""
        return self.chat_buffer.copy()
    
    def __del__(self):
        if self.running:
            self._force_stop()


class YouTubeChatTool(BaseTool):
    """
    YouTube chat tool for monitoring live chat
    Monitor-only mode - cannot send messages (YouTube API restriction)
    """
    
    @property
    def name(self) -> str:
        return "youtube_chat"
    
    async def initialize(self) -> bool:
        """Initialize YouTube chat monitoring"""
        # Load configuration from config file
        try:
            from BASE.tools.installed.youtube_chat import config
            
            self.video_id = getattr(config, 'YOUTUBE_VIDEO_ID', '')
            self.max_context_messages = getattr(config, 'YOUTUBE_MAX_CONTEXT', 10)
            self.auto_start = getattr(config, 'YOUTUBE_AUTO_START', False)
        except (ImportError, AttributeError) as e:
            if self._logger:
                self._logger.warning(f"[YouTube] Could not load config: {e}")
            self.video_id = ''
            self.max_context_messages = 10
            self.auto_start = False
        
        # State
        self.monitor: Optional[YouTubeChatMonitor] = None
        self._last_start_attempt = 0.0
        self._message_callback = None
        
        # Initialize monitor if configured
        if self.video_id and self.auto_start:
            success = self._start_monitor()
            if self._logger:
                if success:
                    self._logger.system(f"[YouTube] Auto-started for video: {self.video_id}")
                else:
                    self._logger.warning(f"[YouTube] Auto-start failed for video: {self.video_id}")
        elif self._logger:
            if not self.video_id:
                self._logger.warning("[YouTube] No video ID configured")
            else:
                self._logger.system(f"[YouTube] Initialized (video: {self.video_id}, manual start)")
        
        return True  # Always return True for graceful degradation
    
    async def cleanup(self):
        """Cleanup YouTube resources"""
        if self.monitor:
            self.monitor.stop()
            self.monitor = None
        
        if self._logger:
            self._logger.system("[YouTube] Cleaned up")
    
    def is_available(self) -> bool:
        """Check if YouTube chat is available"""
        return bool(self.video_id) and self.monitor is not None and self.monitor.running
    
    def _start_monitor(self) -> bool:
        """Start YouTube chat monitoring"""
        current_time = time.time()
        
        # Rate limit start attempts
        if current_time - self._last_start_attempt < 3.0:
            if self._logger:
                self._logger.warning("[YouTube] Too soon since last start attempt")
            return False
        
        self._last_start_attempt = current_time
        
        if self.monitor:
            self.monitor.stop()
            time.sleep(0.5)
        
        if not self.video_id:
            if self._logger:
                self._logger.error("[YouTube] Cannot start: No video ID configured")
            return False
        
        try:
            self.monitor = YouTubeChatMonitor(
                video_id=self.video_id,
                max_messages=self.max_context_messages,
                message_callback=self._on_new_message,
                logger=self._logger
            )
            
            success = self.monitor.start()
            
            if not success and self._logger:
                self._logger.error("[YouTube] Failed to start monitoring")
            
            return success
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[YouTube] Start error: {e}")
            self.monitor = None
            return False
    
    def _on_new_message(self, message: Dict):
        """Internal callback for new messages"""
        if self._message_callback:
            try:
                self._message_callback(message)
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[YouTube] Callback error: {e}")
    
    def set_message_callback(self, callback: Callable):
        """Set callback for incoming messages"""
        self._message_callback = callback
        if self._logger:
            self._logger.tool("[YouTube] Message callback registered")
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute YouTube chat command
        
        Commands:
        - start: Start monitoring
        - stop: Stop monitoring
        - get_context: Get conversation context
        - send_message: Not supported (YouTube API restriction)
        
        Args:
            command: Command name
            args: Command arguments
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[YouTube] Command: '{command}', args: {args}")
        
        # Route commands
        if command == 'start':
            return await self._handle_start()
        elif command == 'stop':
            return await self._handle_stop()
        elif command == 'get_context':
            return await self._handle_get_context()
        elif command == 'send_message' or command == '':
            return self._error_result(
                'YouTube does not support bot message sending via API',
                metadata={'mode': 'monitor-only'},
                guidance='YouTube chat is monitor-only. Cannot send messages.'
            )
        else:
            return self._error_result(
                f'Unknown command: {command}',
                guidance='Available commands: start, stop, get_context'
            )
    
    async def _handle_start(self) -> Dict[str, Any]:
        """Handle start command"""
        if self.is_available():
            return self._success_result(
                'Already monitoring YouTube chat',
                metadata={'video_id': self.video_id}
            )
        
        success = self._start_monitor()
        
        if success:
            return self._success_result(
                f'Started monitoring YouTube chat',
                metadata={
                    'video_id': self.video_id,
                    'polling_interval': self.monitor.polling_interval
                }
            )
        else:
            return self._error_result(
                'Failed to start YouTube chat monitor',
                guidance='Check video ID and ensure stream is live with chat enabled'
            )
    
    async def _handle_stop(self) -> Dict[str, Any]:
        """Handle stop command"""
        if self.monitor:
            self.monitor.stop()
            self.monitor = None
            return self._success_result('Stopped YouTube chat monitoring')
        else:
            return self._success_result('YouTube chat was not running')
    
    async def _handle_get_context(self) -> Dict[str, Any]:
        """Handle get_context command"""
        if not self.is_available():
            return self._error_result(
                'YouTube chat is not connected',
                guidance='Start monitoring first with youtube_chat.start'
            )
        
        context = self.get_context_for_ai()
        
        return self._success_result(
            context if context else 'No conversation context available',
            metadata={'context_messages': len(self.monitor.chat_buffer)}
        )
    
    def get_context_for_ai(self) -> str:
        """Get formatted context for AI"""
        if not self.monitor or not self.monitor.chat_buffer:
            return ""
        
        context_lines = []
        for msg in self.monitor.chat_buffer:
            author = msg['author']
            content = msg['message']
            context_lines.append(f"{author}: {content}")
        
        return "\n".join(context_lines)
    
    def get_status(self) -> Dict[str, Any]:
        """Get YouTube chat status (for debugging/monitoring)"""
        status = {
            'available': self.is_available(),
            'video_id': self.video_id,
            'mode': 'monitor-only',
            'connected': False,
            'uptime_seconds': 0,
            'buffered_messages': 0,
            'polling_interval': 0.0
        }
        
        if self.monitor and self.monitor.running:
            status['connected'] = True
            status['uptime_seconds'] = time.time() - self.monitor.start_time if self.monitor.start_time else 0
            status['buffered_messages'] = len(self.monitor.chat_buffer)
            status['polling_interval'] = self.monitor.polling_interval
        
        return status


def cleanup_all_instances():
    """Clean up all active monitor instances"""
    for instance in list(_active_instances):
        try:
            if instance.running:
                instance._force_stop()
        except:
            pass


atexit.register(cleanup_all_instances)
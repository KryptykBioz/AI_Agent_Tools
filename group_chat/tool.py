# Filename: BASE/tools/installed/group_chat/tool.py
"""
Group Chat Tool - Agent-to-Agent Communication
Enables multiple agent instances to share their spoken responses
FIXED: Removed self-filtering, improved discovery, added connection verification
"""
import asyncio
import socket
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

base_path = Path(__file__).parent.parent.parent.parent
if str(base_path) not in sys.path:
    sys.path.insert(0, str(base_path))

from BASE.handlers.base_tool import BaseTool
from personality.bot_info import agentname


class GroupChatTool(BaseTool):
    """
    Agent-to-agent group chat via local network sockets
    Broadcasts spoken responses to other agents on same device
    """
    
    __slots__ = (
        '_server', '_server_task', '_clients', '_port', '_host',
        '_agent_name', '_message_queue', '_last_broadcast_time',
        '_connected_ports', '_discovery_lock'
    )
    
    def __init__(self, config, controls, logger=None):
        super().__init__(config, controls, logger)
        
        self._server = None
        self._server_task = None
        self._clients: List[tuple] = []
        
        # Import port from bot_info.py if available, else use config module default
        try:
            from personality.bot_info import group_chat_port
            self._port = group_chat_port
        except ImportError:
            try:
                from BASE.tools.installed.group_chat import config as tool_config
                self._port = getattr(tool_config, 'GROUP_CHAT_PORT', 54321)
            except:
                self._port = 54321
        
        # Import host from config module
        try:
            from BASE.tools.installed.group_chat import config as tool_config
            self._host = getattr(tool_config, 'GROUP_CHAT_HOST', '127.0.0.1')
        except:
            self._host = '127.0.0.1'
        
        self._agent_name = agentname
        
        self._message_queue = asyncio.Queue()
        self._last_broadcast_time = 0.0
        self._connected_ports = set()
        self._discovery_lock = asyncio.Lock()
    
    @property
    def name(self) -> str:
        return "group_chat"
    
    async def initialize(self) -> bool:
        """Start server and connect to other agents"""
        try:
            if self._logger:
                self._logger.system(
                    f"[{self.name}] Initializing on port {self._port} as agent '{self._agent_name}'"
                )
            
            # Start server
            self._server = await asyncio.start_server(
                self._handle_client_connection,
                self._host,
                self._port
            )
            
            if self._logger:
                self._logger.success(
                    f"[{self.name}] Server started on {self._host}:{self._port}"
                )
            
            # Initial discovery attempts with delays
            await asyncio.sleep(0.2)  # Let server fully start
            await self._discover_peers()
            
            await asyncio.sleep(0.5)  # Wait for simultaneous agents
            await self._discover_peers()
            
            return True
            
        except OSError as e:
            if e.errno == 48 or e.errno == 98:
                if self._logger:
                    self._logger.warning(
                        f"[{self.name}] Port {self._port} in use, connecting as client only"
                    )
                await self._discover_peers()
                return True
            else:
                if self._logger:
                    self._logger.error(f"[{self.name}] Failed to start server: {e}")
                return False
        except Exception as e:
            if self._logger:
                self._logger.error(f"[{self.name}] Initialization error: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup connections and server"""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            if self._logger:
                self._logger.system(f"[{self.name}] Server closed")
        
        for reader, writer in self._clients:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
        
        self._clients.clear()
        self._connected_ports.clear()
    
    def is_available(self) -> bool:
        """Check if tool is ready - server OR clients exist"""
        has_server = self._server is not None
        has_clients = len(self._clients) > 0
        
        if self._logger and not (has_server or has_clients):
            self._logger.warning(
                f"[{self.name}] Not available: server={has_server}, "
                f"clients={len(self._clients)}"
            )
        
        return has_server or has_clients
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute group chat commands
        
        Commands:
        - broadcast: Send message to all connected agents
        - get_messages: Get pending messages from queue
        """
        try:
            if command == 'broadcast':
                if not args:
                    return self._error_result("No message provided")
                
                message = str(args[0])
                success = await self._broadcast_message(message)
                
                if success:
                    return self._success_result(
                        f"Broadcast to {len(self._clients)} agent(s)",
                        metadata={'recipients': len(self._clients)}
                    )
                else:
                    return self._error_result("Broadcast failed")
            
            elif command == 'get_messages':
                messages = []
                while not self._message_queue.empty():
                    try:
                        messages.append(self._message_queue.get_nowait())
                    except:
                        break
                
                return self._success_result(
                    f"Retrieved {len(messages)} message(s)",
                    metadata={'messages': messages, 'count': len(messages)}
                )
            
            else:
                return self._error_result(
                    f"Unknown command: {command}",
                    guidance="Available: broadcast, get_messages"
                )
        
        except Exception as e:
            return self._error_result(
                f"Execution error: {e}",
                metadata={'error': str(e)}
            )
    
    def has_context_loop(self) -> bool:
        """Enable background loop for message injection"""
        return True
    
    async def context_loop(self, thought_buffer):
        """Inject received messages into thought buffer - FIXED: No self-filtering"""
        last_discovery = 0.0
        startup_time = time.time()
        
        while self._running:
            try:
                current_time = time.time()
                
                # Aggressive discovery for first 30 seconds
                time_since_start = current_time - startup_time
                if time_since_start < 30.0:
                    discovery_interval = 5.0
                else:
                    discovery_interval = 30.0
                
                # Periodic peer rediscovery
                if current_time - last_discovery >= discovery_interval:
                    await self._discover_peers()
                    last_discovery = current_time
                
                # Process incoming messages
                if not self._message_queue.empty():
                    message_data = await self._message_queue.get()
                    
                    sender = message_data.get('agent', 'Unknown')
                    content = message_data.get('message', '')
                    
                    # CRITICAL: Filter out own messages
                    if sender != self._agent_name and content:
                        thought_buffer.add_processed_thought(
                            content=f"{sender} said: {content}",
                            source='group_chat',
                        )
                        
                        if self._logger:
                            self._logger.system(
                                f"[{self.name}] Injected from {sender}: {content[:60]}..."
                            )
                
                await asyncio.sleep(0.5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[{self.name}] Context loop error: {e}")
                await asyncio.sleep(1.0)
    
    async def _discover_peers(self):
        """Attempt connections to other agents on nearby ports"""
        async with self._discovery_lock:
            base_port = self._port
            new_connections = 0
            
            for offset in range(-5, 6):
                if offset == 0:
                    continue
                
                port = base_port + offset
                
                # Skip if already connected
                if port in self._connected_ports:
                    continue
                
                try:
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(self._host, port),
                        timeout=0.5
                    )
                    
                    # CRITICAL FIX: Add to list BEFORE tracking port
                    self._clients.append((reader, writer))
                    self._connected_ports.add(port)
                    new_connections += 1
                    
                    # Start listener
                    asyncio.create_task(self._listen_to_peer(reader, writer, port))
                    
                    if self._logger:
                        self._logger.system(
                            f"[{self.name}] Connected to peer on port {port}"
                        )
                    
                except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                    pass
                except Exception as e:
                    if self._logger:
                        self._logger.warning(
                            f"[{self.name}] Peer discovery error on {port}: {e}"
                        )
            
            # CRITICAL FIX: Log ACTUAL client count
            if self._logger:
                if new_connections > 0:
                    self._logger.success(
                        f"[{self.name}] Discovery: {new_connections} new, "
                        f"{len(self._clients)} total, "
                        f"ports: {sorted(list(self._connected_ports))}"
                    )
                else:
                    self._logger.system(
                        f"[{self.name}] Discovery: no new peers, "
                        f"{len(self._clients)} total active"
                    )
    
    async def _handle_client_connection(self, reader, writer):
        """Handle incoming client connection"""
        addr = writer.get_extra_info('peername')
        
        # CRITICAL FIX: Add to list immediately
        self._clients.append((reader, writer))
        
        if self._logger:
            self._logger.system(
                f"[{self.name}] New connection from {addr}, "
                f"total clients: {len(self._clients)}"
            )
        
        # Track port if available
        if addr and len(addr) > 1:
            self._connected_ports.add(addr[1])
        
        await self._listen_to_peer(reader, writer, addr[1] if addr else None)
    
    async def _listen_to_peer(self, reader, writer, port=None):
        """Listen for messages from a peer"""
        try:
            while self._running:
                data = await reader.readline()
                
                if not data:
                    break
                
                try:
                    message_data = json.loads(data.decode('utf-8'))
                    
                    # CRITICAL FIX: Don't filter by sender here
                    # Let the broadcast method handle filtering
                    await self._message_queue.put(message_data)
                
                except json.JSONDecodeError:
                    if self._logger:
                        self._logger.warning(
                            f"[{self.name}] Invalid JSON received"
                        )
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self._logger:
                self._logger.warning(f"[{self.name}] Peer listener error: {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
            
            if (reader, writer) in self._clients:
                self._clients.remove((reader, writer))
            
            if port:
                self._connected_ports.discard(port)
    
    async def _broadcast_message(self, message: str) -> bool:
        """Broadcast message to all connected peers"""
        if not self._clients:
            return False
        
        message_data = {
            'agent': self._agent_name,
            'message': message,
            'timestamp': time.time()
        }
        
        message_json = json.dumps(message_data) + '\n'
        message_bytes = message_json.encode('utf-8')
        
        dead_clients = []
        sent_count = 0
        
        for reader, writer in self._clients:
            try:
                writer.write(message_bytes)
                await writer.drain()
                sent_count += 1
            except Exception as e:
                if self._logger:
                    self._logger.warning(
                        f"[{self.name}] Failed to send to peer: {e}"
                    )
                dead_clients.append((reader, writer))
        
        for client in dead_clients:
            if client in self._clients:
                self._clients.remove(client)
        
        self._last_broadcast_time = time.time()
        
        return sent_count > 0
    
    def broadcast_spoken_response(self, response: str) -> bool:
        """
        Synchronous wrapper for broadcasting spoken response
        Called by AI Core after generating response
        FIXED: Better error messages and verification
        """
        if not self._running:
            if self._logger:
                self._logger.warning(
                    f"[{self.name}] Cannot broadcast - tool not running"
                )
            return False
        
        if not response or not response.strip():
            return False
        
        if not self._clients:
            if self._logger:
                self._logger.warning(
                    f"[{self.name}] No peer connections - broadcast skipped"
                )
            return False
        
        try:
            loop = asyncio.get_event_loop()
            
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self._broadcast_message(response), 
                    loop
                )
                # Wait briefly to verify send
                result = future.result(timeout=1.0)
                
                if result and self._logger:
                    self._logger.success(
                        f"[{self.name}] Broadcast sent to {len(self._clients)} peer(s)"
                    )
                
                return result
            else:
                result = loop.run_until_complete(self._broadcast_message(response))
                
                if result and self._logger:
                    self._logger.success(
                        f"[{self.name}] Broadcast sent to {len(self._clients)} peer(s)"
                    )
                
                return result
        except Exception as e:
            if self._logger:
                self._logger.error(f"[{self.name}] Broadcast error: {e}")
            return False
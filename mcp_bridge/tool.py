# Filename: BASE/tools/installed/mcp_bridge/tool.py
"""
MCP Bridge Tool - Model Context Protocol Integration
Allows the agent to interact with external MCP servers
Supports dynamic server discovery and tool execution
"""
from typing import List, Dict, Any, Optional
import asyncio
import json
import subprocess
import sys
from pathlib import Path

from BASE.handlers.base_tool import BaseTool


class MCPBridgeTool(BaseTool):
    """
    Bridge to Model Context Protocol servers
    
    Enables agent to:
    - Connect to MCP servers (stdio transport)
    - Discover available tools from servers
    - Execute tool calls through MCP
    - Manage server lifecycle
    """
    
    def __init__(self, config, controls, logger=None):
        super().__init__(config, controls, logger)
        
        # MCP server registry
        self._servers: Dict[str, 'MCPServer'] = {}
        
        # Server configuration directory
        self._config_dir = Path.home() / '.mcp' / 'servers'
        
        # Available tools from all servers
        self._available_tools: Dict[str, Dict] = {}
        
        # Connection status
        self._initialized = False
    
    @property
    def name(self) -> str:
        return "mcp_bridge"
    
    async def initialize(self) -> bool:
        """Initialize MCP bridge and discover servers"""
        try:
            # Create config directory if needed
            self._config_dir.mkdir(parents=True, exist_ok=True)
            
            # Load server configurations
            await self._load_server_configs()
            
            # Connect to configured servers
            await self._connect_servers()
            
            self._initialized = True
            
            if self._logger:
                server_count = len(self._servers)
                tool_count = len(self._available_tools)
                self._logger.success(
                    f"[{self.name}] Initialized: {server_count} servers, "
                    f"{tool_count} tools available"
                )
            
            return True
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[{self.name}] Initialization failed: {e}")
            return False
    
    async def cleanup(self):
        """Disconnect from all MCP servers"""
        if self._servers:
            if self._logger:
                self._logger.system(f"[{self.name}] Disconnecting from {len(self._servers)} servers")
            
            for server_name, server in list(self._servers.items()):
                try:
                    await server.disconnect()
                except Exception as e:
                    if self._logger:
                        self._logger.warning(f"[{self.name}] Error disconnecting {server_name}: {e}")
            
            self._servers.clear()
            self._available_tools.clear()
        
        self._initialized = False
    
    def is_available(self) -> bool:
        """Check if bridge is ready"""
        return self._initialized and len(self._servers) > 0
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute MCP bridge commands
        
        Commands:
        - list_servers: Get all connected servers
        - list_tools: Get all available MCP tools
        - call_tool: Execute an MCP tool
        - add_server: Connect to new MCP server
        - remove_server: Disconnect from server
        """
        if not self.is_available():
            return self._error_result(
                "MCP bridge not initialized",
                guidance="Check MCP server configuration"
            )
        
        try:
            if command == 'list_servers':
                return await self._list_servers()
            
            elif command == 'list_tools':
                return await self._list_tools()
            
            elif command == 'call_tool':
                if len(args) < 2:
                    return self._error_result(
                        "call_tool requires: tool_name, arguments_dict",
                        guidance="Example: ['filesystem.read_file', {'path': 'file.txt'}]"
                    )
                
                tool_name = args[0]
                tool_args = args[1] if len(args) > 1 else {}
                
                return await self._call_tool(tool_name, tool_args)
            
            elif command == 'add_server':
                if len(args) < 2:
                    return self._error_result(
                        "add_server requires: server_name, command",
                        guidance="Example: ['myserver', 'npx -y @modelcontextprotocol/server-everything']"
                    )
                
                server_name = args[0]
                server_command = args[1]
                server_args = args[2] if len(args) > 2 else []
                
                return await self._add_server(server_name, server_command, server_args)
            
            elif command == 'remove_server':
                if len(args) < 1:
                    return self._error_result(
                        "remove_server requires: server_name",
                        guidance="Example: ['myserver']"
                    )
                
                server_name = args[0]
                return await self._remove_server(server_name)
            
            else:
                return self._error_result(
                    f"Unknown command: {command}",
                    guidance="Available: list_servers, list_tools, call_tool, add_server, remove_server"
                )
        
        except Exception as e:
            return self._error_result(
                f"Command execution failed: {e}",
                metadata={'command': command, 'args': args}
            )
    
    # ========================================================================
    # SERVER MANAGEMENT
    # ========================================================================
    
    async def _load_server_configs(self):
        """Load server configurations from config directory"""
        config_file = self._config_dir / 'config.json'
        
        if not config_file.exists():
            # Create default config
            default_config = {
                "servers": {
                    "filesystem": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-filesystem", str(Path.home())]
                    }
                }
            }
            
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            if self._logger:
                self._logger.system(f"[{self.name}] Created default config: {config_file}")
        
        # Load configuration
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            self._server_configs = config.get('servers', {})
            
            if self._logger:
                self._logger.system(
                    f"[{self.name}] Loaded {len(self._server_configs)} server config(s)"
                )
        
        except Exception as e:
            if self._logger:
                self._logger.warning(f"[{self.name}] Failed to load config: {e}")
            self._server_configs = {}
    
    async def _connect_servers(self):
        """Connect to all configured servers"""
        for server_name, config in self._server_configs.items():
            try:
                command = config.get('command')
                args = config.get('args', [])
                
                if not command:
                    if self._logger:
                        self._logger.warning(
                            f"[{self.name}] Server '{server_name}' missing command"
                        )
                    continue
                
                server = MCPServer(server_name, command, args, self._logger)
                await server.connect()
                
                self._servers[server_name] = server
                
                # Discover tools from this server
                tools = await server.list_tools()
                for tool in tools:
                    tool_id = f"{server_name}.{tool['name']}"
                    self._available_tools[tool_id] = {
                        'server': server_name,
                        'tool': tool['name'],
                        'description': tool.get('description', ''),
                        'schema': tool.get('inputSchema', {})
                    }
                
                if self._logger:
                    self._logger.success(
                        f"[{self.name}] Connected to {server_name}: {len(tools)} tools"
                    )
            
            except Exception as e:
                if self._logger:
                    self._logger.error(
                        f"[{self.name}] Failed to connect to {server_name}: {e}"
                    )
    
    async def _add_server(
        self, 
        server_name: str, 
        command: str, 
        args: List[str]
    ) -> Dict[str, Any]:
        """Add and connect to new MCP server"""
        if server_name in self._servers:
            return self._error_result(
                f"Server '{server_name}' already connected",
                guidance="Use remove_server first to reconnect"
            )
        
        try:
            # Create server instance
            server = MCPServer(server_name, command, args, self._logger)
            await server.connect()
            
            self._servers[server_name] = server
            
            # Discover tools
            tools = await server.list_tools()
            for tool in tools:
                tool_id = f"{server_name}.{tool['name']}"
                self._available_tools[tool_id] = {
                    'server': server_name,
                    'tool': tool['name'],
                    'description': tool.get('description', ''),
                    'schema': tool.get('inputSchema', {})
                }
            
            # Save to config
            await self._save_server_config(server_name, command, args)
            
            return self._success_result(
                f"Connected to {server_name}: {len(tools)} tools available",
                metadata={'server': server_name, 'tools': len(tools)}
            )
        
        except Exception as e:
            return self._error_result(
                f"Failed to add server: {e}",
                metadata={'server': server_name}
            )
    
    async def _remove_server(self, server_name: str) -> Dict[str, Any]:
        """Disconnect and remove MCP server"""
        if server_name not in self._servers:
            return self._error_result(
                f"Server '{server_name}' not connected",
                guidance="Use list_servers to see connected servers"
            )
        
        try:
            server = self._servers[server_name]
            await server.disconnect()
            
            del self._servers[server_name]
            
            # Remove tools from this server
            tools_to_remove = [
                tool_id for tool_id, info in self._available_tools.items()
                if info['server'] == server_name
            ]
            
            for tool_id in tools_to_remove:
                del self._available_tools[tool_id]
            
            # Update config
            await self._remove_server_config(server_name)
            
            return self._success_result(
                f"Disconnected from {server_name}",
                metadata={'server': server_name, 'tools_removed': len(tools_to_remove)}
            )
        
        except Exception as e:
            return self._error_result(
                f"Failed to remove server: {e}",
                metadata={'server': server_name}
            )
    
    async def _save_server_config(self, server_name: str, command: str, args: List[str]):
        """Save server configuration"""
        config_file = self._config_dir / 'config.json'
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except:
            config = {"servers": {}}
        
        config['servers'][server_name] = {
            'command': command,
            'args': args
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    async def _remove_server_config(self, server_name: str):
        """Remove server from configuration"""
        config_file = self._config_dir / 'config.json'
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if server_name in config.get('servers', {}):
                del config['servers'][server_name]
                
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
        except:
            pass
    
    # ========================================================================
    # TOOL OPERATIONS
    # ========================================================================
    
    async def _list_servers(self) -> Dict[str, Any]:
        """List all connected servers"""
        servers = []
        
        for server_name, server in self._servers.items():
            tool_count = sum(
                1 for info in self._available_tools.values()
                if info['server'] == server_name
            )
            
            servers.append({
                'name': server_name,
                'connected': server.is_connected(),
                'tools': tool_count
            })
        
        return self._success_result(
            f"Connected to {len(servers)} MCP server(s)",
            metadata={'servers': servers}
        )
    
    async def _list_tools(self) -> Dict[str, Any]:
        """List all available MCP tools"""
        tools = []
        
        for tool_id, info in self._available_tools.items():
            tools.append({
                'id': tool_id,
                'server': info['server'],
                'name': info['tool'],
                'description': info['description']
            })
        
        return self._success_result(
            f"Found {len(tools)} MCP tool(s)",
            metadata={'tools': tools}
        )
    
    async def _call_tool(self, tool_id: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP tool call"""
        if tool_id not in self._available_tools:
            available = list(self._available_tools.keys())[:5]
            return self._error_result(
                f"Tool '{tool_id}' not found",
                guidance=f"Available: {', '.join(available)}",
                metadata={'available_tools': len(self._available_tools)}
            )
        
        tool_info = self._available_tools[tool_id]
        server_name = tool_info['server']
        tool_name = tool_info['tool']
        
        server = self._servers.get(server_name)
        if not server or not server.is_connected():
            return self._error_result(
                f"Server '{server_name}' not connected",
                guidance="Use list_servers to check server status"
            )
        
        try:
            # Call tool through MCP
            result = await server.call_tool(tool_name, tool_args)
            
            return self._success_result(
                f"Tool executed: {tool_id}",
                metadata={
                    'tool': tool_id,
                    'result': result
                }
            )
        
        except Exception as e:
            return self._error_result(
                f"Tool execution failed: {e}",
                metadata={'tool': tool_id, 'args': tool_args}
            )
    
    # ========================================================================
    # CONTEXT LOOP (Optional)
    # ========================================================================
    
    def has_context_loop(self) -> bool:
        """Enable monitoring of MCP server health"""
        return True
    
    async def context_loop(self, thought_buffer):
        """Monitor MCP server connections"""
        while self._running:
            try:
                # Check server health
                disconnected = []
                for server_name, server in self._servers.items():
                    if not server.is_connected():
                        disconnected.append(server_name)
                
                if disconnected:
                    thought_buffer.add_processed_thought(
                        content=f"[MCP] Servers disconnected: {', '.join(disconnected)}",
                        source='tool_context',
                        priority_override="HIGH"
                    )
                
                # Wait 30 seconds before next check
                await asyncio.sleep(30.0)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[{self.name}] Context loop error: {e}")
                await asyncio.sleep(30.0)


# ============================================================================
# MCP SERVER WRAPPER
# ============================================================================

class MCPServer:
    """
    Wrapper for MCP server connection (stdio transport)
    Handles JSON-RPC communication with MCP servers
    """
    
    def __init__(self, name: str, command: str, args: List[str], logger=None):
        self.name = name
        self.command = command
        self.args = args
        self.logger = logger
        
        self._process: Optional[subprocess.Popen] = None
        self._connected = False
        self._message_id = 0
        self._capabilities = {}
        self._tools = []
    
    async def connect(self):
        """Connect to MCP server"""
        try:
            # Start server process
            self._process = subprocess.Popen(
                [self.command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Send initialize request
            init_response = await self._send_request('initialize', {
                'protocolVersion': '2024-11-05',
                'capabilities': {
                    'roots': {'listChanged': False}
                },
                'clientInfo': {
                    'name': 'anna-ai-mcp-bridge',
                    'version': '1.0.0'
                }
            })
            
            self._capabilities = init_response.get('capabilities', {})
            
            # Send initialized notification
            await self._send_notification('notifications/initialized')
            
            # Discover tools
            self._tools = await self.list_tools()
            
            self._connected = True
            
            if self.logger:
                self.logger.success(
                    f"[MCP:{self.name}] Connected: {len(self._tools)} tools"
                )
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"[MCP:{self.name}] Connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except:
                self._process.kill()
            
            self._process = None
            self._connected = False
            
            if self.logger:
                self.logger.system(f"[MCP:{self.name}] Disconnected")
    
    def is_connected(self) -> bool:
        """Check connection status"""
        return self._connected and self._process is not None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from server"""
        try:
            response = await self._send_request('tools/list', {})
            return response.get('tools', [])
        except Exception as e:
            if self.logger:
                self.logger.error(f"[MCP:{self.name}] Failed to list tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute tool call"""
        response = await self._send_request('tools/call', {
            'name': tool_name,
            'arguments': arguments
        })
        
        return response.get('content', [])
    
    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC request"""
        if not self._process:
            raise RuntimeError("Not connected to server")
        
        self._message_id += 1
        
        request = {
            'jsonrpc': '2.0',
            'id': self._message_id,
            'method': method,
            'params': params
        }
        
        # Send request
        request_str = json.dumps(request) + '\n'
        self._process.stdin.write(request_str)
        self._process.stdin.flush()
        
        # Read response
        response_str = self._process.stdout.readline()
        response = json.loads(response_str)
        
        if 'error' in response:
            error = response['error']
            raise RuntimeError(f"MCP error: {error.get('message', 'Unknown error')}")
        
        return response.get('result', {})
    
    async def _send_notification(self, method: str, params: Dict[str, Any] = None):
        """Send JSON-RPC notification (no response expected)"""
        if not self._process:
            raise RuntimeError("Not connected to server")
        
        notification = {
            'jsonrpc': '2.0',
            'method': method
        }
        
        if params:
            notification['params'] = params
        
        notification_str = json.dumps(notification) + '\n'
        self._process.stdin.write(notification_str)
        self._process.stdin.flush()
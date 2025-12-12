# MCP Bridge Integration Guide

## Overview

The MCP Bridge tool enables Anna AI to interact with external tools through the Model Context Protocol (MCP). This provides dynamic access to a growing ecosystem of MCP servers without modifying core code.

## Architecture

```
Anna AI System
    ↓
Tool Manager
    ↓
MCP Bridge Tool (BaseTool)
    ↓
MCP Servers (stdio transport)
    ↓
External Services (filesystem, GitHub, databases, etc.)
```

## Features

✅ **Dynamic Tool Discovery** - Automatically discovers tools from connected servers
✅ **Multiple Server Support** - Connect to multiple MCP servers simultaneously
✅ **Persistent Configuration** - Server configs saved in `~/.mcp/servers/config.json`
✅ **Health Monitoring** - Background loop monitors server connection status
✅ **Instruction Persistence** - Works with 6-minute instruction timer system
✅ **JSON-RPC Communication** - Standard MCP protocol implementation

## Installation

### 1. Install Tool Files

```bash
# Create tool directory
mkdir -p BASE/tools/installed/mcp_bridge

# Copy tool files
cp tool.py BASE/tools/installed/mcp_bridge/
cp information.json BASE/tools/installed/mcp_bridge/
```

### 2. Enable MCP Bridge

```python
# In personality/controls.py
USE_MCP_BRIDGE = True
```

### 3. Configure MCP Servers

Default configuration (`~/.mcp/servers/config.json`):

```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"]
    }
  }
}
```

## Usage

### Discovery Workflow

```xml
<!-- 1. Retrieve MCP bridge instructions -->
<action_list>[
  {"tool": "instructions", "args": ["mcp_bridge"]}
]</action_list>

<!-- 2. List connected servers -->
<action_list>[
  {"tool": "mcp_bridge.list_servers", "args": []}
]</action_list>

<!-- 3. Discover available tools -->
<action_list>[
  {"tool": "mcp_bridge.list_tools", "args": []}
]</action_list>
```

### Tool Execution

```xml
<!-- Execute MCP tool -->
<action_list>[
  {"tool": "mcp_bridge.call_tool", "args": [
    "filesystem.read_file",
    {"path": "document.txt"}
  ]}
]</action_list>
```

### Server Management

```xml
<!-- Add new server -->
<action_list>[
  {"tool": "mcp_bridge.add_server", "args": [
    "github",
    "npx",
    ["-y", "@modelcontextprotocol/server-github"]
  ]}
]</action_list>

<!-- Remove server -->
<action_list>[
  {"tool": "mcp_bridge.remove_server", "args": ["github"]}
]</action_list>
```

## Available MCP Servers

### Official Servers

| Server | Command | Description |
|--------|---------|-------------|
| Filesystem | `@modelcontextprotocol/server-filesystem` | File operations |
| GitHub | `@modelcontextprotocol/server-github` | GitHub API access |
| Google Drive | `@modelcontextprotocol/server-gdrive` | Google Drive integration |
| PostgreSQL | `@modelcontextprotocol/server-postgres` | Database queries |
| Puppeteer | `@modelcontextprotocol/server-puppeteer` | Browser automation |
| Slack | `@modelcontextprotocol/server-slack` | Slack integration |

### Installation Example

```bash
# Install MCP server package
npm install -g @modelcontextprotocol/server-github

# Add to Anna AI via MCP bridge
# (use add_server command in agent)
```

## Example Scenarios

### Scenario 1: File System Operations

```xml
<!-- Read project files -->
<action_list>[
  {"tool": "mcp_bridge.call_tool", "args": [
    "filesystem.read_file",
    {"path": "BASE/core/config.py"}
  ]}
]</action_list>

<!-- List directory -->
<action_list>[
  {"tool": "mcp_bridge.call_tool", "args": [
    "filesystem.list_directory",
    {"path": "BASE/tools/installed"}
  ]}
]</action_list>
```

### Scenario 2: GitHub Integration

```xml
<!-- Search repositories -->
<action_list>[
  {"tool": "mcp_bridge.call_tool", "args": [
    "github.search_repositories",
    {"query": "model context protocol", "limit": 5}
  ]}
]</action_list>

<!-- Create issue -->
<action_list>[
  {"tool": "mcp_bridge.call_tool", "args": [
    "github.create_issue",
    {
      "owner": "myorg",
      "repo": "myrepo",
      "title": "Bug report",
      "body": "Description of issue"
    }
  ]}
]</action_list>
```

### Scenario 3: Database Queries

```xml
<!-- Query database -->
<action_list>[
  {"tool": "mcp_bridge.call_tool", "args": [
    "postgres.query",
    {"query": "SELECT * FROM users LIMIT 10"}
  ]}
]</action_list>
```

## Configuration Examples

### Multi-Server Setup

```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    },
    "postgres": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://localhost/mydb"
      ]
    }
  }
}
```

### Custom Server

```json
{
  "servers": {
    "my_custom_server": {
      "command": "python",
      "args": ["/path/to/my_mcp_server.py"]
    }
  }
}
```

## Troubleshooting

### Server Won't Connect

**Problem**: Server fails to initialize

**Solutions**:
1. Check server package is installed: `npm list -g @modelcontextprotocol/server-*`
2. Verify command path is correct
3. Check server logs in stderr
4. Test server independently: `npx @modelcontextprotocol/server-filesystem /tmp`

### Tool Not Found

**Problem**: Tool ID not recognized

**Solutions**:
1. List servers: `mcp_bridge.list_servers`
2. List tools: `mcp_bridge.list_tools`
3. Verify tool ID format: `server_name.tool_name`
4. Refresh server connection

### Server Disconnected

**Problem**: Server drops connection

**Solutions**:
1. Check context loop notifications for disconnection alerts
2. Remove and re-add server
3. Check server process isn't crashing (stderr)
4. Verify server command is stable

## Best Practices

### 1. Discovery First
Always discover available tools before attempting execution:
```xml
<action_list>[
  {"tool": "mcp_bridge.list_tools", "args": []}
]</action_list>
```

### 2. Error Handling
MCP tools can fail - check results and handle gracefully:
```xml
<!-- Tool might fail if file doesn't exist -->
<action_list>[
  {"tool": "mcp_bridge.call_tool", "args": [
    "filesystem.read_file",
    {"path": "might_not_exist.txt"}
  ]}
]</action_list>
```

### 3. Batch Operations
Group related MCP calls when possible:
```xml
<action_list>[
  {"tool": "mcp_bridge.call_tool", "args": ["filesystem.read_file", {"path": "file1.txt"}]},
  {"tool": "mcp_bridge.call_tool", "args": ["filesystem.read_file", {"path": "file2.txt"}]}
]</action_list>
```

### 4. Monitor Health
Watch for disconnection notifications and reconnect as needed.

## Security Considerations

⚠️ **Important Security Notes**:

1. **Filesystem Access**: Servers can read/write files - configure paths carefully
2. **API Credentials**: Some servers need tokens/keys - store securely
3. **Network Access**: Servers may make external API calls
4. **Resource Usage**: Monitor server processes for memory/CPU usage
5. **Input Validation**: MCP bridge validates tool IDs but not all arguments

### Secure Configuration

```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/home/user/safe_directory"  // Restricted path
      ]
    }
  }
}
```

## Performance

### Metrics
- **Connection Time**: ~1-2s per server
- **Tool Discovery**: <100ms per server
- **Tool Execution**: Varies by server (typically <1s)
- **Health Check**: Every 30s (background)

### Optimization
- Keep server count reasonable (<5 servers)
- Use instruction persistence (6min timer)
- Batch tool calls when possible
- Monitor server stderr for issues

## Integration with Anna AI

### Thought Buffer Integration
```python
# MCP results automatically injected
thought_buffer.add_processed_thought(
    content=f"[mcp_bridge] Tool result: {result}",
    source='tool_result',
    priority_override="MEDIUM"
)
```

### Instruction Persistence
```python
# 6-minute timer applies to MCP bridge
# After retrieval, all MCP commands available for 6 minutes
# Timer resets on each instruction retrieval
```

### Context Loop
```python
# Background monitoring every 30s
# Alerts on server disconnection
# Auto-cleanup of stale connections
```

## Future Enhancements

Planned improvements:
- [ ] WebSocket transport support
- [ ] Server auto-restart on crash
- [ ] Resource usage monitoring
- [ ] Connection pooling
- [ ] Caching layer for frequent calls
- [ ] Server version compatibility checks
- [ ] Enhanced error messages with context

## Support

For issues or questions:
1. Check logs: Anna AI tool execution logs
2. Test server independently: `npx @modelcontextprotocol/server-*`
3. Review MCP protocol: https://modelcontextprotocol.io
4. Check server documentation

## References

- **MCP Specification**: https://spec.modelcontextprotocol.io
- **Official Servers**: https://github.com/modelcontextprotocol/servers
- **Protocol Documentation**: https://modelcontextprotocol.io
- **Community Servers**: https://github.com/topics/mcp-server
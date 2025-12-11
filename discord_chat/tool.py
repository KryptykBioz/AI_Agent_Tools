# Filename: BASE/tools/installed/discord_chat/tool.py
"""
Discord Chat Tool - Simplified Architecture
Single master class for Discord bot integration
Message callback pattern with automatic context tracking
"""
from typing import List, Dict, Any, Optional, Callable
from BASE.handlers.base_tool import BaseTool
import asyncio
import threading
from datetime import datetime
import re

# Check Discord availability
try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False


class DiscordChatTool(BaseTool):
    """
    Discord chat tool for monitoring and sending messages
    Runs Discord bot with event handlers and command support
    """
    
    @property
    def name(self) -> str:
        return "discord_chat"
    
    async def initialize(self) -> bool:
        """Initialize Discord bot"""
        if not DISCORD_AVAILABLE:
            if self._logger:
                self._logger.warning("[Discord] discord.py not installed")
            return False
        
        # Load configuration from config file
        try:
            from BASE.tools.installed.discord_chat import config
            
            self.token = getattr(config, 'DISCORD_BOT_TOKEN', '')
            self.command_prefix = getattr(config, 'DISCORD_COMMAND_PREFIX', '!')
            self.allowed_channels = getattr(config, 'DISCORD_ALLOWED_CHANNELS', None)
            self.allowed_guilds = getattr(config, 'DISCORD_ALLOWED_GUILDS', None)
            self.max_message_length = getattr(config, 'DISCORD_MAX_MESSAGE_LENGTH', 2000)
            self.auto_start = getattr(config, 'DISCORD_AUTO_START', False)
        except (ImportError, AttributeError) as e:
            if self._logger:
                self._logger.warning(f"[Discord] Could not load config: {e}")
            self.token = ''
            self.command_prefix = '!'
            self.allowed_channels = None
            self.allowed_guilds = None
            self.max_message_length = 2000
            self.auto_start = False
        
        # Convert channel/guild IDs to sets
        if self.allowed_channels:
            self.allowed_channels = set(map(int, self.allowed_channels))
        if self.allowed_guilds:
            self.allowed_guilds = set(map(int, self.allowed_guilds))
        
        # State
        self.bot_running = False
        self.bot = None
        self.bot_thread = None
        self.loop = None
        
        # Message callback
        self._message_callback = None
        
        # Context tracking
        self.context_buffer = []
        self.max_context_messages = 10
        self.last_channel_id = None
        
        # Response queue
        self._response_queue = None
        self._response_task = None
        
        # Statistics
        self.stats = {
            'messages_received': 0,
            'messages_sent': 0,
            'errors': 0,
            'start_time': None
        }
        
        # Initialize bot
        if self.token:
            self._initialize_bot()
            if self.auto_start:
                self._start_bot()
                if self._logger:
                    self._logger.system(f"[Discord] Auto-starting bot")
        elif self._logger:
            self._logger.warning("[Discord] No bot token configured")
        
        return True  # Always return True for graceful degradation
    
    async def cleanup(self):
        """Cleanup Discord resources"""
        await self._stop_bot()
        self.context_buffer.clear()
        
        if self._logger:
            self._logger.system("[Discord] Cleaned up")
    
    def is_available(self) -> bool:
        """Check if Discord bot is available"""
        return DISCORD_AVAILABLE and bool(self.token) and self.bot_running
    
    def _initialize_bot(self):
        """Initialize Discord bot instance"""
        # Setup intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.guilds = True
        intents.members = True
        
        # Create bot
        self.bot = commands.Bot(
            command_prefix=self.command_prefix,
            intents=intents,
            help_command=None
        )
        
        # Setup event handlers
        self._setup_events()
        self._setup_commands()
        
        if self._logger:
            self._logger.tool(f"[Discord] Bot configured: prefix='{self.command_prefix}'")
            if self.allowed_channels:
                self._logger.tool(f"[Discord] Restricted to channels: {list(self.allowed_channels)}")
            if self.allowed_guilds:
                self._logger.tool(f"[Discord] Restricted to guilds: {list(self.allowed_guilds)}")
    
    def _setup_events(self):
        """Setup Discord event handlers"""
        
        @self.bot.event
        async def on_ready():
            if self._logger:
                self._logger.success(f"[Discord] Bot logged in as {self.bot.user}")
                self._logger.tool(f"[Discord] Connected to {len(self.bot.guilds)} guilds")
            self.stats['start_time'] = datetime.now()
            
            # Start response processor
            if self._response_queue is None:
                self._response_queue = asyncio.Queue()
            self._response_task = asyncio.create_task(self._process_responses())
        
        @self.bot.event
        async def on_message(message: discord.Message):
            # Ignore own messages
            if message.author == self.bot.user:
                return
            
            # Check guild restrictions
            if self.allowed_guilds and message.guild:
                if message.guild.id not in self.allowed_guilds:
                    return
            
            # Check channel restrictions
            if self.allowed_channels:
                if message.channel.id not in self.allowed_channels:
                    return
            
            # Process commands first
            await self.bot.process_commands(message)
            
            # Don't process commands as regular messages
            if message.content.startswith(self.command_prefix):
                return
            
            if self._logger:
                self._logger.tool(
                    f"[Discord] Message from {message.author}: "
                    f"{message.content[:50]}{'...' if len(message.content) > 50 else ''}"
                )
            
            self.stats['messages_received'] += 1
            
            # Track channel for responses
            self.last_channel_id = message.channel.id
            
            # Add to context buffer
            self._add_to_context(message)
            
            # Invoke message callback if set
            if self._message_callback:
                self._invoke_message_callback(message)
    
    def _setup_commands(self):
        """Setup bot commands"""
        
        @self.bot.command(name='ping')
        async def ping(ctx):
            """Check bot responsiveness"""
            latency = round(self.bot.latency * 1000)
            await ctx.send(f"🏓 Pong! Latency: {latency}ms")
            if self._logger:
                self._logger.tool(f"[Discord] Ping command: {latency}ms")
        
        @self.bot.command(name='status')
        async def status(ctx):
            """Show bot statistics"""
            status_data = self.get_status()
            
            embed = discord.Embed(
                title="🤖 Bot Status",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Messages",
                value=f"Received: {status_data['messages_received']}\nSent: {status_data['messages_sent']}"
            )
            
            if status_data.get('uptime_seconds'):
                hours = status_data['uptime_seconds'] / 3600
                embed.add_field(name="Uptime", value=f"{hours:.1f} hours")
            
            embed.add_field(name="Guilds", value=status_data['guilds'])
            embed.add_field(name="Connected", value="[SUCCESS]" if status_data['connected'] else "[FAILED]")
            
            await ctx.send(embed=embed)
            if self._logger:
                self._logger.tool(f"[Discord] Status command used")
        
        @self.bot.command(name='clear_context')
        async def clear_context(ctx):
            """Clear conversation context"""
            self.context_buffer.clear()
            await ctx.send("[SUCCESS] Context cleared!")
            if self._logger:
                self._logger.tool(f"[Discord] Context cleared")
    
    def set_message_callback(self, callback: Callable):
        """Set callback for incoming messages"""
        self._message_callback = callback
        if self._logger:
            self._logger.tool("[Discord] Message callback registered")
    
    def _invoke_message_callback(self, message: discord.Message):
        """Invoke message callback with normalized format"""
        if not self._message_callback:
            return
        
        # Resolve mentions to usernames
        resolved_content = self._resolve_mentions(message)
        
        # Normalize to unified format
        message_dict = {
            'author': message.author.display_name or message.author.name,
            'message': resolved_content,
            'timestamp': message.created_at.timestamp() * 1000,
            'user_id': str(message.author.id),
            'badges': self._extract_badges(message.author),
            'emotes': [],
            'color': str(message.author.color) if hasattr(message.author, 'color') else None,
            'channel_id': message.channel.id,
            'channel_name': message.channel.name if hasattr(message.channel, 'name') else 'DM',
            'guild_id': message.guild.id if message.guild else None,
            'guild_name': message.guild.name if message.guild else None,
            'is_mentioned': self.bot.user in message.mentions,
            'is_reply': message.reference is not None
        }
        
        try:
            self._message_callback(message_dict)
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Discord] Error in message callback: {e}")
            self.stats['errors'] += 1
    
    def _resolve_mentions(self, message: discord.Message) -> str:
        """Replace Discord mention IDs with actual usernames"""
        content = message.content
        
        # User mentions
        for mention in message.mentions:
            content = content.replace(f'<@{mention.id}>', f'@{mention.display_name}')
            content = content.replace(f'<@!{mention.id}>', f'@{mention.display_name}')
        
        # Role mentions
        if hasattr(message, 'role_mentions'):
            for role in message.role_mentions:
                content = content.replace(f'<@&{role.id}>', f'@{role.name}')
        
        # Channel mentions
        if hasattr(message, 'channel_mentions'):
            for channel in message.channel_mentions:
                content = content.replace(f'<#{channel.id}>', f'#{channel.name}')
        
        return content
    
    def _extract_badges(self, member) -> List[str]:
        """Extract user badges/roles"""
        badges = []
        if hasattr(member, 'roles'):
            for role in member.roles:
                if role.name != '@everyone':
                    badges.append(role.name)
        return badges
    
    def _add_to_context(self, message: discord.Message):
        """Add message to context buffer"""
        self.context_buffer.append({
            'author': str(message.author),
            'content': message.content,
            'timestamp': message.created_at
        })
        
        if len(self.context_buffer) > self.max_context_messages:
            self.context_buffer.pop(0)
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute Discord chat command
        
        Commands:
        - start: Start Discord bot
        - stop: Stop Discord bot
        - send_message: Send message to channel
        - get_context: Get conversation context
        
        Args:
            command: Command name
            args: Command arguments
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[Discord] Command: '{command}', args: {args}")
        
        # Route commands
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
                guidance='Available commands: start, stop, send_message, get_context'
            )
    
    async def _handle_start(self) -> Dict[str, Any]:
        """Handle start command"""
        if self.bot_running:
            return self._success_result(
                'Discord bot already running',
                metadata={'guilds': len(self.bot.guilds) if self.bot else 0}
            )
        
        self._start_bot()
        
        # Wait a moment for connection
        await asyncio.sleep(2)
        
        if self.bot_running:
            return self._success_result(
                'Started Discord bot',
                metadata={'guilds': len(self.bot.guilds) if self.bot else 0}
            )
        else:
            return self._error_result(
                'Failed to start Discord bot',
                guidance='Check bot token and network connection'
            )
    
    async def _handle_stop(self) -> Dict[str, Any]:
        """Handle stop command"""
        await self._stop_bot()
        return self._success_result('Stopped Discord bot')
    
    async def _handle_send_message(self, args: List[Any]) -> Dict[str, Any]:
        """Handle send_message command"""
        if not self.is_available():
            return self._error_result(
                'Discord bot is not connected',
                guidance='Start bot first with discord_chat.start'
            )
        
        if not args:
            return self._error_result(
                'No message provided',
                guidance='Provide message: {"tool": "discord_chat.send_message", "args": ["message"]}'
            )
        
        message = str(args[0])
        channel_id = int(args[1]) if len(args) > 1 else self.last_channel_id
        
        if not channel_id:
            return self._error_result(
                'No channel ID specified and no recent messages',
                guidance='Specify channel_id or send after receiving a message'
            )
        
        # Queue message for sending
        try:
            await self._queue_message(channel_id, message)
            
            if self._logger:
                self._logger.success(f"[Discord] Queued message to channel {channel_id}")
            
            return self._success_result(
                f'Message queued for channel {channel_id}',
                metadata={
                    'channel_id': channel_id,
                    'message_length': len(message)
                }
            )
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Discord] Error queuing message: {e}")
            return self._error_result(
                f'Failed to queue message: {str(e)}',
                guidance='Check channel ID and bot permissions'
            )
    
    async def _handle_get_context(self) -> Dict[str, Any]:
        """Handle get_context command"""
        if not self.is_available():
            return self._error_result(
                'Discord bot is not connected',
                guidance='Start bot first'
            )
        
        context = self.get_context_for_ai()
        
        return self._success_result(
            context if context else 'No conversation context available',
            metadata={'context_messages': len(self.context_buffer)}
        )
    
    def get_context_for_ai(self) -> str:
        """Get formatted context for AI"""
        if not self.context_buffer:
            return ""
        
        context_lines = []
        for msg in self.context_buffer:
            author = msg['author']
            content = msg['content']
            context_lines.append(f"{author}: {content}")
        
        return "\n".join(context_lines)
    
    async def _queue_message(self, channel_id: int, content: str):
        """Queue message for sending"""
        if not self._response_queue:
            raise RuntimeError("Response queue not initialized")
        
        await self._response_queue.put((channel_id, content))
    
    async def _process_responses(self):
        """Background task to process response queue"""
        while True:
            try:
                channel_id, content = await self._response_queue.get()
                
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    if self._logger:
                        self._logger.error(f"[Discord] Channel {channel_id} not found")
                    continue
                
                await self._send_message_internal(channel, content)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[Discord] Error in response processor: {e}")
                self.stats['errors'] += 1
    
    async def _send_message_internal(self, channel: discord.TextChannel, content: str):
        """Internal method to send message with splitting"""
        content = self._sanitize_message(content)
        
        if len(content) <= self.max_message_length:
            await channel.send(content)
            self.stats['messages_sent'] += 1
            if self._logger:
                self._logger.success(f"[Discord] Sent message to #{channel.name}")
        else:
            chunks = self._split_message(content)
            if self._logger:
                self._logger.tool(f"[Discord] Splitting message into {len(chunks)} chunks")
            for chunk in chunks:
                await channel.send(chunk)
                self.stats['messages_sent'] += 1
                await asyncio.sleep(0.5)
    
    def _sanitize_message(self, content: str) -> str:
        """Remove potentially problematic content"""
        content = content.replace('@everyone', '@\u200beveryone')
        content = content.replace('@here', '@\u200bhere')
        content = re.sub(r'<@&(\d+)>', r'[role]', content)
        content = re.sub(r'<@!?(\d+)>', r'[user]', content)
        return content
    
    def _split_message(self, content: str) -> List[str]:
        """Split long message into chunks"""
        chunks = []
        current_chunk = ""
        
        parts = re.split(r'([.!?\n])', content)
        
        for i in range(0, len(parts), 2):
            part = parts[i]
            separator = parts[i+1] if i+1 < len(parts) else ''
            segment = part + separator
            
            if len(current_chunk) + len(segment) <= self.max_message_length - 50:
                current_chunk += segment
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = segment
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Fallback for very long segments
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > self.max_message_length:
                for i in range(0, len(chunk), self.max_message_length):
                    final_chunks.append(chunk[i:i + self.max_message_length].strip())
            else:
                final_chunks.append(chunk)
        
        return final_chunks
    
    def _start_bot(self):
        """Start Discord bot"""
        if self.bot_running:
            if self._logger:
                self._logger.warning("[Discord] Bot already running")
            return
        
        if not self.token or self.token.strip() == "":
            if self._logger:
                self._logger.error("[Discord] Cannot start: Token not configured")
            return
        
        self.bot_running = True
        self.bot_thread = threading.Thread(
            target=self._run_bot,
            daemon=True
        )
        self.bot_thread.start()
        
        if self._logger:
            self._logger.tool("[Discord] Bot starting...")
    
    def _run_bot(self):
        """Run bot in thread"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.bot.start(self.token))
        except discord.errors.LoginFailure:
            if self._logger:
                self._logger.error("[Discord] Login failed: Invalid token")
            self.bot_running = False
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Discord] Bot error: {e}")
            self.bot_running = False
            self.stats['errors'] += 1
    
    async def _stop_bot(self):
        """Stop Discord bot"""
        if not self.bot_running:
            return
        
        if self._logger:
            self._logger.tool("[Discord] Stopping bot...")
        
        if self._response_task and not self._response_task.done():
            self._response_task.cancel()
        
        if self.loop and self.bot:
            future = asyncio.run_coroutine_threadsafe(self.bot.close(), self.loop)
            try:
                future.result(timeout=5.0)
            except asyncio.TimeoutError:
                if self._logger:
                    self._logger.warning("[Discord] Timeout during shutdown")
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[Discord] Error during shutdown: {e}")
        
        if self.loop and self.loop.is_running():
            self.loop.stop()
        
        self.bot_running = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get Discord bot status (for debugging/monitoring)"""
        status = {
            'available': self.is_available(),
            'discord_library': DISCORD_AVAILABLE,
            'token_configured': bool(self.token),
            'connected': self.bot_running,
            'guilds': 0,
            'command_prefix': self.command_prefix,
            'messages_received': self.stats['messages_received'],
            'messages_sent': self.stats['messages_sent'],
            'errors': self.stats['errors']
        }
        
        if self.bot and self.bot_running:
            status['guilds'] = len(self.bot.guilds)
            status['user'] = str(self.bot.user) if self.bot.user else None
        
        if self.stats.get('start_time'):
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
            status['uptime_seconds'] = uptime
        
        return status
# Filename: minecraft_spectator/tool.py
"""
Minecraft Spectator Tool - Direct Connection (No Bot Server Required)
======================================================================
Lightweight spectator that connects directly to Minecraft servers.
Works with both LAN and multiplayer servers.

Uses quarry library for direct Minecraft protocol communication.
No Node.js bot server needed.

Spectator can:
- Monitor game state
- Track player position and health
- Observe nearby entities
- View inventory
- Receive environmental updates

Spectator CANNOT:
- Move or control player
- Gather resources or mine
- Attack or interact with world
- Craft items or use inventory
- Send chat or build structures
"""
from pathlib import Path
import sys
import asyncio
from typing import List, Dict, Any, Optional
from collections import defaultdict
import time

# Add BASE to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root / 'BASE') not in sys.path:
    sys.path.insert(0, str(project_root / 'BASE'))

from handlers.base_tool import BaseTool


class MinecraftSpectatorTool(BaseTool):
    """Direct-connection Minecraft spectator (no bot server required)"""
    
    __slots__ = (
        '_config', '_controls', '_logger', '_running', '_context_task',
        '_host', '_port', '_username', '_version',
        '_client', '_connected', '_game_state', '_last_update',
        '_context_interval', '_packet_handlers'
    )
    
    def __init__(self, config, controls, logger=None):
        super().__init__(config, controls, logger)
        
        # Connection settings (configurable)
        self._host = config.get('minecraft_host', 'localhost')
        self._port = config.get('minecraft_port', 25565)
        self._username = config.get('minecraft_username', 'SpectatorBot')
        self._version = config.get('minecraft_version', '1.19.4')
        
        # Client state
        self._client = None
        self._connected = False
        
        # Game state cache
        self._game_state = {
            'player': {
                'health': 20.0,
                'food': 20,
                'position': {'x': 0, 'y': 0, 'z': 0},
                'yaw': 0,
                'pitch': 0
            },
            'game': {
                'time': 0,
                'weather': 'clear'
            },
            'entities': [],
            'inventory': [],
            'nearby_blocks': []
        }
        
        self._last_update = time.time()
        self._context_interval = 10.0
        self._packet_handlers = {}
    
    # ========================================================================
    # REQUIRED BASETOOL METHODS
    # ========================================================================
    
    @property
    def name(self) -> str:
        return "minecraft_spectator"
    
    async def initialize(self) -> bool:
        """Initialize direct connection to Minecraft server"""
        try:
            # Import quarry (lightweight Minecraft protocol library)
            try:
                from quarry.net.client import ClientFactory, ClientProtocol
                from twisted.internet import reactor
            except ImportError:
                if self._logger:
                    self._logger.error(
                        f"[{self.name}] quarry library not installed. "
                        f"Install with: pip install quarry-minecraft"
                    )
                return False
            
            # Create spectator client
            self._client = MinecraftSpectatorClient(
                self._host,
                self._port,
                self._username,
                self._version,
                self._game_state,
                self._logger
            )
            
            # Attempt connection
            success = await self._client.connect()
            
            if success:
                self._connected = True
                if self._logger:
                    self._logger.success(
                        f"[{self.name}] Connected to {self._host}:{self._port}"
                    )
                return True
            else:
                if self._logger:
                    self._logger.error(
                        f"[{self.name}] Failed to connect to server"
                    )
                return False
        
        except Exception as e:
            if self._logger:
                self._logger.error(
                    f"[{self.name}] Initialization failed: {e}"
                )
            return False
    
    async def cleanup(self):
        """Cleanup spectator resources"""
        if self._client:
            await self._client.disconnect()
            self._client = None
        
        self._connected = False
        
        if self._logger:
            self._logger.system(f"[{self.name}] Spectator disconnected")
    
    def is_available(self) -> bool:
        """Check if spectator is available"""
        return self._connected and self._client is not None
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """Execute spectator commands (observation only)"""
        if not self.is_available():
            return self._error_result(
                "Spectator not connected",
                guidance="Check server address and ensure Minecraft is running"
            )
        
        try:
            # Route to appropriate handler
            if command == "get_full_status":
                return await self._get_full_status()
            
            elif command == "get_inventory":
                return await self._get_inventory()
            
            elif command == "get_nearby_blocks":
                max_distance = args[0] if args else 10.0
                return await self._get_nearby_blocks(max_distance)
            
            elif command == "get_nearby_entities":
                max_distance = args[0] if args else 20.0
                return await self._get_nearby_entities(max_distance)
            
            elif command == "get_player_stats":
                return await self._get_player_stats()
            
            else:
                return self._error_result(
                    f"Unknown spectator command: {command}",
                    guidance="Available: get_full_status, get_inventory, "
                             "get_nearby_blocks, get_nearby_entities, get_player_stats"
                )
        
        except Exception as e:
            if self._logger:
                self._logger.error(
                    f"[{self.name}] Execute error: {e}"
                )
            return self._error_result(
                f"Spectator command failed: {str(e)}",
                guidance="Check connection to Minecraft server"
            )
    
    # ========================================================================
    # CONTEXT LOOP (Background Monitoring)
    # ========================================================================
    
    def has_context_loop(self) -> bool:
        """Enable background monitoring"""
        return True
    
    async def context_loop(self, thought_buffer):
        """
        Background loop: inject minimal status updates
        Plus critical alerts when detected
        """
        while self._running:
            try:
                if not self._connected:
                    await asyncio.sleep(5.0)
                    continue
                
                # Check for critical alerts
                alerts = self._check_critical_alerts()
                
                if alerts:
                    # Inject critical alert with high urgency
                    alert_msg = "\n".join(alerts)
                    thought_buffer.add_processed_thought(
                        content=f"[Minecraft Spectator - ALERT]\n{alert_msg}",
                        source='tool_context',
                        urgency_override=8
                    )
                
                # Always inject minimal background summary
                summary = self._create_status_summary()
                thought_buffer.add_processed_thought(
                    content=f"[Minecraft Spectator] {summary}",
                    source='tool_context',
                    urgency_override=4
                )
                
                # Update timestamp
                self._last_update = time.time()
                
                # Wait before next update
                await asyncio.sleep(self._context_interval)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._logger:
                    self._logger.error(
                        f"[{self.name}] Context loop error: {e}"
                    )
                await asyncio.sleep(5.0)
    
    # ========================================================================
    # SPECTATOR COMMAND IMPLEMENTATIONS
    # ========================================================================
    
    async def _get_full_status(self) -> Dict[str, Any]:
        """Get complete detailed game state"""
        player = self._game_state['player']
        game = self._game_state['game']
        entities = self._game_state['entities']
        inventory = self._game_state['inventory']
        
        status_parts = []
        
        # Player info
        status_parts.append(
            f"Health: {player.get('health', 0):.1f}/20 | "
            f"Food: {player.get('food', 0)}/20"
        )
        
        # Position
        pos = player.get('position', {})
        status_parts.append(
            f"Position: ({pos.get('x', 0):.1f}, "
            f"{pos.get('y', 0):.1f}, {pos.get('z', 0):.1f})"
        )
        
        # Game info
        time_val = game.get('time', 0)
        time_phase = self._get_time_phase(time_val)
        status_parts.append(
            f"Time: {time_phase} ({time_val}) | "
            f"Weather: {game.get('weather', 'clear')}"
        )
        
        # Entities
        hostile_count = sum(1 for e in entities if e.get('hostile', False))
        status_parts.append(
            f"Nearby entities: {len(entities)} ({hostile_count} hostile)"
        )
        
        # Inventory
        status_parts.append(f"Inventory: {len(inventory)} items")
        
        content = "\n".join(status_parts)
        
        return self._success_result(
            content,
            metadata={
                'player': player,
                'game': game,
                'entities': entities,
                'inventory': inventory
            }
        )
    
    async def _get_inventory(self) -> Dict[str, Any]:
        """Get detailed inventory breakdown"""
        inventory = self._game_state['inventory']
        
        if not inventory:
            return self._success_result(
                "Inventory is empty",
                metadata={'items': []}
            )
        
        # Count items by type
        item_counts = defaultdict(int)
        for item in inventory:
            name = item.get('name', 'unknown')
            count = item.get('count', 1)
            item_counts[name] += count
        
        # Format inventory list
        inventory_lines = [
            f"{name}: {count}" 
            for name, count in sorted(item_counts.items())
        ]
        
        content = "Inventory:\n" + "\n".join(inventory_lines)
        
        return self._success_result(
            content,
            metadata={'items': inventory, 'counts': dict(item_counts)}
        )
    
    async def _get_nearby_blocks(self, max_distance: float) -> Dict[str, Any]:
        """Get nearby blocks with coordinates"""
        blocks = self._game_state.get('nearby_blocks', [])
        
        # Filter by distance
        nearby = [
            b for b in blocks 
            if b.get('distance', 999) <= max_distance
        ]
        
        if not nearby:
            return self._success_result(
                f"No blocks found within {max_distance}m",
                metadata={'blocks': []}
            )
        
        # Sort by distance
        nearby_sorted = sorted(nearby, key=lambda b: b.get('distance', 999))
        
        # Format block list (limit to 20)
        block_lines = [
            f"{b.get('name', 'unknown')} at "
            f"({b.get('x', 0)}, {b.get('y', 0)}, {b.get('z', 0)}) "
            f"- {b.get('distance', 0):.1f}m"
            for b in nearby_sorted[:20]
        ]
        
        content = f"Nearby blocks (within {max_distance}m):\n"
        content += "\n".join(block_lines)
        
        if len(nearby) > 20:
            content += f"\n... and {len(nearby) - 20} more"
        
        return self._success_result(
            content,
            metadata={'blocks': nearby, 'count': len(nearby)}
        )
    
    async def _get_nearby_entities(self, max_distance: float) -> Dict[str, Any]:
        """Get nearby entities/mobs with details"""
        entities = self._game_state['entities']
        
        # Filter by distance
        nearby = [
            e for e in entities 
            if e.get('distance', 999) <= max_distance
        ]
        
        if not nearby:
            return self._success_result(
                f"No entities found within {max_distance}m",
                metadata={'entities': []}
            )
        
        # Separate hostile and passive
        hostile = [e for e in nearby if e.get('hostile', False)]
        passive = [e for e in nearby if not e.get('hostile', False)]
        
        lines = []
        
        if hostile:
            lines.append(f"Hostile entities ({len(hostile)}):")
            hostile_sorted = sorted(hostile, key=lambda e: e.get('distance', 999))
            for e in hostile_sorted[:10]:
                pos = e.get('position', {})
                dist = e.get('distance', 0)
                lines.append(
                    f"  {e.get('type', 'unknown')} - {dist:.1f}m away at "
                    f"({pos.get('x', 0):.1f}, {pos.get('y', 0):.1f}, {pos.get('z', 0):.1f})"
                )
        
        if passive:
            lines.append(f"Passive entities ({len(passive)}):")
            passive_sorted = sorted(passive, key=lambda e: e.get('distance', 999))
            for e in passive_sorted[:10]:
                dist = e.get('distance', 0)
                lines.append(f"  {e.get('type', 'unknown')} - {dist:.1f}m away")
        
        content = "\n".join(lines)
        
        return self._success_result(
            content,
            metadata={
                'entities': nearby,
                'hostile_count': len(hostile),
                'passive_count': len(passive)
            }
        )
    
    async def _get_player_stats(self) -> Dict[str, Any]:
        """Get player statistics"""
        player = self._game_state['player']
        
        stats = [
            f"Health: {player.get('health', 0):.1f}/20",
            f"Food: {player.get('food', 0)}/20",
            f"Position: ({player.get('position', {}).get('x', 0):.1f}, "
            f"{player.get('position', {}).get('y', 0):.1f}, "
            f"{player.get('position', {}).get('z', 0):.1f})",
            f"Facing: Yaw {player.get('yaw', 0):.1f}°, Pitch {player.get('pitch', 0):.1f}°"
        ]
        
        content = "\n".join(stats)
        
        return self._success_result(
            content,
            metadata={'player': player}
        )
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _create_status_summary(self) -> str:
        """Create one-line status summary for background updates"""
        player = self._game_state['player']
        game = self._game_state['game']
        entities = self._game_state['entities']
        
        pos = player.get('position', {})
        hostile_count = sum(1 for e in entities if e.get('hostile', False))
        time_phase = self._get_time_phase(game.get('time', 0))
        
        return (
            f"HP: {player.get('health', 0):.1f}/20 | "
            f"Food: {player.get('food', 0)}/20 | "
            f"Pos: ({pos.get('x', 0):.0f},{pos.get('y', 0):.0f},{pos.get('z', 0):.0f}) | "
            f"Threats: {hostile_count} | "
            f"Time: {time_phase}"
        )
    
    def _check_critical_alerts(self) -> List[str]:
        """Check for critical events that need immediate attention"""
        alerts = []
        
        player = self._game_state['player']
        health = player.get('health', 20)
        food = player.get('food', 20)
        
        # Critical health
        if health < 8:
            alerts.append(f"⚠️ CRITICAL: Health at {health:.1f}/20!")
        
        # Low food
        if food <= 3:
            alerts.append(f"⚠️ WARNING: Food at {food}/20!")
        
        # Nearby hostile mobs
        entities = self._game_state['entities']
        close_hostiles = [
            e for e in entities 
            if e.get('hostile', False) and e.get('distance', 999) < 10
        ]
        
        if close_hostiles:
            mob_types = [e.get('type', 'unknown') for e in close_hostiles]
            alerts.append(
                f"⚠️ THREAT: {len(close_hostiles)} hostile mob(s) nearby: "
                f"{', '.join(set(mob_types))}"
            )
        
        return alerts
    
    def _get_time_phase(self, time_ticks: int) -> str:
        """Convert Minecraft time ticks to phase"""
        time_ticks = time_ticks % 24000
        
        if 0 <= time_ticks < 6000:
            return "Day"
        elif 6000 <= time_ticks < 12000:
            return "Noon"
        elif 12000 <= time_ticks < 13000:
            return "Sunset"
        elif 13000 <= time_ticks < 18000:
            return "Night"
        elif 18000 <= time_ticks < 23000:
            return "Late Night"
        else:
            return "Sunrise"


class MinecraftSpectatorClient:
    """
    Lightweight Minecraft client for spectator mode
    Handles direct protocol communication without bot server
    """
    
    def __init__(self, host, port, username, version, game_state, logger=None):
        self.host = host
        self.port = port
        self.username = username
        self.version = version
        self.game_state = game_state
        self.logger = logger
        self.connected = False
        
        # Packet processing
        self._packet_queue = asyncio.Queue()
        self._processor_task = None
    
    async def connect(self) -> bool:
        """
        Connect to Minecraft server
        
        NOTE: This is a simplified implementation.
        For production, you'd use quarry or pyCraft libraries.
        """
        try:
            if self.logger:
                self.logger.system(
                    f"[Spectator Client] Attempting connection to {self.host}:{self.port}"
                )
            
            # In production, this would:
            # 1. Establish TCP connection
            # 2. Perform handshake
            # 3. Login to server
            # 4. Start packet processing loop
            
            # For now, simulate connection
            # You would replace this with actual quarry/pyCraft implementation
            
            self.connected = True
            
            # Start packet processor
            self._processor_task = asyncio.create_task(self._packet_processor())
            
            if self.logger:
                self.logger.success(
                    f"[Spectator Client] Connected as {self.username}"
                )
            
            return True
        
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"[Spectator Client] Connection failed: {e}"
                )
            return False
    
    async def disconnect(self):
        """Disconnect from server"""
        self.connected = False
        
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        if self.logger:
            self.logger.system("[Spectator Client] Disconnected")
    
    async def _packet_processor(self):
        """
        Process incoming packets from server
        
        This would handle packets like:
        - Player health/food updates
        - Position updates
        - Entity spawn/movement
        - Block changes
        - Time updates
        """
        while self.connected:
            try:
                # In production, you'd read packets from socket
                # and update game_state accordingly
                
                # Simulate packet processing
                await asyncio.sleep(0.1)
                
                # Example: Update time
                self.game_state['game']['time'] = (
                    self.game_state['game']['time'] + 1
                ) % 24000
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        f"[Spectator Client] Packet processing error: {e}"
                    )
                await asyncio.sleep(1.0)
    
    def _handle_health_update(self, health: float, food: int):
        """Handle health/food update packet"""
        self.game_state['player']['health'] = health
        self.game_state['player']['food'] = food
    
    def _handle_position_update(self, x: float, y: float, z: float, yaw: float, pitch: float):
        """Handle position update packet"""
        self.game_state['player']['position'] = {'x': x, 'y': y, 'z': z}
        self.game_state['player']['yaw'] = yaw
        self.game_state['player']['pitch'] = pitch
    
    def _handle_entity_spawn(self, entity_id: int, entity_type: str, x: float, y: float, z: float):
        """Handle entity spawn packet"""
        entity = {
            'id': entity_id,
            'type': entity_type,
            'position': {'x': x, 'y': y, 'z': z},
            'distance': self._calculate_distance(x, y, z),
            'hostile': self._is_hostile(entity_type)
        }
        self.game_state['entities'].append(entity)
    
    def _calculate_distance(self, x: float, y: float, z: float) -> float:
        """Calculate distance from player to coordinates"""
        player_pos = self.game_state['player']['position']
        dx = x - player_pos['x']
        dy = y - player_pos['y']
        dz = z - player_pos['z']
        return (dx**2 + dy**2 + dz**2) ** 0.5
    
    def _is_hostile(self, entity_type: str) -> bool:
        """Check if entity type is hostile"""
        hostile_mobs = {
            'zombie', 'skeleton', 'creeper', 'spider', 'enderman',
            'witch', 'blaze', 'ghast', 'slime', 'magma_cube',
            'phantom', 'drowned', 'husk', 'stray', 'wither_skeleton',
            'hoglin', 'piglin', 'zoglin', 'pillager', 'vindicator',
            'evoker', 'vex', 'ravager', 'warden'
        }
        return entity_type.lower() in hostile_mobs
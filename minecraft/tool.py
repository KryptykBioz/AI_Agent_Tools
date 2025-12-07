# Filename: BASE/tools/installed/minecraft/tool.py
"""
Minecraft Tool - Simplified Architecture
Single master class with start() and end() lifecycle
Includes context loop for game state awareness and proactive reactions
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from BASE.handlers.base_tool import BaseTool
import requests


class MinecraftTool(BaseTool):
    """
    Minecraft bot control with full command execution and vision
    Proactively injects game state context into thought buffer via context loop
    """
    
    @property
    def name(self) -> str:
        return "minecraft"
    
    def has_context_loop(self) -> bool:
        """Enable background context loop for game state awareness"""
        return True
    
    async def initialize(self) -> bool:
        """
        Initialize Minecraft bot system
        
        Returns:
            True if initialization successful (always returns True for graceful degradation)
        """
        # Get API configuration
        self.api_host = getattr(self._controls, 'MINECRAFT_API_HOST', 'http://127.0.0.1')
        self.api_port = getattr(self._controls, 'MINECRAFT_API_PORT', 3001)
        self.api_base = f"{self.api_host}:{self.api_port}"
        
        # Connection state
        self._last_vision_data = None
        self._connection_verified = False
        self._last_health = 20
        self._last_food = 20
        self._last_context_time = 0
        
        # Verify connection on init
        self._verify_connection()
        
        if self._logger:
            if self._connection_verified:
                self._logger.system(
                    f"[Minecraft] Bot ready: Connected (API: {self.api_base})"
                )
            else:
                self._logger.warning(
                    f"[Minecraft] Bot not connected or API unavailable (API: {self.api_base})"
                )
        
        # Always return True for graceful degradation
        return True
    
    async def cleanup(self):
        """Cleanup Minecraft interface resources"""
        self._connection_verified = False
        self._last_vision_data = None
        
        if self._logger:
            self._logger.system("[Minecraft] Cleanup complete")
    
    def is_available(self) -> bool:
        """
        Check if Minecraft bot is ready
        
        Returns:
            True if bot is connected and spawned
        """
        if self._connection_verified:
            return True
        
        return self._verify_connection()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get Minecraft bot status
        
        Returns:
            Status dictionary with connection info
        """
        if not self._connection_verified:
            return {
                'available': False,
                'connected': False,
                'api_base': self.api_base
            }
        
        try:
            response = requests.get(
                f"{self.api_base}/api/health",
                timeout=2.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'available': True,
                    'connected': data.get('botConnected', False),
                    'spawned': data.get('botSpawned', False),
                    'api_base': self.api_base
                }
        except:
            pass
        
        return {
            'available': False,
            'connected': False,
            'api_base': self.api_base
        }
    
    def _verify_connection(self) -> bool:
        """Verify bot is connected and spawned"""
        try:
            response = requests.get(
                f"{self.api_base}/api/health",
                timeout=2.0
            )
            
            if response.status_code == 200:
                data = response.json()
                is_ready = (
                    data.get('botConnected', False) and 
                    data.get('botSpawned', False)
                )
                
                self._connection_verified = is_ready
                
                if self._logger:
                    status = "[OK]" if is_ready else "[FAIL]"
                    self._logger.tool(
                        f"[Minecraft] {status} Bot health: "
                        f"connected={data.get('botConnected')}, "
                        f"spawned={data.get('botSpawned')}"
                    )
                
                return is_ready
            
            return False
            
        except Exception as e:
            if self._logger:
                self._logger.warning(f"[Minecraft] Health check failed: {e}")
            self._connection_verified = False
            return False
    
    async def context_loop(self, thought_buffer):
        """
        Background loop for game state awareness
        Retrieves game environmental data every 5 seconds and injects into thought buffer
        
        Args:
            thought_buffer: ThoughtBuffer instance for injecting game state
        """
        if self._logger:
            self._logger.system("[Minecraft] Context loop started (5s interval)")
        
        while self._running:
            try:
                # Check if bot is available
                if not self.is_available():
                    if self._logger:
                        self._logger.tool("[Minecraft] Bot not available, waiting 10s...")
                    await asyncio.sleep(10.0)
                    continue
                
                # Retrieve game environmental data
                context = self._get_game_context()
                
                if context:
                    # Parse vision data for urgency calculation
                    vision = self._last_vision_data
                    if vision:
                        health = vision.get('health', 20)
                        food = vision.get('food', 20)
                        hostile_count = len([e for e in vision.get('entitiesInSight', []) if e.get('isHostile')])
                        
                        # Calculate urgency level
                        urgency = self._calculate_urgency(health, food, hostile_count)
                        
                        # Inject formatted context into thought buffer
                        thought_buffer.add_processed_thought(
                            content=context,
                            source='minecraft_state',
                            urgency_override=urgency
                        )
                        
                        if self._logger:
                            self._logger.tool(
                                f"[Minecraft] Injected game state (urgency: {urgency}, "
                                f"health: {health}, food: {food}, hostiles: {hostile_count})"
                            )
                        
                        # Track changes for future comparison
                        self._last_health = health
                        self._last_food = food
                        self._last_context_time = time.time()
                else:
                    if self._logger:
                        self._logger.tool("[Minecraft] No context data retrieved")
                
                # Wait 5 seconds before next retrieval
                await asyncio.sleep(5.0)
                
            except asyncio.CancelledError:
                # Normal cancellation when tool is disabled
                if self._logger:
                    self._logger.system("[Minecraft] Context loop cancelled (tool disabled)")
                break
                
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[Minecraft] Context loop error: {e}")
                # Continue running despite errors, wait 5s before retry
                await asyncio.sleep(5.0)
        
        if self._logger:
            self._logger.system("[Minecraft] Context loop stopped")
    
    def _calculate_urgency(self, health: int, food: int, hostile_count: int) -> int:
        """
        Calculate urgency level for context injection
        
        Args:
            health: Current health (0-20)
            food: Current food (0-20)
            hostile_count: Number of nearby hostile mobs
            
        Returns:
            Urgency level (1-10)
        """
        urgency = 5  # Default baseline
        
        # Critical health
        if health < 6:
            urgency = 10
        elif health < 10:
            urgency = 8
        
        # Low food
        if food < 4:
            urgency = max(urgency, 9)
        elif food < 6:
            urgency = max(urgency, 7)
        
        # Hostile threats
        if hostile_count >= 3:
            urgency = max(urgency, 9)
        elif hostile_count >= 1:
            urgency = max(urgency, 7)
        
        return urgency
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute Minecraft bot command
        
        Commands:
        - gather_resource: [resource, optional_count]
        - goto_location: [x, y, z]
        - move_direction: [direction, distance]
        - attack_entity: [entity]
        - stop_movement: []
        - follow: [target]
        - craft_item: [item, optional_count]
        - use_item: [item]
        - chat: [message]
        - build: [structure, optional_size]
        
        Args:
            command: Command name
            args: Command arguments as defined in information.json
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[Minecraft] Command: '{command}', args: {args}")
        
        # Check availability
        if not self.is_available():
            return self._error_result(
                'Minecraft bot is not connected or not spawned',
                guidance='Check bot connection and ensure it has spawned in world'
            )
        
        # Validate command
        if not command:
            return self._error_result(
                'No command provided',
                guidance='Use minecraft.gather_resource, minecraft.goto_location, etc.'
            )
        
        # Translate generic command to bot's action format
        bot_command = self._translate_to_bot_action(command, args)
        
        if not bot_command:
            return self._error_result(
                f'Unknown command: {command}',
                guidance='Available commands: gather_resource, goto_location, move_direction, attack_entity, stop_movement, follow, craft_item, use_item, chat, build'
            )
        
        # Send structured command to bot API
        try:
            if self._logger:
                self._logger.tool(f"[Minecraft] Sending: {bot_command}")
            
            response = requests.post(
                f"{self.api_base}/api/action",
                json=bot_command,
                headers={'Content-Type': 'application/json'},
                timeout=15.0
            )
            
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_data.get('message', error_msg))
                except:
                    error_msg = response.text[:200] if response.text else error_msg
                
                return self._error_result(
                    f'Command failed: {error_msg}',
                    guidance='Check bot logs for details'
                )
            
            result = response.json()
            success = result.get('status') == 'success'
            message = result.get('message', 'Command executed')
            
            if self._logger:
                status_icon = "[OK]" if success else "[FAIL]"
                self._logger.tool(
                    f"[Minecraft] {status_icon} {bot_command['action']} -> {message}"
                )
            
            return self._success_result(
                message,
                metadata={
                    'bot_action': bot_command['action'],
                    'bot_args': bot_command['args'],
                    'raw_result': result
                }
            )
            
        except requests.exceptions.Timeout:
            if self._logger:
                self._logger.warning(f"[Minecraft] Command timeout: {bot_command}")
            return self._error_result(
                'Command timed out after 15 seconds',
                guidance='Bot may be busy - try again or use stop_movement first'
            )
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Minecraft] Execution error: {e}")
            return self._error_result(
                f'Execution error: {str(e)[:200]}',
                guidance='Check bot connection and API availability'
            )
    
    def _translate_to_bot_action(self, command: str, args: list) -> Optional[dict]:
        """
        Translate generic game command to bot's action format
        
        Args:
            command: Generic command name
            args: Command arguments
            
        Returns:
            {"action": "gather", "args": ["wood", 1]} or None
        """
        # Command mapping
        command_map = {
            'gather_resource': 'gather',
            'goto_location': 'goto',
            'move_direction': 'move',
            'attack_entity': 'attack',
            'stop_movement': 'stop',
            'use_item': 'use',
            'craft_item': 'craft',
            # Direct mappings (already bot action names)
            'follow': 'follow',
            'come': 'come',
            'build': 'build',
            'give': 'give',
            'trade': 'trade',
            'chat': 'chat',
            'defend': 'defend',
            'flee': 'flee',
            'equip': 'equip',
            'look': 'look',
            'status': 'status'
        }
        
        bot_action = command_map.get(command)
        
        if not bot_action:
            if self._logger:
                self._logger.warning(f"[Minecraft] Unknown command: {command}")
            return None
        
        # Build structured command for bot
        return {
            'action': bot_action,
            'args': args if args else []
        }
    
    def _get_game_context(self) -> Optional[str]:
        """
        Get current game state from vision endpoint
        Returns formatted context text with ALL data and coordinates
        
        Returns:
            Formatted context string or None if unavailable
        """
        if not self.is_available():
            return None
        
        try:
            response = requests.get(
                f"{self.api_base}/api/vision",
                timeout=3.0
            )
            
            if response.status_code != 200:
                if self._logger:
                    self._logger.warning(f"[Minecraft] Vision request failed: {response.status_code}")
                return None
            
            data = response.json()
            
            if data.get('status') != 'success':
                if self._logger:
                    self._logger.warning(f"[Minecraft] Vision error: {data.get('error', 'Unknown')}")
                return None
            
            vision = data.get('vision', {})
            self._last_vision_data = vision
            
            # Format complete vision context with ALL data
            return self._format_vision_context(vision)
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Minecraft] Context error: {e}")
            return None
    
    def _format_vision_context(self, vision: Dict) -> str:
        """Format vision data with ALL coordinates and NO truncation"""
        lines = ["## Minecraft Bot Status"]
        
        # === SURVIVAL STATUS (Critical Info First) ===
        health = vision.get('health', 0)
        food = vision.get('food', 0)
        
        status_line = f"**Health: {health}/20 | Food: {food}/20**"
        if health < 10:
            status_line += " [!] LOW HEALTH"
        if food < 6:
            status_line += " [!] HUNGRY"
        lines.append(status_line)
        
        # === POSITION & ENVIRONMENT ===
        pos = vision.get('position', {})
        x, y, z = pos.get('x', 0), pos.get('y', 0), pos.get('z', 0)
        lines.append(f"\n**Location:** ({x:.1f}, {y:.1f}, {z:.1f})")
        
        # Biome with context
        biome = vision.get('biome', 'unknown')
        if biome and biome != 'unknown':
            lines.append(f"**Biome:** {biome.replace('_', ' ').title()}")
        
        # Time/Weather with gameplay implications
        time_info = vision.get('time', {})
        weather = vision.get('weather', {})
        phase = time_info.get('phase', 'unknown')
        tick = time_info.get('timeOfDay', 0)
        raining = weather.get('isRaining', False)
        thundering = weather.get('isThundering', False)
        
        time_str = phase.title()
        if thundering:
            time_str += " THUNDER (hostile spawns, fire risk)"
        elif raining:
            time_str += " RAIN (no fire, filled cauldrons)"
        elif phase == 'night':
            time_str += " (hostile mobs spawning)"
        elif phase == 'day':
            time_str += " (safe from spawns)"
        
        lines.append(f"**Time:** {time_str} (tick: {tick})")
        
        # === INVENTORY DETAILS ===
        lines.append("\n**Inventory:**")
        inventory = vision.get('inventory', {})
        item_in_hand = inventory.get('itemInHand')
        
        if item_in_hand:
            item_name = item_in_hand.get('name', 'unknown')
            item_count = item_in_hand.get('count', 1)
            durability = item_in_hand.get('durability', 0)
            max_durability = item_in_hand.get('maxDurability')
            
            hand_str = f"  Holding: {item_name} x{item_count}"
            if max_durability and durability > 0:
                durability_percent = ((max_durability - durability) / max_durability * 100)
                hand_str += f" ({durability_percent:.0f}% durability)"
            lines.append(hand_str)
        else:
            lines.append("  Holding: empty hand")
        
        # Show ALL categorized items
        categories = inventory.get('categories', {})
        total_items = inventory.get('totalItems', 0)
        
        if total_items > 0:
            lines.append(f"  Total: {total_items} items")
            
            for category, icon in [
                ('tools', '[T]'), ('weapons', '[W]'), ('armor', '[A]'),
                ('food', '[F]'), ('ores', '[O]'), ('blocks', '[B]'),
                ('resources', '[R]')
            ]:
                if categories.get(category):
                    items_str = ', '.join([f"{i['name']} x{i['count']}" for i in categories[category]])
                    lines.append(f"  {icon} {category.title()}: {items_str}")
        else:
            lines.append("  Empty inventory")
        
        # === NEARBY ENTITIES - ALL WITH COORDINATES ===
        entities = vision.get('entitiesInSight', [])
        if entities:
            lines.append("\n**Nearby Entities:**")
            
            # Hostile mobs
            hostile = [e for e in entities if e.get('isHostile')]
            if hostile:
                lines.append(f"  [!] HOSTILES ({len(hostile)}):")
                for mob in hostile:
                    coords = mob.get('coordinates', {})
                    threat = mob.get('threatLevel', 5)
                    threat_indicator = "[HIGH]" if threat >= 8 else "[MED]" if threat >= 6 else "[LOW]"
                    lines.append(
                        f"    {threat_indicator} {mob.get('type', 'unknown')} at "
                        f"({coords.get('x', 0)}, {coords.get('y', 0)}, {coords.get('z', 0)}) - "
                        f"{mob.get('distance', 0):.1f}m {mob.get('direction', 'unknown')} (threat: {threat}/10)"
                    )
            
            # Passive mobs
            passive = [e for e in entities if e.get('isPassive', False)]
            if passive:
                lines.append(f"  Passive Animals ({len(passive)}):")
                for mob in passive[:10]:  # Limit passive to 10 for brevity
                    coords = mob.get('coordinates', {})
                    lines.append(
                        f"    - {mob.get('type', 'unknown')} at "
                        f"({coords.get('x', 0)}, {coords.get('y', 0)}, {coords.get('z', 0)}) - "
                        f"{mob.get('distance', 0):.1f}m {mob.get('direction', 'unknown')}"
                    )
            
            # Players
            players = [e for e in entities if e.get('isPlayer')]
            if players:
                lines.append(f"  Players ({len(players)}):")
                for player in players:
                    coords = player.get('coordinates', {})
                    lines.append(
                        f"    - {player.get('username', player.get('type', 'unknown'))} at "
                        f"({coords.get('x', 0)}, {coords.get('y', 0)}, {coords.get('z', 0)}) - "
                        f"{player.get('distance', 0):.1f}m {player.get('direction', 'unknown')}"
                    )
        else:
            lines.append("\n**Nearby Entities:** None visible")
        
        # === VISIBLE BLOCKS - PROXIMITY-BASED ===
        blocks = vision.get('blocksInSight', [])
        if blocks:
            lines.append(f"\n**Nearby Blocks ({len(blocks)} visible):**")
            
            # Sort by distance and group by proximity
            blocks_sorted = sorted(blocks, key=lambda b: b.get('distance', 999))
            
            immediate = [b for b in blocks_sorted if b.get('distance', 99) <= 5]
            close = [b for b in blocks_sorted if 5 < b.get('distance', 99) <= 10]
            
            if immediate:
                lines.append(f"  **Immediate (<=5m):** {len(immediate)} blocks")
                for block in immediate[:10]:
                    pos = block.get('position', {})
                    btype = block.get('type', 'other')
                    icon = {'ore': '[O]', 'wood': '[W]', 'crafted': '[C]'}.get(btype, '-')
                    lines.append(
                        f"    {icon} {block['name']} at "
                        f"({pos['x']}, {pos['y']}, {pos['z']}) - {block.get('distance', 0):.1f}m"
                    )
            
            if close:
                lines.append(f"  **Close (5-10m):** {len(close)} blocks (showing top 5)")
                for block in close[:5]:
                    pos = block.get('position', {})
                    lines.append(
                        f"    - {block['name']} at "
                        f"({pos['x']}, {pos['y']}, {pos['z']}) - {block.get('distance', 0):.1f}m"
                    )
        
        # === SITUATION ASSESSMENT ===
        lines.append("\n**Situation Assessment:**")
        
        issues = []
        opportunities = []
        
        if health < 10:
            issues.append("Low health - seek food/shelter")
        if food < 6:
            issues.append("Hungry - eat food or hunt animals")
        if phase == 'night' and hostile:
            issues.append(f"Night with {len(hostile)} hostiles nearby")
        
        if blocks:
            close_blocks = [b for b in blocks if b.get('distance', 999) <= 8]
            ores_nearby = [b for b in close_blocks if b.get('type') == 'ore']
            if ores_nearby:
                opportunities.append(f"{len(ores_nearby)} ore(s) within 8m")
        
        if passive:
            opportunities.append(f"{len(passive)} passive mobs for food")
        
        if issues:
            lines.append("  [!] " + " | ".join(issues))
        if opportunities:
            lines.append("  [+] " + " | ".join(opportunities))
        if not issues and not opportunities:
            lines.append("  [OK] Situation stable")
        
        return '\n'.join(lines)
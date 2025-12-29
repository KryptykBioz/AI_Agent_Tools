# Filename: BASE/tools/installed/minecraft/tool.py
"""
Minecraft Tool - HYBRID PULL-PUSH MODEL
========================================
Background: Minimal summary every 10s (~100 chars)
Critical Push: Immediate alerts for threats/opportunities
Detailed Pull: Full state on explicit agent request

This pattern scales to ANY game integration.
"""
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from BASE.handlers.base_tool import BaseTool
import requests


class MinecraftTool(BaseTool):
    """
    Minecraft bot control with hybrid context model
    - Minimal background awareness (no spam)
    - Critical event alerts (immediate)
    - Detailed state on demand (explicit calls)
    """
    
    @property
    def name(self) -> str:
        return "minecraft"
    
    def has_context_loop(self) -> bool:
        """Enable background context loop for minimal summaries"""
        return True
    
    async def initialize(self) -> bool:
        """Initialize Minecraft bot system"""
        # Get API configuration
        self.api_host = getattr(self._controls, 'MINECRAFT_API_HOST', 'http://127.0.0.1')
        self.api_port = getattr(self._controls, 'MINECRAFT_API_PORT', 3001)
        self.api_base = f"{self.api_host}:{self.api_port}"
        
        # Connection state
        self._last_vision_data = None
        self._connection_verified = False
        
        # State tracking for change detection
        self._last_health = 20
        self._last_food = 20
        self._last_hostile_count = 0
        self._known_hostile_types = set()
        self._last_context_time = 0
        
        # Critical event thresholds (configurable)
        self.CRITICAL_HEALTH_THRESHOLD = 8  # HP < 8 = critical
        self.LOW_HEALTH_THRESHOLD = 10      # HP < 10 = warning
        self.LOW_FOOD_THRESHOLD = 6         # Food < 6 = hungry
        self.HOSTILE_DISTANCE_ALERT = 5.0   # Hostile < 5m = alert
        self.HEALTH_DROP_ALERT = 5          # HP drops 5+ = alert
        
        # Verify connection on init
        self._verify_connection()
        
        if self._logger:
            if self._connection_verified:
                self._logger.system(
                    f"[Minecraft] Bot ready: Connected (Hybrid Model)"
                )
            else:
                self._logger.warning(
                    f"[Minecraft] Bot not connected (API: {self.api_base})"
                )
        
        return True
    
    async def cleanup(self):
        """Cleanup Minecraft interface resources"""
        self._connection_verified = False
        self._last_vision_data = None
        
        if self._logger:
            self._logger.system("[Minecraft] Cleanup complete")
    
    def is_available(self) -> bool:
        """Check if Minecraft bot is ready"""
        if self._connection_verified:
            return True
        
        return self._verify_connection()
    
    def get_status(self) -> Dict[str, Any]:
        """Get Minecraft bot status"""
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
                return is_ready
            
            return False
            
        except Exception as e:
            if self._logger:
                self._logger.warning(f"[Minecraft] Health check failed: {e}")
            self._connection_verified = False
            return False
    
    # ========================================================================
    # CONTEXT LOOP - HYBRID MODEL
    # ========================================================================
    
    async def context_loop(self, thought_buffer):
        """
        HYBRID CONTEXT LOOP
        ===================
        Every 10 seconds:
        1. Get minimal summary (~100 chars)
        2. Check for critical events
        3. Inject summary OR critical alert (never both)
        
        Agent can explicitly call get_full_status for details.
        """
        if self._logger:
            self._logger.system(
                "[Minecraft] Hybrid context loop started "
                "(10s interval, minimal summaries + critical alerts)"
            )
        
        while self._running:
            try:
                # Check if bot is available
                if not self.is_available():
                    if self._logger:
                        self._logger.tool("[Minecraft] Bot not available, waiting 15s...")
                    await asyncio.sleep(15.0)
                    continue
                
                # Get current game state
                vision = self._get_current_vision()
                
                if not vision:
                    if self._logger:
                        self._logger.tool("[Minecraft] No vision data retrieved")
                    await asyncio.sleep(10.0)
                    continue
                
                # STEP 1: Check for critical events (immediate push)
                critical_event = self._detect_critical_events(vision)
                
                if critical_event:
                    # CRITICAL EVENT - Push detailed alert immediately
                    thought_buffer.add_processed_thought(
                        content=critical_event,
                        source='minecraft_state',
                        timestamp=time.time()
                    )
                    
                    if self._logger:
                        self._logger.tool(f"[Minecraft] CRITICAL EVENT: {critical_event[:100]}")
                    
                    # Update tracking
                    self._update_state_tracking(vision)
                    
                    # Shorter wait after critical event (more responsive)
                    await asyncio.sleep(5.0)
                    continue
                
                # STEP 2: No critical events - Inject minimal summary
                summary = self._get_minimal_summary(vision)
                
                if summary:
                    thought_buffer.add_processed_thought(
                        content=summary,
                        source='minecraft_state',
                        timestamp=time.time()
                    )
                    
                    if self._logger:
                        self._logger.tool(f"[Minecraft] Summary: {summary}")
                
                # Update tracking
                self._update_state_tracking(vision)
                
                # Wait 10 seconds before next check
                await asyncio.sleep(10.0)
                
            except asyncio.CancelledError:
                if self._logger:
                    self._logger.system("[Minecraft] Context loop cancelled")
                break
                
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[Minecraft] Context loop error: {e}")
                await asyncio.sleep(10.0)
        
        if self._logger:
            self._logger.system("[Minecraft] Context loop stopped")
    
    # ========================================================================
    # MINIMAL SUMMARY (Background Awareness)
    # ========================================================================
    
    def _get_minimal_summary(self, vision: Dict) -> str:
        """
        Generate minimal one-line summary for background awareness
        
        Format: [Minecraft] HP: 15/20 | Food: 10/20 | Pos: (X,Y,Z) | Threats: 2 | Time: Night
        
        Returns ~80-120 characters total
        """
        health = vision.get('health', 0)
        food = vision.get('food', 0)
        
        # Position (rounded)
        pos = vision.get('position', {})
        x, y, z = int(pos.get('x', 0)), int(pos.get('y', 0)), int(pos.get('z', 0))
        
        # Threat count (hostile mobs only)
        entities = vision.get('entitiesInSight', [])
        hostile_count = len([e for e in entities if e.get('isHostile')])
        
        # Time phase
        time_info = vision.get('time', {})
        phase = time_info.get('phase', 'unknown').title()
        
        # Build summary
        parts = [
            f"HP: {health}/20",
            f"Food: {food}/20",
            f"Pos: ({x},{y},{z})",
            f"Threats: {hostile_count}",
            f"Time: {phase}"
        ]
        
        # Add warnings for low stats (but not critical - those trigger events)
        warnings = []
        if self.LOW_HEALTH_THRESHOLD <= health < 15:
            warnings.append("Low HP")
        if self.LOW_FOOD_THRESHOLD <= food < 10:
            warnings.append("Hungry")
        
        summary = "[Minecraft] " + " | ".join(parts)
        
        if warnings:
            summary += f" [{', '.join(warnings)}]"
        
        return summary
    
    # ========================================================================
    # CRITICAL EVENT DETECTION (Immediate Push)
    # ========================================================================
    
    def _detect_critical_events(self, vision: Dict) -> Optional[str]:
        """
        Detect critical events that require immediate attention
        
        Critical events:
        - Health drops below 8 (critical danger)
        - Health drops 5+ points suddenly (under attack)
        - New hostile within 5 meters
        - Food level at 0 (starving)
        - Valuable resource detected (diamond/emerald ore)
        
        Returns formatted alert string or None
        """
        health = vision.get('health', 0)
        food = vision.get('food', 0)
        
        entities = vision.get('entitiesInSight', [])
        hostiles = [e for e in entities if e.get('isHostile')]
        
        blocks = vision.get('blocksInSight', [])
        
        alerts = []
        
        # ================================================================
        # CRITICAL HEALTH
        # ================================================================
        if health < self.CRITICAL_HEALTH_THRESHOLD:
            health_drop = self._last_health - health
            alerts.append(
                f"[!] CRITICAL HEALTH: {health}/20 HP "
                f"(dropped {health_drop} from last check)"
            )
        
        # ================================================================
        # SUDDEN HEALTH DROP (under attack)
        # ================================================================
        elif health < self._last_health:
            health_drop = self._last_health - health
            if health_drop >= self.HEALTH_DROP_ALERT:
                alerts.append(
                    f"[!] TAKING DAMAGE: Lost {health_drop} HP "
                    f"(now {health}/20) - Under attack!"
                )
        
        # ================================================================
        # STARVING
        # ================================================================
        if food == 0:
            alerts.append(
                f"[!] STARVING: Food at 0/20 - Health will drain!"
            )
        
        # ================================================================
        # NEW CLOSE HOSTILE
        # ================================================================
        close_hostiles = [h for h in hostiles if h.get('distance', 999) < self.HOSTILE_DISTANCE_ALERT]
        
        if close_hostiles:
            # Check for new hostile types
            current_types = set(h.get('type', 'unknown') for h in close_hostiles)
            new_types = current_types - self._known_hostile_types
            
            if new_types or len(close_hostiles) > self._last_hostile_count:
                hostile_list = []
                for h in close_hostiles:
                    threat = h.get('threatLevel', 5)
                    hostile_list.append(
                        f"{h.get('type', 'unknown')} at {h.get('distance', 0):.1f}m "
                        f"(threat: {threat}/10)"
                    )
                
                alerts.append(
                    f"[!] HOSTILES NEARBY: {len(close_hostiles)} mob(s) within {self.HOSTILE_DISTANCE_ALERT}m:\n" +
                    "\n".join([f"  - {h}" for h in hostile_list])
                )
        
        # ================================================================
        # VALUABLE RESOURCE DISCOVERY
        # ================================================================
        valuable_ores = ['diamond_ore', 'emerald_ore', 'ancient_debris']
        close_blocks = [b for b in blocks if b.get('distance', 999) < 8]
        
        found_valuables = [b for b in close_blocks if b.get('name', '') in valuable_ores]
        
        if found_valuables:
            for valuable in found_valuables:
                pos = valuable.get('position', {})
                alerts.append(
                    f"[+] VALUABLE RESOURCE: {valuable.get('name', 'unknown')} "
                    f"at ({pos.get('x', 0)}, {pos.get('y', 0)}, {pos.get('z', 0)}) - "
                    f"{valuable.get('distance', 0):.1f}m away"
                )
        
        # ================================================================
        # Return combined alerts or None
        # ================================================================
        if alerts:
            return "\n".join(alerts)
        
        return None
    
    def _update_state_tracking(self, vision: Dict):
        """Update internal state tracking for change detection"""
        self._last_health = vision.get('health', 20)
        self._last_food = vision.get('food', 20)
        
        entities = vision.get('entitiesInSight', [])
        hostiles = [e for e in entities if e.get('isHostile')]
        close_hostiles = [h for h in hostiles if h.get('distance', 999) < self.HOSTILE_DISTANCE_ALERT]
        
        self._last_hostile_count = len(close_hostiles)
        self._known_hostile_types = set(h.get('type', 'unknown') for h in close_hostiles)
    
    def _get_current_vision(self) -> Optional[Dict]:
        """Get current game state from vision endpoint"""
        if not self.is_available():
            return None
        
        try:
            response = requests.get(
                f"{self.api_base}/api/vision",
                timeout=3.0
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if data.get('status') != 'success':
                return None
            
            vision = data.get('vision', {})
            self._last_vision_data = vision
            
            return vision
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Minecraft] Vision error: {e}")
            return None
    
    # ========================================================================
    # DETAILED PULL COMMANDS (Explicit Agent Requests)
    # ========================================================================
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute Minecraft bot command
        
        NEW HYBRID COMMANDS:
        - get_full_status: Get complete detailed game state
        - get_inventory: Get detailed inventory breakdown
        - get_nearby_blocks: Get blocks with coordinates
        
        EXISTING COMMANDS:
        - gather_resource, goto_location, move_direction, etc.
        """
        if self._logger:
            self._logger.tool(f"[Minecraft] Command: '{command}', args: {args}")
        
        # Check availability
        if not self.is_available():
            return self._error_result(
                'Minecraft bot is not connected or not spawned',
                guidance='Check bot connection and ensure it has spawned in world'
            )
        
        # ====================================================================
        # HYBRID PULL COMMANDS - Detailed state on demand
        # ====================================================================
        
        if command == 'get_full_status':
            return await self._get_full_status_command()
        
        if command == 'get_inventory':
            return await self._get_inventory_command()
        
        if command == 'get_nearby_blocks':
            return await self._get_nearby_blocks_command(args)
        
        # ====================================================================
        # STANDARD ACTION COMMANDS
        # ====================================================================
        
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
                guidance='Available commands: gather_resource, goto_location, get_full_status, etc.'
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
    
    async def _get_full_status_command(self) -> Dict[str, Any]:
        """
        Get complete detailed game state
        
        This is the "detailed pull" - returns everything
        """
        vision = self._get_current_vision()
        
        if not vision:
            return self._error_result(
                'Failed to retrieve game state',
                guidance='Check bot connection'
            )
        
        # Use the existing detailed formatter
        detailed_context = self._format_vision_context(vision)
        
        if self._logger:
            self._logger.tool(
                f"[Minecraft] Full status retrieved: {len(detailed_context)} chars"
            )
        
        return self._success_result(
            detailed_context,
            metadata={'type': 'full_status', 'char_count': len(detailed_context)}
        )
    
    async def _get_inventory_command(self) -> Dict[str, Any]:
        """Get detailed inventory breakdown"""
        vision = self._get_current_vision()
        
        if not vision:
            return self._error_result(
                'Failed to retrieve inventory',
                guidance='Check bot connection'
            )
        
        inventory = vision.get('inventory', {})
        
        # Format detailed inventory
        lines = ["## Inventory Details\n"]
        
        # Item in hand
        hand = inventory.get('itemInHand')
        if hand:
            holding = f"**Holding:** {hand.get('name', 'unknown')}"
            if hand.get('count', 1) > 1:
                holding += f" x{hand['count']}"
            if hand.get('maxDurability'):
                durability = hand.get('durability', 0)
                max_dur = hand.get('maxDurability')
                durability_pct = ((max_dur - durability) / max_dur * 100)
                holding += f" ({durability_pct:.0f}% durability)"
            lines.append(holding)
        else:
            lines.append("**Holding:** Empty hand")
        
        # Total items
        total = inventory.get('totalItems', 0)
        lines.append(f"\n**Total:** {total} items\n")
        
        # Categories
        categories = inventory.get('categories', {})
        for cat_name in ['tools', 'weapons', 'armor', 'food', 'ores', 'blocks', 'resources']:
            items = categories.get(cat_name, [])
            if items:
                items_str = ', '.join([f"{i['name']} x{i['count']}" for i in items])
                lines.append(f"**{cat_name.title()}:** {items_str}")
        
        result = "\n".join(lines)
        
        if self._logger:
            self._logger.tool(f"[Minecraft] Inventory retrieved: {total} items")
        
        return self._success_result(
            result,
            metadata={'type': 'inventory', 'total_items': total}
        )
    
    async def _get_nearby_blocks_command(self, args: List[Any]) -> Dict[str, Any]:
        """
        Get nearby blocks with coordinates
        
        Args:
            args[0] (optional): max_distance (default: 10)
        """
        max_distance = args[0] if args and len(args) > 0 else 10
        
        try:
            max_distance = float(max_distance)
        except:
            max_distance = 10.0
        
        vision = self._get_current_vision()
        
        if not vision:
            return self._error_result(
                'Failed to retrieve block data',
                guidance='Check bot connection'
            )
        
        blocks = vision.get('blocksInSight', [])
        
        # Filter by distance
        nearby = [b for b in blocks if b.get('distance', 999) <= max_distance]
        
        # Sort by distance
        nearby_sorted = sorted(nearby, key=lambda b: b.get('distance', 999))
        
        # Format block list
        lines = [f"## Nearby Blocks (within {max_distance}m)\n"]
        lines.append(f"Found {len(nearby_sorted)} blocks\n")
        
        for block in nearby_sorted[:30]:  # Limit to 30 for readability
            pos = block.get('position', {})
            block_type = block.get('type', 'other')
            icon = {'ore': '[O]', 'wood': '[W]', 'crafted': '[C]'}.get(block_type, '-')
            
            lines.append(
                f"{icon} **{block.get('name', 'unknown')}** at "
                f"({pos.get('x', 0)}, {pos.get('y', 0)}, {pos.get('z', 0)}) - "
                f"{block.get('distance', 0):.1f}m"
            )
        
        if len(nearby_sorted) > 30:
            lines.append(f"\n... and {len(nearby_sorted) - 30} more blocks")
        
        result = "\n".join(lines)
        
        if self._logger:
            self._logger.tool(
                f"[Minecraft] Blocks retrieved: {len(nearby_sorted)} within {max_distance}m"
            )
        
        return self._success_result(
            result,
            metadata={'type': 'blocks', 'count': len(nearby_sorted), 'max_distance': max_distance}
        )
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _translate_to_bot_action(self, command: str, args: list) -> Optional[dict]:
        """Translate generic game command to bot's action format"""
        # Command mapping
        command_map = {
            'gather_resource': 'gather',
            'goto_location': 'goto',
            'move_direction': 'move',
            'attack_entity': 'attack',
            'stop_movement': 'stop',
            'use_item': 'use',
            'craft_item': 'craft',
            # Direct mappings
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
        
        return {
            'action': bot_action,
            'args': args if args else []
        }
    
    def _format_vision_context(self, vision: Dict) -> str:
        """
        DETAILED VISION FORMATTER
        
        This is now ONLY used for explicit get_full_status calls
        No longer called by context loop
        """
        lines = ["## Minecraft Bot - Complete Status"]
        
        # === SURVIVAL STATUS ===
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
        
        biome = vision.get('biome', 'unknown')
        if biome and biome != 'unknown':
            lines.append(f"**Biome:** {biome.replace('_', ' ').title()}")
        
        time_info = vision.get('time', {})
        weather = vision.get('weather', {})
        phase = time_info.get('phase', 'unknown')
        tick = time_info.get('timeOfDay', 0)
        raining = weather.get('isRaining', False)
        thundering = weather.get('isThundering', False)
        
        time_str = phase.title()
        if thundering:
            time_str += " THUNDER"
        elif raining:
            time_str += " RAIN"
        
        lines.append(f"**Time:** {time_str} (tick: {tick})")
        
        # === INVENTORY ===
        lines.append("\n**Inventory:**")
        inventory = vision.get('inventory', {})
        item_in_hand = inventory.get('itemInHand')
        
        if item_in_hand:
            hand_str = f"  Holding: {item_in_hand.get('name', 'unknown')} x{item_in_hand.get('count', 1)}"
            lines.append(hand_str)
        else:
            lines.append("  Holding: empty hand")
        
        categories = inventory.get('categories', {})
        total_items = inventory.get('totalItems', 0)
        
        if total_items > 0:
            lines.append(f"  Total: {total_items} items")
            
            for category, icon in [
                ('tools', '[T]'), ('weapons', '[W]'), ('armor', '[A]'),
                ('food', '[F]'), ('ores', '[O]'), ('blocks', '[B]')
            ]:
                if categories.get(category):
                    items_str = ', '.join([f"{i['name']} x{i['count']}" for i in categories[category]])
                    lines.append(f"  {icon} {category.title()}: {items_str}")
        
        # === ENTITIES ===
        entities = vision.get('entitiesInSight', [])
        if entities:
            lines.append("\n**Nearby Entities:**")
            
            hostile = [e for e in entities if e.get('isHostile')]
            if hostile:
                lines.append(f"  [!] HOSTILES ({len(hostile)}):")
                for mob in hostile:
                    coords = mob.get('coordinates', {})
                    threat = mob.get('threatLevel', 5)
                    lines.append(
                        f"    {mob.get('type', 'unknown')} at "
                        f"({coords.get('x', 0)}, {coords.get('y', 0)}, {coords.get('z', 0)}) - "
                        f"{mob.get('distance', 0):.1f}m (threat: {threat}/10)"
                    )
            
            passive = [e for e in entities if e.get('isPassive', False)]
            if passive:
                lines.append(f"  Passive Animals ({len(passive)}):")
                for mob in passive[:5]:
                    coords = mob.get('coordinates', {})
                    lines.append(
                        f"    {mob.get('type', 'unknown')} at "
                        f"({coords.get('x', 0)}, {coords.get('y', 0)}, {coords.get('z', 0)}) - "
                        f"{mob.get('distance', 0):.1f}m"
                    )
        
        # === BLOCKS ===
        blocks = vision.get('blocksInSight', [])
        if blocks:
            blocks_sorted = sorted(blocks, key=lambda b: b.get('distance', 999))
            
            immediate = [b for b in blocks_sorted if b.get('distance', 99) <= 5]
            
            if immediate:
                lines.append(f"\n**Immediate Blocks (≤5m):** {len(immediate)}")
                for block in immediate[:10]:
                    pos = block.get('position', {})
                    lines.append(
                        f"  {block['name']} at "
                        f"({pos['x']}, {pos['y']}, {pos['z']}) - "
                        f"{block.get('distance', 0):.1f}m"
                    )
        
        return '\n'.join(lines)
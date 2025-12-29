# Filename: BASE/tools/installed/dice_roller/tool.py
"""
Dice Roller Tool - For tabletop RPGs and gaming
Supports standard RPG dice (d4, d6, d8, d10, d12, d20, d100)
with advanced features like advantage/disadvantage, modifiers, and statistics
"""
from typing import List, Dict, Any
import random
import re
from collections import Counter


class DiceRollerTool:
    """
    Dice rolling tool for tabletop RPGs
    
    Inherits from BaseTool and provides comprehensive dice rolling functionality
    including standard dice, modifiers, advantage/disadvantage, and roll statistics.
    """
    
    def __init__(self, config, controls, logger=None):
        """Initialize dice roller tool"""
        # Import BaseTool to inherit from
        from BASE.handlers.base_tool import BaseTool
        
        # Store initialization parameters
        self._config = config
        self._controls = controls
        self._logger = logger
        self._running = False
        
        # Tool state
        self._roll_history = []
        self._max_history = 100
        
        # Supported dice types
        self._standard_dice = [4, 6, 8, 10, 12, 20, 100]
    
    # ==================== REQUIRED METHODS ====================
    
    @property
    def name(self) -> str:
        """Return tool name matching control variable"""
        return "dice_roller"
    
    async def initialize(self) -> bool:
        """
        Initialize the dice roller
        Simple initialization - no external connections needed
        """
        try:
            # Clear history on initialization
            self._roll_history.clear()
            
            if self._logger:
                self._logger.success(
                    f"[{self.name}] Initialized - Ready to roll!"
                )
            
            return True
        
        except Exception as e:
            if self._logger:
                self._logger.error(
                    f"[{self.name}] Initialization failed: {e}"
                )
            return False
    
    async def cleanup(self):
        """
        Cleanup dice roller resources
        Save final statistics if needed
        """
        if self._logger:
            total_rolls = len(self._roll_history)
            self._logger.system(
                f"[{self.name}] Cleaned up - {total_rolls} rolls in session"
            )
        
        # Clear history
        self._roll_history.clear()
    
    def is_available(self) -> bool:
        """Dice roller is always available once initialized"""
        return self._running
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute dice rolling commands
        
        Supported commands:
        - roll: Roll dice with standard notation (XdY+Z)
        - advantage: Roll with advantage (2d20, keep highest)
        - disadvantage: Roll with disadvantage (2d20, keep lowest)
        - stats: Get statistics for a dice type
        - history: View recent roll history
        - clear_history: Clear roll history
        """
        if not self.is_available():
            return self._error_result(
                "Dice roller not available",
                guidance="Tool must be initialized first"
            )
        
        try:
            # Route to appropriate handler
            if command == "roll":
                return await self._handle_roll(args)
            elif command == "advantage":
                return await self._handle_advantage(args)
            elif command == "disadvantage":
                return await self._handle_disadvantage(args)
            elif command == "stats":
                return await self._handle_stats(args)
            elif command == "history":
                return await self._handle_history(args)
            elif command == "clear_history":
                return await self._handle_clear_history(args)
            else:
                return self._error_result(
                    f"Unknown command: {command}",
                    guidance="Available commands: roll, advantage, disadvantage, stats, history, clear_history"
                )
        
        except Exception as e:
            return self._error_result(
                f"Command execution failed: {e}",
                guidance=f"Error executing {command}"
            )
    
    # ==================== COMMAND HANDLERS ====================
    
    async def _handle_roll(self, args: List[Any]) -> Dict[str, Any]:
        """
        Handle standard dice roll command
        
        Args format: [notation: str]
        Example: ["3d6+5"] or ["2d20"] or ["1d100-10"]
        """
        if not args or len(args) < 1:
            return self._error_result(
                "Missing dice notation",
                guidance="Usage: roll ['XdY+Z'] where X=count, Y=sides, Z=modifier (optional)"
            )
        
        notation = str(args[0]).strip().lower()
        
        # Parse dice notation
        parsed = self._parse_dice_notation(notation)
        if not parsed:
            return self._error_result(
                f"Invalid dice notation: {notation}",
                guidance="Use format: XdY+Z (e.g., 3d6+5, 2d20, 1d100-10)"
            )
        
        count, sides, modifier = parsed
        
        # Validate dice type
        if sides not in self._standard_dice:
            return self._error_result(
                f"Unsupported die type: d{sides}",
                guidance=f"Supported dice: {', '.join(f'd{d}' for d in self._standard_dice)}"
            )
        
        # Validate count
        if count < 1 or count > 100:
            return self._error_result(
                f"Invalid dice count: {count}",
                guidance="Count must be between 1 and 100"
            )
        
        # Roll the dice
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + modifier
        
        # Store in history
        self._add_to_history({
            'notation': notation,
            'rolls': rolls,
            'modifier': modifier,
            'total': total,
            'type': 'standard'
        })
        
        # Format result
        if count == 1:
            result_str = f"Rolled {notation}: **{rolls[0]}**"
            if modifier != 0:
                result_str += f" {modifier:+d} = **{total}**"
        else:
            rolls_str = ", ".join(str(r) for r in rolls)
            result_str = f"Rolled {notation}: [{rolls_str}]"
            if modifier != 0:
                result_str += f" {modifier:+d} = **{total}**"
            else:
                result_str += f" = **{total}**"
        
        return self._success_result(
            result_str,
            metadata={
                'notation': notation,
                'rolls': rolls,
                'modifier': modifier,
                'total': total,
                'min_possible': count + modifier,
                'max_possible': count * sides + modifier
            }
        )
    
    async def _handle_advantage(self, args: List[Any]) -> Dict[str, Any]:
        """
        Handle advantage roll (roll 2d20, keep highest)
        
        Args format: [modifier: Optional[int]]
        Example: [] or [5] or [-2]
        """
        modifier = 0
        if args and len(args) > 0:
            try:
                modifier = int(args[0])
            except (ValueError, TypeError):
                return self._error_result(
                    f"Invalid modifier: {args[0]}",
                    guidance="Modifier must be an integer"
                )
        
        # Roll 2d20
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        kept = max(roll1, roll2)
        total = kept + modifier
        
        # Store in history
        self._add_to_history({
            'notation': f'2d20 (advantage) {modifier:+d}' if modifier else '2d20 (advantage)',
            'rolls': [roll1, roll2],
            'kept': kept,
            'modifier': modifier,
            'total': total,
            'type': 'advantage'
        })
        
        # Format result
        result_str = f"Rolled with **Advantage**: [{roll1}, {roll2}] → Kept **{kept}**"
        if modifier != 0:
            result_str += f" {modifier:+d} = **{total}**"
        else:
            result_str += f" = **{total}**"
        
        return self._success_result(
            result_str,
            metadata={
                'roll1': roll1,
                'roll2': roll2,
                'kept': kept,
                'discarded': min(roll1, roll2),
                'modifier': modifier,
                'total': total
            }
        )
    
    async def _handle_disadvantage(self, args: List[Any]) -> Dict[str, Any]:
        """
        Handle disadvantage roll (roll 2d20, keep lowest)
        
        Args format: [modifier: Optional[int]]
        Example: [] or [5] or [-2]
        """
        modifier = 0
        if args and len(args) > 0:
            try:
                modifier = int(args[0])
            except (ValueError, TypeError):
                return self._error_result(
                    f"Invalid modifier: {args[0]}",
                    guidance="Modifier must be an integer"
                )
        
        # Roll 2d20
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        kept = min(roll1, roll2)
        total = kept + modifier
        
        # Store in history
        self._add_to_history({
            'notation': f'2d20 (disadvantage) {modifier:+d}' if modifier else '2d20 (disadvantage)',
            'rolls': [roll1, roll2],
            'kept': kept,
            'modifier': modifier,
            'total': total,
            'type': 'disadvantage'
        })
        
        # Format result
        result_str = f"Rolled with **Disadvantage**: [{roll1}, {roll2}] → Kept **{kept}**"
        if modifier != 0:
            result_str += f" {modifier:+d} = **{total}**"
        else:
            result_str += f" = **{total}**"
        
        return self._success_result(
            result_str,
            metadata={
                'roll1': roll1,
                'roll2': roll2,
                'kept': kept,
                'discarded': max(roll1, roll2),
                'modifier': modifier,
                'total': total
            }
        )
    
    async def _handle_stats(self, args: List[Any]) -> Dict[str, Any]:
        """
        Calculate theoretical statistics for a dice type
        
        Args format: [notation: str]
        Example: ["3d6"] or ["2d20+5"]
        """
        if not args or len(args) < 1:
            return self._error_result(
                "Missing dice notation",
                guidance="Usage: stats ['XdY+Z']"
            )
        
        notation = str(args[0]).strip().lower()
        
        # Parse dice notation
        parsed = self._parse_dice_notation(notation)
        if not parsed:
            return self._error_result(
                f"Invalid dice notation: {notation}",
                guidance="Use format: XdY+Z (e.g., 3d6+5)"
            )
        
        count, sides, modifier = parsed
        
        # Calculate statistics
        min_roll = count + modifier
        max_roll = count * sides + modifier
        avg_roll = (count * (sides + 1) / 2) + modifier
        
        # Calculate distribution for reasonable dice counts
        distribution = None
        if count <= 10 and sides <= 20:
            distribution = self._calculate_distribution(count, sides, modifier)
        
        result_lines = [
            f"**Statistics for {notation}:**",
            f"• Minimum: {min_roll}",
            f"• Maximum: {max_roll}",
            f"• Average: {avg_roll:.2f}"
        ]
        
        if distribution:
            mode = max(distribution.items(), key=lambda x: x[1])
            result_lines.append(f"• Most likely: {mode[0]} ({mode[1]:.1f}%)")
        
        return self._success_result(
            "\n".join(result_lines),
            metadata={
                'notation': notation,
                'min': min_roll,
                'max': max_roll,
                'average': avg_roll,
                'distribution': distribution
            }
        )
    
    async def _handle_history(self, args: List[Any]) -> Dict[str, Any]:
        """
        Get recent roll history
        
        Args format: [count: Optional[int]]
        Example: [] or [10]
        """
        count = 10
        if args and len(args) > 0:
            try:
                count = int(args[0])
                if count < 1:
                    count = 10
                elif count > 100:
                    count = 100
            except (ValueError, TypeError):
                count = 10
        
        if not self._roll_history:
            return self._success_result(
                "No rolls in history yet",
                metadata={'history': []}
            )
        
        # Get most recent rolls
        recent = self._roll_history[-count:]
        
        # Format history
        lines = [f"**Recent rolls (last {len(recent)}):**"]
        for i, roll in enumerate(reversed(recent), 1):
            roll_type = roll.get('type', 'standard')
            notation = roll.get('notation', 'unknown')
            total = roll.get('total', 0)
            
            if roll_type in ['advantage', 'disadvantage']:
                kept = roll.get('kept', 0)
                lines.append(f"{i}. {notation} → Kept {kept} = **{total}**")
            else:
                lines.append(f"{i}. {notation} = **{total}**")
        
        return self._success_result(
            "\n".join(lines),
            metadata={
                'history': recent,
                'count': len(recent)
            }
        )
    
    async def _handle_clear_history(self, args: List[Any]) -> Dict[str, Any]:
        """Clear roll history"""
        count = len(self._roll_history)
        self._roll_history.clear()
        
        return self._success_result(
            f"Cleared {count} roll(s) from history",
            metadata={'cleared_count': count}
        )
    
    # ==================== HELPER METHODS ====================
    
    def _parse_dice_notation(self, notation: str) -> tuple:
        """
        Parse standard dice notation (XdY+Z)
        
        Returns:
            Tuple of (count, sides, modifier) or None if invalid
        """
        # Remove spaces
        notation = notation.replace(' ', '')
        
        # Pattern: XdY+Z or XdY-Z or XdY
        pattern = r'^(\d+)d(\d+)([\+\-]\d+)?$'
        match = re.match(pattern, notation)
        
        if not match:
            return None
        
        count = int(match.group(1))
        sides = int(match.group(2))
        modifier = 0
        
        if match.group(3):
            modifier = int(match.group(3))
        
        return (count, sides, modifier)
    
    def _add_to_history(self, roll_data: Dict):
        """Add roll to history, maintaining max size"""
        self._roll_history.append(roll_data)
        
        # Trim history if too large
        if len(self._roll_history) > self._max_history:
            self._roll_history = self._roll_history[-self._max_history:]
    
    def _calculate_distribution(self, count: int, sides: int, modifier: int) -> Dict[int, float]:
        """
        Calculate probability distribution for dice roll
        
        Returns:
            Dict mapping result to percentage probability
        """
        # Use simulation for complex calculations
        samples = 10000
        results = []
        
        for _ in range(samples):
            roll = sum(random.randint(1, sides) for _ in range(count)) + modifier
            results.append(roll)
        
        # Count occurrences
        counts = Counter(results)
        total = len(results)
        
        # Convert to percentages
        distribution = {
            result: (count / total) * 100
            for result, count in counts.items()
        }
        
        return dict(sorted(distribution.items()))
    
    def _success_result(self, content: str, metadata: Dict = None) -> Dict[str, Any]:
        """Create standardized success result"""
        return {
            'success': True,
            'content': content,
            'source': self.name,
            'metadata': metadata or {},
            'guidance': f'{self.name} executed successfully'
        }
    
    def _error_result(self, content: str, metadata: Dict = None, guidance: str = None) -> Dict[str, Any]:
        """Create standardized error result"""
        return {
            'success': False,
            'content': content,
            'source': self.name,
            'metadata': metadata or {},
            'guidance': guidance or f'{self.name} execution failed'
        }
    
    # ==================== LIFECYCLE MANAGEMENT ====================
    
    async def start(self, thought_buffer=None, event_loop=None):
        """Start the dice roller tool"""
        if self._running:
            if self._logger:
                self._logger.warning(f"[{self.name}] Already running")
            return
        
        # Initialize tool
        success = await self.initialize()
        
        if not success:
            if self._logger:
                self._logger.error(f"[{self.name}] Initialization failed")
            return
        
        self._running = True
        
        if self._logger:
            self._logger.success(f"[{self.name}] Tool started successfully")
    
    async def end(self):
        """Stop the dice roller tool"""
        if not self._running:
            return
        
        self._running = False
        
        # Cleanup tool
        await self.cleanup()
        
        if self._logger:
            self._logger.system(f"[{self.name}] Tool stopped")
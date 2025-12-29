# Dice Roller Tool

A comprehensive dice rolling tool for tabletop RPGs, designed to integrate with the BaseTool architecture.

## Overview

The Dice Roller provides full support for standard tabletop RPG dice with advanced features including:

- **Standard Dice Rolling**: Roll any combination of d4, d6, d8, d10, d12, d20, d100
- **Modifiers**: Add or subtract values from rolls
- **Advantage/Disadvantage**: D&D 5e style advantage and disadvantage mechanics
- **Roll History**: Track your last 100 rolls
- **Statistics**: Calculate theoretical probabilities and distributions

## Installation

1. Create the tool directory structure:
```
BASE/tools/installed/dice_roller/
├── tool.py
└── information.json
```

2. Copy both files into the directory
3. Enable the tool by setting `USE_DICE_ROLLER = true` in your controls

## Supported Dice Types

- **d4**: Four-sided die (1-4)
- **d6**: Six-sided die (1-6)
- **d8**: Eight-sided die (1-8)
- **d10**: Ten-sided die (1-10)
- **d12**: Twelve-sided die (1-12)
- **d20**: Twenty-sided die (1-20)
- **d100**: Percentile die (1-100)

## Commands

### 1. Roll (Standard Dice Rolling)

Roll dice using standard notation: `XdY+Z`
- X = number of dice (1-100)
- Y = sides per die (4, 6, 8, 10, 12, 20, or 100)
- Z = modifier (optional, can be positive or negative)

**Examples:**
```json
{"tool": "dice_roller.roll", "args": ["1d20+5"]}
// Roll one d20 and add 5

{"tool": "dice_roller.roll", "args": ["3d6"]}
// Roll three d6 (standard ability score)

{"tool": "dice_roller.roll", "args": ["4d8+3"]}
// Roll four d8 and add 3 (maybe a healing spell)

{"tool": "dice_roller.roll", "args": ["2d10-2"]}
// Roll two d10 and subtract 2

{"tool": "dice_roller.roll", "args": ["1d100"]}
// Roll percentile dice
```

**Output Format:**
- Single die: `Rolled 1d20+5: **18** +5 = **23**`
- Multiple dice: `Rolled 3d6: [4, 5, 3] = **12**`
- With modifier: `Rolled 4d8+3: [6, 2, 8, 1] +3 = **20**`

### 2. Advantage

Roll with advantage (D&D 5e): Roll 2d20 and keep the highest result.

**Examples:**
```json
{"tool": "dice_roller.advantage", "args": [5]}
// Roll with advantage, add +5 modifier

{"tool": "dice_roller.advantage", "args": []}
// Roll with advantage, no modifier
```

**Output Format:**
```
Rolled with Advantage: [15, 8] → Kept **15** +5 = **20**
```

### 3. Disadvantage

Roll with disadvantage (D&D 5e): Roll 2d20 and keep the lowest result.

**Examples:**
```json
{"tool": "dice_roller.disadvantage", "args": [-2]}
// Roll with disadvantage, subtract 2

{"tool": "dice_roller.disadvantage", "args": []}
// Roll with disadvantage, no modifier
```

**Output Format:**
```
Rolled with Disadvantage: [15, 8] → Kept **8** -2 = **6**
```

### 4. Stats (Statistical Analysis)

Calculate theoretical statistics for any dice combination.

**Examples:**
```json
{"tool": "dice_roller.stats", "args": ["3d6+5"]}
// Analyze 3d6+5 distribution

{"tool": "dice_roller.stats", "args": ["2d20"]}
// Analyze 2d20 distribution
```

**Output Format:**
```
Statistics for 3d6+5:
• Minimum: 8
• Maximum: 23
• Average: 15.50
• Most likely: 15 (12.5%)
```

### 5. History

View recent roll history (up to 100 rolls stored).

**Examples:**
```json
{"tool": "dice_roller.history", "args": [10]}
// Show last 10 rolls

{"tool": "dice_roller.history", "args": []}
// Show last 10 rolls (default)
```

**Output Format:**
```
Recent rolls (last 5):
1. 2d20 (advantage) +5 → Kept 18 = **23**
2. 3d6 = **12**
3. 1d20+5 = **17**
4. 4d8+3 = **20**
5. 2d20 (disadvantage) -2 → Kept 8 = **6**
```

### 6. Clear History

Clear all stored roll history.

**Example:**
```json
{"tool": "dice_roller.clear_history", "args": []}
```

## Common Use Cases

### D&D 5e / Pathfinder

**Ability Score Generation:**
```json
{"tool": "dice_roller.roll", "args": ["4d6"]}
// Drop lowest manually, or use for straight 3d6
{"tool": "dice_roller.roll", "args": ["3d6"]}
```

**Attack Roll:**
```json
{"tool": "dice_roller.roll", "args": ["1d20+7"]}
// Attack with +7 bonus
```

**Attack with Advantage:**
```json
{"tool": "dice_roller.advantage", "args": [7]}
```

**Saving Throw with Disadvantage:**
```json
{"tool": "dice_roller.disadvantage", "args": [3]}
```

**Damage Roll:**
```json
{"tool": "dice_roller.roll", "args": ["2d6+4"]}
// Greatsword damage with +4 STR
```

**Sneak Attack Damage:**
```json
{"tool": "dice_roller.roll", "args": ["8d6"]}
// Level 13+ rogue sneak attack
```

**Healing Spell:**
```json
{"tool": "dice_roller.roll", "args": ["4d8+5"]}
// Cure Wounds at 4th level with +5 WIS
```

### Call of Cthulhu

**Skill Check:**
```json
{"tool": "dice_roller.roll", "args": ["1d100"]}
// Roll under your skill value
```

**Sanity Loss:**
```json
{"tool": "dice_roller.roll", "args": ["1d10"]}
```

### Savage Worlds

**Standard Roll:**
```json
{"tool": "dice_roller.roll", "args": ["1d8"]}
// Trait die
```

**Exploding Dice:**
```json
{"tool": "dice_roller.roll", "args": ["1d6"]}
// If you roll max, roll again and add (manual)
```

### FATE

**FATE Dice:**
```json
{"tool": "dice_roller.roll", "args": ["4d6"]}
// Manual conversion: 1-2 = minus, 3-4 = blank, 5-6 = plus
```

## Roll Notation Guide

### Basic Format
```
XdY+Z
```
- **X**: Number of dice (1-100)
- **Y**: Sides per die (4, 6, 8, 10, 12, 20, 100)
- **Z**: Modifier (optional)

### Valid Examples
- `1d20` - Single d20
- `3d6` - Three d6
- `2d10+5` - Two d10 plus 5
- `1d100-10` - Percentile minus 10
- `4d8+3` - Four d8 plus 3
- `20d6` - Twenty d6 (fireball at max level!)

### Invalid Examples
- `d20` - Missing dice count (use `1d20`)
- `3d7` - Invalid die type (no d7)
- `1d20 + 5` - Spaces not allowed (use `1d20+5`)
- `101d6` - Too many dice (max 100)

## Features

### Automatic History Tracking
- Last 100 rolls stored automatically
- Includes full details: notation, individual rolls, modifiers, totals
- Accessible via `history` command

### Statistical Analysis
- Calculates min, max, and average for any roll
- Probability distribution for reasonable dice counts
- Identifies most likely outcomes

### Advantage/Disadvantage
- Full D&D 5e implementation
- Rolls 2d20 automatically
- Shows both rolls and which was kept
- Supports modifiers

### Comprehensive Error Handling
- Clear error messages
- Usage guidance for each command
- Validates dice types and counts

## Technical Details

### Architecture
- Inherits from `BaseTool`
- No external dependencies (pure Python)
- Async/await compatible
- Integrates with tool lifecycle management

### Performance
- Instant rolls (< 1ms typical)
- No API calls required
- No cooldown period
- Efficient history management

### Thread Safety
- All operations are atomic
- Safe for concurrent use
- No race conditions

## Troubleshooting

### "Invalid dice notation" Error
- Check format: must be `XdY+Z` or `XdY-Z`
- No spaces allowed in notation
- Dice count must be 1-100
- Die type must be 4, 6, 8, 10, 12, 20, or 100

### "Unsupported die type" Error
- Only standard RPG dice supported
- Use d4, d6, d8, d10, d12, d20, or d100
- No custom dice sizes (e.g., no d7, d14, d30)

### "Invalid dice count" Error
- Must roll at least 1 die
- Maximum 100 dice per roll
- Use multiple rolls if you need more

## Future Enhancements (Potential)

- [ ] Custom dice sizes
- [ ] Drop lowest/highest (e.g., 4d6 drop lowest)
- [ ] Exploding dice (roll again on max)
- [ ] Dice pools (count successes)
- [ ] Fate dice (-, 0, +)
- [ ] Named macros (save common rolls)
- [ ] Multi-roll commands
- [ ] Graphical probability curves

## License

Part of the BASE tool architecture.

## Support

For issues or questions, refer to the main BASE documentation.
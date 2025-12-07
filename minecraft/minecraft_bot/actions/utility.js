/**
 * actions/utility.js - Utility and miscellaneous actions
 */

const { currentMcData } = require('../bot');

/**
 * Get bot status
 */
async function executeStatus(bot) {
  const pos = bot.entity.position;
  const health = bot.health;
  const food = bot.food;
  
  return {
    status: 'success',
    action: 'status',
    message: `Position: (${Math.round(pos.x)}, ${Math.round(pos.y)}, ${Math.round(pos.z)}), Health: ${health}/20, Food: ${food}/20`,
    data: {
      position: { x: pos.x, y: pos.y, z: pos.z },
      health,
      food,
      gameMode: bot.game?.gameMode || 'unknown'
    }
  };
}

/**
 * Equip an item from inventory
 */
async function executeEquip(bot, itemName) {
  console.log(`[Utility] Equipping ${itemName}`);
  
  try {
    const mcData = currentMcData(bot);
    if (!mcData) {
      return { status: 'error', message: 'Minecraft data not available' };
    }
    
    const item = mcData.itemsByName[itemName];
    if (!item) {
      return { status: 'error', message: `Unknown item: ${itemName}` };
    }
    
    const inventoryItem = bot.inventory.items().find(i => i.type === item.id);
    if (!inventoryItem) {
      return { status: 'error', message: `No ${itemName} in inventory` };
    }
    
    // Determine destination slot
    let destination = 'hand';
    if (itemName.includes('helmet')) destination = 'head';
    else if (itemName.includes('chestplate')) destination = 'torso';
    else if (itemName.includes('leggings')) destination = 'legs';
    else if (itemName.includes('boots')) destination = 'feet';
    
    await bot.equip(inventoryItem, destination);
    
    return {
      status: 'success',
      action: 'equip',
      message: `Equipped ${itemName}`,
      item: itemName,
      slot: destination
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'equip',
      message: `Failed to equip: ${err.message}`
    };
  }
}

/**
 * Craft an item
 */
async function executeCraft(bot, itemName) {
  console.log(`[Utility] Crafting ${itemName}`);
  
  return {
    status: 'error',
    action: 'craft',
    message: 'Crafting system not yet implemented'
  };
}

/**
 * Use/activate a block or item
 */
async function executeUse(bot, targetName) {
  console.log(`[Utility] Using ${targetName}`);
  
  try {
    const mcData = currentMcData(bot);
    if (!mcData) {
      return { status: 'error', message: 'Minecraft data not available' };
    }
    
    // Try to find the block nearby
    const block = mcData.blocksByName[targetName];
    if (block) {
      const targetBlock = bot.findBlock({
        matching: block.id,
        maxDistance: 5
      });
      
      if (targetBlock) {
        await bot.activateBlock(targetBlock);
        return {
          status: 'success',
          action: 'use',
          message: `Used ${targetName}`,
          target: targetName
        };
      }
    }
    
    return {
      status: 'error',
      action: 'use',
      message: `Cannot find ${targetName} nearby`
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'use',
      message: `Failed to use: ${err.message}`
    };
  }
}

/**
 * Look at a target
 */
/**
 * Look at a target
 */
async function executeLook(bot, targetName) {
  // Handle missing/undefined target - look at what bot is currently looking at
  if (!targetName || targetName === 'undefined' || targetName.trim() === '') {
    console.log(`[Utility] Looking at current view`);
    try {
      const block = bot.blockAtCursor(5);
      if (block) {
        return {
          status: 'success',
          action: 'look',
          message: `Looking at ${block.name} at (${block.position.x}, ${block.position.y}, ${block.position.z})`,
          target: block.name
        };
      } else {
        return {
          status: 'success',
          action: 'look',
          message: 'Looking around - no specific block in focus'
        };
      }
    } catch (err) {
      return {
        status: 'error',
        action: 'look',
        message: `Failed to look: ${err.message}`
      };
    }
  }
  
  console.log(`[Utility] Looking at ${targetName}`);
  
  try {
    const targetLower = targetName.toLowerCase();
    
    // Try to find player first
    const player = bot.players[targetName];
    if (player && player.entity) {
      await bot.lookAt(player.entity.position.offset(0, player.entity.height, 0));
      return {
        status: 'success',
        action: 'look',
        message: `Looking at ${targetName}`,
        target: targetName
      };
    }
    
    // Try to find entity/mob
    const entity = Object.values(bot.entities).find(e => {
      const name = (e.name || e.displayName || '').toLowerCase();
      return name.includes(targetLower);
    });
    
    if (entity) {
      await bot.lookAt(entity.position.offset(0, entity.height || 1, 0));
      return {
        status: 'success',
        action: 'look',
        message: `Looking at ${targetName}`,
        target: targetName
      };
    }
    
    // Try to find block
    const mcData = currentMcData(bot);
    if (mcData) {
      const block = mcData.blocksByName[targetLower.replace(/ /g, '_')];
      if (block) {
        const targetBlock = bot.findBlock({
          matching: block.id,
          maxDistance: 32
        });
        
        if (targetBlock) {
          await bot.lookAt(targetBlock.position.offset(0.5, 0.5, 0.5));
          return {
            status: 'success',
            action: 'look',
            message: `Looking at ${targetName}`,
            target: targetName
          };
        }
      }
    }
    
    return {
      status: 'error',
      action: 'look',
      message: `Cannot find ${targetName} to look at`
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'look',
      message: `Failed to look: ${err.message}`
    };
  }
}

/**
 * Drop an item from inventory
 */
async function executeDrop(bot, itemName, count = null) {
  console.log(`[Utility] Dropping ${count || 'all'} ${itemName}`);
  
  try {
    const mcData = currentMcData(bot);
    if (!mcData) {
      return { status: 'error', message: 'Minecraft data not available' };
    }
    
    const item = mcData.itemsByName[itemName];
    if (!item) {
      return { status: 'error', message: `Unknown item: ${itemName}` };
    }
    
    const inventoryItem = bot.inventory.items().find(i => i.type === item.id);
    if (!inventoryItem) {
      return { status: 'error', message: `No ${itemName} in inventory` };
    }
    
    const dropCount = count === null ? inventoryItem.count : Math.min(count, inventoryItem.count);
    
    await bot.toss(item.id, null, dropCount);
    
    return {
      status: 'success',
      action: 'drop',
      message: `Dropped ${dropCount}x ${itemName}`,
      item: itemName,
      count: dropCount
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'drop',
      message: `Failed to drop: ${err.message}`
    };
  }
}

/**
 * Eat food from inventory
 */
async function executeEat(bot, foodName = null) {
  console.log(`[Utility] Eating ${foodName || 'any food'}`);
  
  try {
    const mcData = currentMcData(bot);
    if (!mcData) {
      return { status: 'error', message: 'Minecraft data not available' };
    }
    
    // If no specific food, find any edible item
    let foodItem = null;
    
    if (foodName) {
      const item = mcData.itemsByName[foodName];
      if (!item) {
        return { status: 'error', message: `Unknown food: ${foodName}` };
      }
      foodItem = bot.inventory.items().find(i => i.type === item.id);
    } else {
      // Find any food in inventory
      const foods = ['cooked_beef', 'cooked_porkchop', 'bread', 'apple', 'cooked_chicken'];
      for (const food of foods) {
        const item = mcData.itemsByName[food];
        if (item) {
          foodItem = bot.inventory.items().find(i => i.type === item.id);
          if (foodItem) break;
        }
      }
    }
    
    if (!foodItem) {
      return { status: 'error', message: 'No food in inventory' };
    }
    
    await bot.equip(foodItem, 'hand');
    await bot.consume();
    
    return {
      status: 'success',
      action: 'eat',
      message: `Ate ${foodItem.name}`,
      food: foodItem.name
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'eat',
      message: `Failed to eat: ${err.message}`
    };
  }
}

/**
 * Sleep in a bed
 */
async function executeSleep(bot) {
  console.log(`[Utility] Sleeping in bed`);
  
  try {
    const bed = bot.findBlock({
      matching: bot.registry.blocksByName.bed.id,
      maxDistance: 32
    });
    
    if (!bed) {
      return {
        status: 'error',
        action: 'sleep',
        message: `No bed found nearby`
      };
    }
    
    await bot.sleep(bed);
    
    return {
      status: 'success',
      action: 'sleep',
      message: `Slept in bed`
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'sleep',
      message: `Failed to sleep: ${err.message}`
    };
  }
}

// CRITICAL: Export all functions!
module.exports = {
  executeStatus,
  executeEquip,
  executeCraft,
  executeUse,
  executeLook,
  executeDrop,
  executeEat,
  executeSleep
};
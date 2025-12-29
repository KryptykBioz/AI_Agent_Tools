/**
 * actions/utility.js - Enhanced utility actions with full crafting support
 */

const { currentMcData } = require('../bot');

/**
 * Craft an item using recipe system
 */
async function executeCraft(bot, itemName, count = 1) {
  console.log(`[Utility] Crafting ${count}x ${itemName}`);
  
  try {
    const mcData = currentMcData(bot);
    if (!mcData) {
      return { status: 'error', message: 'Minecraft data not available' };
    }
    
    const item = mcData.itemsByName[itemName];
    if (!item) {
      return { status: 'error', message: `Unknown item: ${itemName}` };
    }
    
    // Find recipe
    const recipe = bot.recipesFor(item.id, null, 1, null)[0];
    
    if (!recipe) {
      return {
        status: 'error',
        action: 'craft',
        message: `No recipe found for ${itemName}`
      };
    }
    
    // Check if we need crafting table
    const needsCraftingTable = recipe.requiresTable;
    
    if (needsCraftingTable) {
      const craftingTable = bot.findBlock({
        matching: mcData.blocksByName['crafting_table'].id,
        maxDistance: 32
      });
      
      if (!craftingTable) {
        return {
          status: 'error',
          action: 'craft',
          message: `${itemName} requires crafting table (not found nearby)`
        };
      }
      
      // Craft at table
      await bot.craft(recipe, count, craftingTable);
    } else {
      // Craft in inventory
      await bot.craft(recipe, count, null);
    }
    
    return {
      status: 'success',
      action: 'craft',
      message: `Crafted ${count}x ${itemName}`,
      item: itemName,
      count,
      usedTable: needsCraftingTable
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'craft',
      message: `Failed to craft: ${err.message}`
    };
  }
}

/**
 * Place crafting table
 */
async function executePlaceCraftingTable(bot) {
  console.log(`[Utility] Placing crafting table`);
  
  try {
    const mcData = currentMcData(bot);
    if (!mcData) {
      return { status: 'error', message: 'Minecraft data not available' };
    }
    
    const craftingTable = mcData.itemsByName['crafting_table'];
    if (!craftingTable) {
      return { status: 'error', message: 'Crafting table not in game data' };
    }
    
    const tableItem = bot.inventory.items().find(i => i.type === craftingTable.id);
    
    if (!tableItem) {
      return { status: 'error', message: 'No crafting table in inventory' };
    }
    
    // Find a place to put it
    const pos = bot.entity.position.floored().offset(1, 0, 0);
    const referenceBlock = bot.blockAt(pos.offset(0, -1, 0));
    
    if (!referenceBlock || referenceBlock.name === 'air') {
      return { status: 'error', message: 'No solid block to place on' };
    }
    
    await bot.equip(tableItem, 'hand');
    await bot.placeBlock(referenceBlock, bot.vec3(0, 1, 0));
    
    return {
      status: 'success',
      action: 'place_crafting_table',
      message: 'Placed crafting table',
      position: { x: pos.x, y: pos.y, z: pos.z }
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'place_crafting_table',
      message: `Failed: ${err.message}`
    };
  }
}

/**
 * Equip item with proper slot detection
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
    else if (itemName.includes('shield')) destination = 'off-hand';
    
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
 * Unequip item from slot
 */
async function executeUnequip(bot, slot = 'hand') {
  console.log(`[Utility] Unequipping ${slot}`);
  
  try {
    await bot.unequip(slot);
    
    return {
      status: 'success',
      action: 'unequip',
      message: `Unequipped ${slot}`,
      slot
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'unequip',
      message: `Failed to unequip: ${err.message}`
    };
  }
}

/**
 * Drop item from inventory
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
 * Eat food to restore health/hunger
 */
async function executeEat(bot, foodName = null) {
  console.log(`[Utility] Eating ${foodName || 'any food'}`);
  
  try {
    const mcData = currentMcData(bot);
    if (!mcData) {
      return { status: 'error', message: 'Minecraft data not available' };
    }
    
    let foodItem = null;
    
    if (foodName) {
      const item = mcData.itemsByName[foodName];
      if (!item) {
        return { status: 'error', message: `Unknown food: ${foodName}` };
      }
      foodItem = bot.inventory.items().find(i => i.type === item.id);
    } else {
      // Find any food
      const foods = [
        'cooked_beef', 'cooked_porkchop', 'cooked_chicken', 'cooked_mutton',
        'bread', 'apple', 'golden_apple', 'carrot', 'baked_potato',
        'cooked_salmon', 'cooked_cod', 'cookie'
      ];
      
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
 * Sleep in nearest bed
 */
async function executeSleep(bot) {
  console.log(`[Utility] Sleeping`);
  
  try {
    const mcData = currentMcData(bot);
    if (!mcData) {
      return { status: 'error', message: 'Minecraft data not available' };
    }
    
    const bedTypes = ['red_bed', 'white_bed', 'black_bed', 'blue_bed', 'brown_bed',
                      'cyan_bed', 'gray_bed', 'green_bed', 'light_blue_bed', 'light_gray_bed',
                      'lime_bed', 'magenta_bed', 'orange_bed', 'pink_bed', 'purple_bed', 'yellow_bed'];
    
    let bed = null;
    
    for (const bedType of bedTypes) {
      const bedBlock = mcData.blocksByName[bedType];
      if (bedBlock) {
        bed = bot.findBlock({
          matching: bedBlock.id,
          maxDistance: 32
        });
        if (bed) break;
      }
    }
    
    if (!bed) {
      return { status: 'error', message: 'No bed found nearby' };
    }
    
    try {
      await bot.sleep(bed);
      
      return {
        status: 'success',
        action: 'sleep',
        message: 'Sleeping in bed'
      };
    } catch (err) {
      if (err.message.includes('cannot sleep')) {
        return {
          status: 'error',
          action: 'sleep',
          message: 'Cannot sleep (must be night or thundering)'
        };
      }
      throw err;
    }
    
  } catch (err) {
    return {
      status: 'error',
      action: 'sleep',
      message: `Failed to sleep: ${err.message}`
    };
  }
}

/**
 * Wake up from bed
 */
async function executeWake(bot) {
  console.log(`[Utility] Waking up`);
  
  try {
    await bot.wake();
    
    return {
      status: 'success',
      action: 'wake',
      message: 'Woke up from bed'
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'wake',
      message: `Failed to wake: ${err.message}`
    };
  }
}

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
      gameMode: bot.game?.gameMode || 'unknown',
      dimension: bot.game?.dimension || 'unknown',
      experience: bot.experience || 0,
      level: bot.experienceLevel || 0
    }
  };
}

/**
 * Look at target
 */
async function executeLook(bot, targetName) {
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
    
    // Try to find player
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

module.exports = {
  executeStatus,
  executeEquip,
  executeUnequip,
  executeCraft,
  executePlaceCraftingTable,
  executeDrop,
  executeEat,
  executeSleep,
  executeWake,
  executeLook
};
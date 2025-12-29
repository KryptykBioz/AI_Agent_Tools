/**
 * actions/interaction.js - Container and world object interactions
 */

const { currentMcData } = require('../bot');
const { Vec3 } = require('vec3');

/**
 * Open and view chest contents
 */
async function executeOpenChest(bot, x, y, z) {
  console.log(`[Interaction] Opening chest at (${x}, ${y}, ${z})`);
  
  try {
    let chest;
    
    if (x !== undefined && y !== undefined && z !== undefined) {
      // Open chest at specific coordinates
      const pos = new Vec3(Math.floor(x), Math.floor(y), Math.floor(z));
      chest = bot.blockAt(pos);
    } else {
      // Find nearest chest
      const mcData = currentMcData(bot);
      if (!mcData) {
        return { status: 'error', message: 'Minecraft data not available' };
      }
      
      const chestBlock = mcData.blocksByName['chest'];
      if (!chestBlock) {
        return { status: 'error', message: 'Chest not found in game data' };
      }
      
      chest = bot.findBlock({
        matching: chestBlock.id,
        maxDistance: 32
      });
    }
    
    if (!chest || (chest.name !== 'chest' && chest.name !== 'trapped_chest')) {
      return {
        status: 'error',
        action: 'open_chest',
        message: 'No chest at that location'
      };
    }
    
    const chestWindow = await bot.openChest(chest);
    
    const items = chestWindow.containerItems();
    const itemList = items.map(item => ({
      name: item.name,
      count: item.count,
      slot: item.slot
    }));
    
    // Keep chest open for a moment, then close
    await new Promise(resolve => setTimeout(resolve, 500));
    chestWindow.close();
    
    return {
      status: 'success',
      action: 'open_chest',
      message: `Chest contains ${items.length} item stacks`,
      position: { x: chest.position.x, y: chest.position.y, z: chest.position.z },
      items: itemList,
      totalStacks: items.length
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'open_chest',
      message: `Failed to open chest: ${err.message}`
    };
  }
}

/**
 * Take items from chest
 */
async function executeTakeFromChest(bot, itemName, count = null, x, y, z) {
  console.log(`[Interaction] Taking ${count || 'all'} ${itemName} from chest`);
  
  try {
    let chest;
    
    if (x !== undefined && y !== undefined && z !== undefined) {
      const pos = new Vec3(Math.floor(x), Math.floor(y), Math.floor(z));
      chest = bot.blockAt(pos);
    } else {
      const mcData = currentMcData(bot);
      if (!mcData) {
        return { status: 'error', message: 'Minecraft data not available' };
      }
      
      const chestBlock = mcData.blocksByName['chest'];
      chest = bot.findBlock({
        matching: chestBlock.id,
        maxDistance: 32
      });
    }
    
    if (!chest || chest.name !== 'chest') {
      return { status: 'error', message: 'No chest found' };
    }
    
    const chestWindow = await bot.openChest(chest);
    
    const mcData = currentMcData(bot);
    const item = mcData.itemsByName[itemName];
    
    if (!item) {
      chestWindow.close();
      return { status: 'error', message: `Unknown item: ${itemName}` };
    }
    
    const chestItem = chestWindow.containerItems().find(i => i.type === item.id);
    
    if (!chestItem) {
      chestWindow.close();
      return { status: 'error', message: `No ${itemName} in chest` };
    }
    
    const takeCount = count === null ? chestItem.count : Math.min(count, chestItem.count);
    
    await chestWindow.withdraw(item.id, null, takeCount);
    await new Promise(resolve => setTimeout(resolve, 500));
    chestWindow.close();
    
    return {
      status: 'success',
      action: 'take_from_chest',
      message: `Took ${takeCount}x ${itemName} from chest`,
      item: itemName,
      count: takeCount
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'take_from_chest',
      message: `Failed: ${err.message}`
    };
  }
}

/**
 * Put items into chest
 */
async function executePutInChest(bot, itemName, count = null, x, y, z) {
  console.log(`[Interaction] Putting ${count || 'all'} ${itemName} in chest`);
  
  try {
    let chest;
    
    if (x !== undefined && y !== undefined && z !== undefined) {
      const pos = new Vec3(Math.floor(x), Math.floor(y), Math.floor(z));
      chest = bot.blockAt(pos);
    } else {
      const mcData = currentMcData(bot);
      if (!mcData) {
        return { status: 'error', message: 'Minecraft data not available' };
      }
      
      const chestBlock = mcData.blocksByName['chest'];
      chest = bot.findBlock({
        matching: chestBlock.id,
        maxDistance: 32
      });
    }
    
    if (!chest || chest.name !== 'chest') {
      return { status: 'error', message: 'No chest found' };
    }
    
    const mcData = currentMcData(bot);
    const item = mcData.itemsByName[itemName];
    
    if (!item) {
      return { status: 'error', message: `Unknown item: ${itemName}` };
    }
    
    const inventoryItem = bot.inventory.items().find(i => i.type === item.id);
    
    if (!inventoryItem) {
      return { status: 'error', message: `No ${itemName} in inventory` };
    }
    
    const chestWindow = await bot.openChest(chest);
    
    const depositCount = count === null ? inventoryItem.count : Math.min(count, inventoryItem.count);
    
    await chestWindow.deposit(item.id, null, depositCount);
    await new Promise(resolve => setTimeout(resolve, 500));
    chestWindow.close();
    
    return {
      status: 'success',
      action: 'put_in_chest',
      message: `Put ${depositCount}x ${itemName} in chest`,
      item: itemName,
      count: depositCount
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'put_in_chest',
      message: `Failed: ${err.message}`
    };
  }
}

/**
 * Use/activate a block (door, lever, button, etc.)
 */
async function executeActivateBlock(bot, blockName, x, y, z) {
  console.log(`[Interaction] Activating ${blockName || 'block'}`);
  
  try {
    let targetBlock;
    
    if (x !== undefined && y !== undefined && z !== undefined) {
      const pos = new Vec3(Math.floor(x), Math.floor(y), Math.floor(z));
      targetBlock = bot.blockAt(pos);
    } else {
      // Find nearest block of that type
      const mcData = currentMcData(bot);
      if (!mcData) {
        return { status: 'error', message: 'Minecraft data not available' };
      }
      
      const block = mcData.blocksByName[blockName];
      if (!block) {
        return { status: 'error', message: `Unknown block: ${blockName}` };
      }
      
      targetBlock = bot.findBlock({
        matching: block.id,
        maxDistance: 32
      });
    }
    
    if (!targetBlock) {
      return {
        status: 'error',
        action: 'activate',
        message: `No ${blockName || 'block'} found`
      };
    }
    
    await bot.activateBlock(targetBlock);
    
    return {
      status: 'success',
      action: 'activate',
      message: `Activated ${targetBlock.name}`,
      block: targetBlock.name,
      position: {
        x: targetBlock.position.x,
        y: targetBlock.position.y,
        z: targetBlock.position.z
      }
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'activate',
      message: `Failed to activate: ${err.message}`
    };
  }
}

/**
 * Open door
 */
async function executeOpenDoor(bot, x, y, z) {
  return executeActivateBlock(bot, 'door', x, y, z);
}

/**
 * Press button
 */
async function executePressButton(bot, x, y, z) {
  return executeActivateBlock(bot, 'button', x, y, z);
}

/**
 * Flip lever
 */
async function executeFlipLever(bot, x, y, z) {
  return executeActivateBlock(bot, 'lever', x, y, z);
}

/**
 * Open furnace and check contents
 */
async function executeOpenFurnace(bot, x, y, z) {
  console.log(`[Interaction] Opening furnace`);
  
  try {
    let furnace;
    
    if (x !== undefined && y !== undefined && z !== undefined) {
      const pos = new Vec3(Math.floor(x), Math.floor(y), Math.floor(z));
      furnace = bot.blockAt(pos);
    } else {
      const mcData = currentMcData(bot);
      if (!mcData) {
        return { status: 'error', message: 'Minecraft data not available' };
      }
      
      const furnaceBlock = mcData.blocksByName['furnace'];
      furnace = bot.findBlock({
        matching: furnaceBlock.id,
        maxDistance: 32
      });
    }
    
    if (!furnace || furnace.name !== 'furnace') {
      return { status: 'error', message: 'No furnace found' };
    }
    
    const furnaceWindow = await bot.openFurnace(furnace);
    
    const inputItem = furnaceWindow.inputItem();
    const fuelItem = furnaceWindow.fuelItem();
    const outputItem = furnaceWindow.outputItem();
    
    await new Promise(resolve => setTimeout(resolve, 500));
    furnaceWindow.close();
    
    return {
      status: 'success',
      action: 'open_furnace',
      message: 'Furnace opened',
      input: inputItem ? { name: inputItem.name, count: inputItem.count } : null,
      fuel: fuelItem ? { name: fuelItem.name, count: fuelItem.count } : null,
      output: outputItem ? { name: outputItem.name, count: outputItem.count } : null
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'open_furnace',
      message: `Failed: ${err.message}`
    };
  }
}

/**
 * Smelt items in furnace
 */
async function executeSmelt(bot, itemName, fuelName, count = 1) {
  console.log(`[Interaction] Smelting ${count}x ${itemName} with ${fuelName}`);
  
  try {
    const mcData = currentMcData(bot);
    if (!mcData) {
      return { status: 'error', message: 'Minecraft data not available' };
    }
    
    // Find furnace
    const furnaceBlock = mcData.blocksByName['furnace'];
    const furnace = bot.findBlock({
      matching: furnaceBlock.id,
      maxDistance: 32
    });
    
    if (!furnace) {
      return { status: 'error', message: 'No furnace found' };
    }
    
    // Get items
    const item = mcData.itemsByName[itemName];
    const fuel = mcData.itemsByName[fuelName];
    
    if (!item || !fuel) {
      return { status: 'error', message: 'Invalid item or fuel' };
    }
    
    const inventoryItem = bot.inventory.items().find(i => i.type === item.id);
    const inventoryFuel = bot.inventory.items().find(i => i.type === fuel.id);
    
    if (!inventoryItem) {
      return { status: 'error', message: `No ${itemName} in inventory` };
    }
    
    if (!inventoryFuel) {
      return { status: 'error', message: `No ${fuelName} in inventory` };
    }
    
    const furnaceWindow = await bot.openFurnace(furnace);
    
    // Put items in furnace
    await furnaceWindow.putInput(item.id, null, Math.min(count, inventoryItem.count));
    await furnaceWindow.putFuel(fuel.id, null, 1);
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    furnaceWindow.close();
    
    return {
      status: 'success',
      action: 'smelt',
      message: `Started smelting ${count}x ${itemName}`,
      item: itemName,
      fuel: fuelName,
      count
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'smelt',
      message: `Failed: ${err.message}`
    };
  }
}

module.exports = {
  executeOpenChest,
  executeTakeFromChest,
  executePutInChest,
  executeActivateBlock,
  executeOpenDoor,
  executePressButton,
  executeFlipLever,
  executeOpenFurnace,
  executeSmelt
};
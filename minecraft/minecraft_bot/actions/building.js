/**
 * actions/building.js - Building and construction actions
 */

const { currentMcData } = require('../bot');

/**
 * Build a structure
 */
async function executeBuild(bot, structureName) {
  console.log(`[Building] Building ${structureName}`);
  
  const structures = {
    'wall': buildWall,
    'tower': buildTower,
    'platform': buildPlatform,
    'pillar': buildPillar
  };
  
  const buildFunc = structures[structureName.toLowerCase()];
  
  if (!buildFunc) {
    return {
      status: 'error',
      action: 'build',
      message: `Unknown structure: "${structureName}". Available: ${Object.keys(structures).join(', ')}`
    };
  }
  
  try {
    return await buildFunc(bot);
  } catch (err) {
    return {
      status: 'error',
      action: 'build',
      message: `Failed to build ${structureName}: ${err.message}`
    };
  }
}

/**
 * Place a single block
 */
async function executePlaceBlock(bot, blockName, x, y, z) {
  console.log(`[Building] Placing ${blockName} at (${x}, ${y}, ${z})`);
  
  try {
    const mcData = currentMcData(bot);
    if (!mcData) {
      return { status: 'error', message: 'Minecraft data not available' };
    }
    
    const item = mcData.itemsByName[blockName];
    if (!item) {
      return { status: 'error', message: `Unknown block: ${blockName}` };
    }
    
    const inventoryItem = bot.inventory.items().find(i => i.type === item.id);
    if (!inventoryItem) {
      return { status: 'error', message: `No ${blockName} in inventory` };
    }
    
    const targetPos = bot.vec3(x, y, z);
    const referenceBlock = bot.blockAt(targetPos.offset(0, -1, 0));
    
    if (!referenceBlock || referenceBlock.name === 'air') {
      return { status: 'error', message: 'No solid block to place against' };
    }
    
    await bot.equip(inventoryItem, 'hand');
    await bot.placeBlock(referenceBlock, bot.vec3(0, 1, 0));
    
    return {
      status: 'success',
      action: 'place',
      message: `Placed ${blockName}`,
      block: blockName,
      position: targetPos
    };
    
  } catch (err) {
    return { status: 'error', message: `Failed to place: ${err.message}` };
  }
}

/**
 * Break a block
 */
async function executeBreakBlock(bot, x, y, z) {
  console.log(`[Building] Breaking block at (${x}, ${y}, ${z})`);
  
  try {
    const block = bot.blockAt(bot.vec3(x, y, z));
    if (!block || block.name === 'air') {
      return { status: 'error', message: 'No block at that position' };
    }
    
    await bot.dig(block);
    
    return {
      status: 'success',
      action: 'break',
      message: `Broke ${block.name}`,
      block: block.name
    };
    
  } catch (err) {
    return { status: 'error', message: `Failed to break: ${err.message}` };
  }
}

// Structure builders
async function buildWall(bot) {
  return { status: 'error', message: 'Wall building not yet implemented' };
}

async function buildTower(bot) {
  return { status: 'error', message: 'Tower building not yet implemented' };
}

async function buildPlatform(bot) {
  return { status: 'error', message: 'Platform building not yet implemented' };
}

async function buildPillar(bot) {
  return { status: 'error', message: 'Pillar building not yet implemented' };
}

module.exports = {
  executeBuild,
  executePlaceBlock,
  executeBreakBlock
};
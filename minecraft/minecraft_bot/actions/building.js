/**
 * actions/building.js - Complete building and construction system
 */

const { currentMcData } = require('../bot');
const { Vec3 } = require('vec3');

/**
 * Build a structure
 */
async function executeBuild(bot, structureName, size = 5) {
  console.log(`[Building] Building ${structureName} (size: ${size})`);
  
  const structures = {
    'wall': buildWall,
    'tower': buildTower,
    'platform': buildPlatform,
    'pillar': buildPillar,
    'bridge': buildBridge,
    'stairs': buildStairs,
    'house': buildHouse,
    'shelter': buildShelter
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
    return await buildFunc(bot, size);
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
    
    const block = mcData.blocksByName[blockName];
    if (!block) {
      return { status: 'error', message: `Unknown block: ${blockName}` };
    }
    
    const item = mcData.itemsByName[blockName];
    if (!item) {
      return { status: 'error', message: `Block "${blockName}" cannot be placed as item` };
    }
    
    const inventoryItem = bot.inventory.items().find(i => i.type === item.id);
    if (!inventoryItem) {
      return { status: 'error', message: `No ${blockName} in inventory` };
    }
    
    const targetPos = new Vec3(Math.floor(x), Math.floor(y), Math.floor(z));
    const referenceBlock = bot.blockAt(targetPos.offset(0, -1, 0));
    
    if (!referenceBlock || referenceBlock.name === 'air') {
      return { status: 'error', message: 'No solid block to place against' };
    }
    
    await bot.equip(inventoryItem, 'hand');
    await bot.placeBlock(referenceBlock, new Vec3(0, 1, 0));
    
    return {
      status: 'success',
      action: 'place',
      message: `Placed ${blockName} at (${x}, ${y}, ${z})`,
      block: blockName,
      position: { x, y, z }
    };
    
  } catch (err) {
    return { 
      status: 'error', 
      message: `Failed to place: ${err.message}` 
    };
  }
}

/**
 * Break a block at coordinates
 */
async function executeBreakBlock(bot, x, y, z) {
  console.log(`[Building] Breaking block at (${x}, ${y}, ${z})`);
  
  try {
    const pos = new Vec3(Math.floor(x), Math.floor(y), Math.floor(z));
    const block = bot.blockAt(pos);
    
    if (!block || block.name === 'air') {
      return { status: 'error', message: 'No block at that position' };
    }
    
    // Equip appropriate tool
    const { equipBestTool } = require('./gathering');
    await equipBestTool(bot, block);
    
    await bot.dig(block);
    
    return {
      status: 'success',
      action: 'break',
      message: `Broke ${block.name}`,
      block: block.name,
      position: { x, y, z }
    };
    
  } catch (err) {
    return { 
      status: 'error', 
      message: `Failed to break: ${err.message}` 
    };
  }
}

/**
 * Fill an area with blocks
 */
async function executeFill(bot, x1, y1, z1, x2, y2, z2, blockName) {
  console.log(`[Building] Filling area from (${x1},${y1},${z1}) to (${x2},${y2},${z2}) with ${blockName}`);
  
  try {
    const mcData = currentMcData(bot);
    if (!mcData) {
      return { status: 'error', message: 'Minecraft data not available' };
    }
    
    const block = mcData.blocksByName[blockName];
    if (!block) {
      return { status: 'error', message: `Unknown block: ${blockName}` };
    }
    
    const item = mcData.itemsByName[blockName];
    if (!item) {
      return { status: 'error', message: `Block "${blockName}" cannot be placed as item` };
    }
    
    let placed = 0;
    const minX = Math.min(x1, x2);
    const maxX = Math.max(x1, x2);
    const minY = Math.min(y1, y2);
    const maxY = Math.max(y1, y2);
    const minZ = Math.min(z1, z2);
    const maxZ = Math.max(z1, z2);
    
    const totalBlocks = (maxX - minX + 1) * (maxY - minY + 1) * (maxZ - minZ + 1);
    
    if (totalBlocks > 1000) {
      return { 
        status: 'error', 
        message: `Area too large (${totalBlocks} blocks). Maximum: 1000` 
      };
    }
    
    for (let x = minX; x <= maxX; x++) {
      for (let y = minY; y <= maxY; y++) {
        for (let z = minZ; z <= maxZ; z++) {
          try {
            const result = await executePlaceBlock(bot, blockName, x, y, z);
            if (result.status === 'success') {
              placed++;
            }
            await new Promise(resolve => setTimeout(resolve, 50));
          } catch (err) {
            console.warn(`[Fill] Failed to place at (${x},${y},${z}): ${err.message}`);
          }
        }
      }
    }
    
    return {
      status: 'success',
      action: 'fill',
      message: `Filled area with ${placed}/${totalBlocks} ${blockName} blocks`,
      placed,
      total: totalBlocks
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'fill',
      message: `Failed: ${err.message}`
    };
  }
}

// Structure builders
async function buildWall(bot, length) {
  const startPos = bot.entity.position.floored();
  let placed = 0;
  
  const mcData = currentMcData(bot);
  const cobblestone = mcData?.blocksByName['cobblestone'];
  
  if (!cobblestone) {
    return { status: 'error', message: 'Cobblestone not available' };
  }
  
  // Build wall in front of bot
  for (let i = 0; i < length; i++) {
    for (let h = 0; h < 3; h++) {
      const pos = startPos.offset(i, h, 0);
      try {
        const result = await executePlaceBlock(bot, 'cobblestone', pos.x, pos.y, pos.z);
        if (result.status === 'success') placed++;
        await new Promise(resolve => setTimeout(resolve, 100));
      } catch (err) {
        console.warn(`[Wall] Failed at (${pos.x},${pos.y},${pos.z})`);
      }
    }
  }
  
  return {
    status: 'success',
    action: 'build',
    structure: 'wall',
    message: `Built wall with ${placed} blocks`,
    placed
  };
}

async function buildTower(bot, height) {
  const startPos = bot.entity.position.floored();
  let placed = 0;
  
  for (let y = 0; y < height; y++) {
    const pos = startPos.offset(1, y, 0);
    try {
      const result = await executePlaceBlock(bot, 'cobblestone', pos.x, pos.y, pos.z);
      if (result.status === 'success') placed++;
      await new Promise(resolve => setTimeout(resolve, 150));
    } catch (err) {
      console.warn(`[Tower] Failed at height ${y}`);
    }
  }
  
  return {
    status: 'success',
    action: 'build',
    structure: 'tower',
    message: `Built tower ${height} blocks tall (${placed} placed)`,
    placed,
    height
  };
}

async function buildPlatform(bot, size) {
  const startPos = bot.entity.position.floored().offset(1, 0, 1);
  let placed = 0;
  
  for (let x = 0; x < size; x++) {
    for (let z = 0; z < size; z++) {
      const pos = startPos.offset(x, 0, z);
      try {
        const result = await executePlaceBlock(bot, 'oak_planks', pos.x, pos.y, pos.z);
        if (result.status === 'success') placed++;
        await new Promise(resolve => setTimeout(resolve, 100));
      } catch (err) {
        console.warn(`[Platform] Failed at (${pos.x},${pos.z})`);
      }
    }
  }
  
  return {
    status: 'success',
    action: 'build',
    structure: 'platform',
    message: `Built ${size}x${size} platform (${placed} blocks)`,
    placed,
    size
  };
}

async function buildPillar(bot, height) {
  return buildTower(bot, height);
}

async function buildBridge(bot, length) {
  const startPos = bot.entity.position.floored();
  let placed = 0;
  
  for (let i = 0; i < length; i++) {
    const pos = startPos.offset(i, -1, 0);
    try {
      const result = await executePlaceBlock(bot, 'oak_planks', pos.x, pos.y, pos.z);
      if (result.status === 'success') placed++;
      await new Promise(resolve => setTimeout(resolve, 100));
    } catch (err) {
      console.warn(`[Bridge] Failed at position ${i}`);
    }
  }
  
  return {
    status: 'success',
    action: 'build',
    structure: 'bridge',
    message: `Built bridge ${length} blocks long (${placed} placed)`,
    placed,
    length
  };
}

async function buildStairs(bot, height) {
  const startPos = bot.entity.position.floored();
  let placed = 0;
  
  for (let i = 0; i < height; i++) {
    const pos = startPos.offset(i, i, 0);
    try {
      const result = await executePlaceBlock(bot, 'cobblestone', pos.x, pos.y, pos.z);
      if (result.status === 'success') placed++;
      await new Promise(resolve => setTimeout(resolve, 150));
    } catch (err) {
      console.warn(`[Stairs] Failed at step ${i}`);
    }
  }
  
  return {
    status: 'success',
    action: 'build',
    structure: 'stairs',
    message: `Built stairs ${height} blocks high (${placed} placed)`,
    placed,
    height
  };
}

async function buildHouse(bot, size) {
  return {
    status: 'error',
    message: 'House building not yet implemented - use simpler structures like walls and platforms'
  };
}

async function buildShelter(bot, size) {
  const startPos = bot.entity.position.floored();
  let placed = 0;
  
  // Build simple 3x3 shelter
  const shelterSize = Math.min(size, 5);
  
  // Floor
  for (let x = 0; x < shelterSize; x++) {
    for (let z = 0; z < shelterSize; z++) {
      const pos = startPos.offset(x, -1, z);
      try {
        const result = await executePlaceBlock(bot, 'cobblestone', pos.x, pos.y, pos.z);
        if (result.status === 'success') placed++;
      } catch (err) {}
    }
  }
  
  // Walls (2 blocks high)
  for (let h = 0; h < 2; h++) {
    for (let x = 0; x < shelterSize; x++) {
      const pos1 = startPos.offset(x, h, 0);
      const pos2 = startPos.offset(x, h, shelterSize - 1);
      try {
        await executePlaceBlock(bot, 'cobblestone', pos1.x, pos1.y, pos1.z);
        await executePlaceBlock(bot, 'cobblestone', pos2.x, pos2.y, pos2.z);
        placed += 2;
      } catch (err) {}
    }
    
    for (let z = 1; z < shelterSize - 1; z++) {
      const pos1 = startPos.offset(0, h, z);
      const pos2 = startPos.offset(shelterSize - 1, h, z);
      try {
        await executePlaceBlock(bot, 'cobblestone', pos1.x, pos1.y, pos1.z);
        await executePlaceBlock(bot, 'cobblestone', pos2.x, pos2.y, pos2.z);
        placed += 2;
      } catch (err) {}
    }
  }
  
  return {
    status: 'success',
    action: 'build',
    structure: 'shelter',
    message: `Built ${shelterSize}x${shelterSize} shelter (${placed} blocks)`,
    placed
  };
}

module.exports = {
  executeBuild,
  executePlaceBlock,
  executeBreakBlock,
  executeFill
};
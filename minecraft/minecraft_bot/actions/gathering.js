/**
 * actions/gathering.js - Resource gathering
 */

const { currentMcData } = require('../bot');

async function executeGather(bot, resourceName, targetCount = 1) {
  console.log(`[Gathering] Gathering ${targetCount}x ${resourceName}`);
  
  if (!bot?.collectBlock) {
    return {
      status: 'error',
      action: 'gather',
      message: 'collectBlock plugin not available'
    };
  }
  
  try {
    const mcData = currentMcData(bot);
    if (!mcData?.blocksByName) {
      return {
        status: 'error',
        action: 'gather',
        message: 'Minecraft data not available'
      };
    }
    
    const blockName = normalizeResourceName(resourceName);
    const block = mcData.blocksByName[blockName];
    
    if (!block) {
      return {
        status: 'error',
        action: 'gather',
        message: `Unknown resource: "${resourceName}"`
      };
    }
    
    const safeTargetCount = Math.min(targetCount, 64);
    const startCount = countItemInInventory(bot, blockName);
    let collected = 0;
    let consecutiveFailures = 0;
    const maxFailures = 3;
    
    for (let i = 0; i < safeTargetCount; i++) {
      const blockToCollect = bot.findBlock({
        matching: block.id,
        maxDistance: 64
      });
      
      if (!blockToCollect) {
        consecutiveFailures++;
        if (consecutiveFailures >= maxFailures) {
          const gained = countItemInInventory(bot, blockName) - startCount;
          return {
            status: gained > 0 ? 'partial' : 'error',
            action: 'gather',
            message: gained > 0 
              ? `Collected ${gained}/${safeTargetCount} ${blockName}`
              : `No ${blockName} found within 64 blocks`,
            collected: gained,
            target: safeTargetCount
          };
        }
        await new Promise(resolve => setTimeout(resolve, 500));
        continue;
      }
      
      consecutiveFailures = 0;
      
      try {
        await bot.collectBlock.collect(blockToCollect);
        collected++;
        console.log(`[Gathering] Collected ${collected}/${safeTargetCount}`);
        await new Promise(resolve => setTimeout(resolve, 100));
      } catch (err) {
        if (err.message.includes('interrupted') || err.message.includes('cancel')) {
          const gained = countItemInInventory(bot, blockName) - startCount;
          return {
            status: 'cancelled',
            action: 'gather',
            message: `Cancelled after collecting ${gained}`,
            collected: gained
          };
        }
        consecutiveFailures++;
        if (consecutiveFailures >= maxFailures) break;
      }
    }
    
    const actualGained = countItemInInventory(bot, blockName) - startCount;
    
    return {
      status: 'success',
      action: 'gather',
      message: `Collected ${actualGained}x ${blockName}`,
      resource: blockName,
      collected: actualGained
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'gather',
      message: `Failed: ${err.message}`
    };
  }
}

async function executeChopTree(bot, treeType = 'oak') {
  const logType = `${treeType}_log`;
  return executeGather(bot, logType, 16);
}

async function executeMineOre(bot, oreType, count = 1) {
  const oreNames = {
    'iron': 'iron_ore',
    'coal': 'coal_ore',
    'gold': 'gold_ore',
    'diamond': 'diamond_ore'
  };
  const fullOreName = oreNames[oreType.toLowerCase()] || `${oreType}_ore`;
  return executeGather(bot, fullOreName, count);
}

async function executeFarmCrop(bot, cropType) {
  return { status: 'error', message: 'Not implemented' };
}

async function executeFish(bot, duration = 30000) {
  return { status: 'error', message: 'Not implemented' };
}

function normalizeResourceName(name) {
  const aliases = {
    'wood': 'oak_log',
    'log': 'oak_log',
    'logs': 'oak_log',
    'tree': 'oak_log',
    'oak': 'oak_log',
    'cobble': 'cobblestone',
    'rock': 'stone',
    'coal': 'coal_ore',
    'iron': 'iron_ore',
    'gold': 'gold_ore',
    'diamond': 'diamond_ore'
  };
  
  const normalized = name.toLowerCase().trim();
  return aliases[normalized] || normalized;
}

function countItemInInventory(bot, itemName) {
  if (!bot?.inventory) return 0;
  
  try {
    return bot.inventory.items()
      .filter(item => item?.name === itemName)
      .reduce((sum, item) => sum + (item.count || 0), 0);
  } catch (err) {
    return 0;
  }
}

module.exports = {
  executeGather,
  executeChopTree,
  executeMineOre,
  executeFarmCrop,
  executeFish
};
/**
 * actions/combat.js - Combat and defense actions
 */

const { goals, Movements } = require('mineflayer-pathfinder');
const { currentMcData } = require('../bot');

/**
 * Attack a specific entity
 */
async function executeAttack(bot, targetName) {
  console.log(`[Combat] Attacking ${targetName}`);
  
  try {
    let target = null;
    
    // Find the target entity
    if (targetName === 'nearest' || targetName === 'closest') {
      target = findNearestHostile(bot);
      if (!target) {
        return {
          status: 'error',
          action: 'attack',
          message: 'No hostile mobs nearby'
        };
      }
    } else {
      // Find by mob type or player name
      target = findEntityByName(bot, targetName);
      if (!target) {
        return {
          status: 'error',
          action: 'attack',
          message: `Cannot find ${targetName} to attack`
        };
      }
    }
    
    // Check if we have a weapon
    const weapon = bot.heldItem;
    const weaponName = weapon ? weapon.name : 'fist';
    
    console.log(`[Combat] Engaging ${target.name || target.username || 'target'} with ${weaponName}`);
    
    // Use pvp plugin if available
    if (bot.pvp) {
      bot.pvp.attack(target);
      
      return {
        status: 'success',
        action: 'attack',
        message: `Attacking ${target.name || target.username || 'target'} with ${weaponName}`,
        target: target.name || target.username,
        weapon: weaponName
      };
    } else {
      // Manual attack
      await bot.attack(target);
      
      return {
        status: 'success',
        action: 'attack',
        message: `Attacked ${target.name || target.username || 'target'}`,
        target: target.name || target.username
      };
    }
    
  } catch (err) {
    return {
      status: 'error',
      action: 'attack',
      message: `Failed to attack: ${err.message}`
    };
  }
}

/**
 * Enter defend/guard mode
 */
async function executeDefend(bot) {
  console.log('[Combat] Entering defend mode');
  
  try {
    // Set up auto-defense against hostile mobs
    if (!bot.defendMode) {
      bot.defendMode = true;
      
      // Listen for nearby hostile mobs
      const checkInterval = setInterval(() => {
        if (!bot.defendMode) {
          clearInterval(checkInterval);
          return;
        }
        
        const hostile = findNearestHostile(bot);
        if (hostile && bot.pvp) {
          const distance = bot.entity.position.distanceTo(hostile.position);
          if (distance < 16) {
            console.log(`[Combat] Auto-defending against ${hostile.name}`);
            bot.pvp.attack(hostile);
          }
        }
      }, 1000);
      
      // Store interval for cleanup
      bot.defendInterval = checkInterval;
    }
    
    return {
      status: 'success',
      action: 'defend',
      message: 'Defend mode activated - will attack nearby hostiles',
      mode: 'active'
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'defend',
      message: `Failed to enter defend mode: ${err.message}`
    };
  }
}

/**
 * Stop defending
 */
async function executeStopDefend(bot) {
  console.log('[Combat] Stopping defend mode');
  
  try {
    bot.defendMode = false;
    
    if (bot.defendInterval) {
      clearInterval(bot.defendInterval);
      bot.defendInterval = null;
    }
    
    if (bot.pvp) {
      bot.pvp.stop();
    }
    
    return {
      status: 'success',
      action: 'stop_defend',
      message: 'Defend mode deactivated',
      mode: 'inactive'
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'stop_defend',
      message: `Failed to stop defend mode: ${err.message}`
    };
  }
}

/**
 * Flee from danger
 */
async function executeFlee(bot, distance = 20) {
  console.log(`[Combat] Fleeing ${distance} blocks`);
  
  try {
    const hostile = findNearestHostile(bot);
    if (!hostile) {
      return {
        status: 'success',
        action: 'flee',
        message: 'No threats nearby, no need to flee'
      };
    }
    
    // Calculate escape direction (opposite of threat)
    const botPos = bot.entity.position;
    const threatPos = hostile.position;
    
    const dx = botPos.x - threatPos.x;
    const dz = botPos.z - threatPos.z;
    const length = Math.sqrt(dx * dx + dz * dz);
    
    const escapeX = botPos.x + (dx / length) * distance;
    const escapeZ = botPos.z + (dz / length) * distance;
    const escapeY = botPos.y;
    
    // Use pathfinder to escape
    if (bot.pathfinder) {
      const mcData = currentMcData(bot);
      if (mcData) {
        const movements = new Movements(bot, mcData);
        movements.canDig = false;
        movements.allowSprinting = true;
        bot.pathfinder.setMovements(movements);
        
        const goal = new goals.GoalBlock(
          Math.floor(escapeX),
          Math.floor(escapeY),
          Math.floor(escapeZ)
        );
        bot.pathfinder.setGoal(goal);
      }
    }
    
    return {
      status: 'success',
      action: 'flee',
      message: `Fleeing from ${hostile.name || 'threat'}`,
      threat: hostile.name
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'flee',
      message: `Failed to flee: ${err.message}`
    };
  }
}

/**
 * Equip best weapon/armor from inventory
 */
async function executeEquipBest(bot, type = 'weapon') {
  console.log(`[Combat] Equipping best ${type}`);
  
  try {
    const mcData = currentMcData(bot);
    if (!mcData) {
      return { status: 'error', message: 'Minecraft data not available' };
    }
    
    if (type === 'weapon') {
      // Find best weapon
      const weapons = ['diamond_sword', 'iron_sword', 'stone_sword', 'wooden_sword'];
      
      for (const weaponName of weapons) {
        const item = mcData.itemsByName[weaponName];
        if (item) {
          const inventoryItem = bot.inventory.items().find(i => i.type === item.id);
          if (inventoryItem) {
            await bot.equip(inventoryItem, 'hand');
            return {
              status: 'success',
              action: 'equip_best',
              message: `Equipped ${weaponName}`,
              item: weaponName
            };
          }
        }
      }
      
      return { status: 'error', message: 'No weapons in inventory' };
    }
    
    return { status: 'error', message: `Unknown equipment type: ${type}` };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'equip_best',
      message: `Failed to equip: ${err.message}`
    };
  }
}

// Helper functions

function findNearestHostile(bot) {
  const hostileMobs = [
    'zombie', 'skeleton', 'creeper', 'spider', 'enderman', 'witch',
    'zombie_villager', 'husk', 'stray', 'cave_spider', 'silverfish',
    'blaze', 'ghast', 'magma_cube', 'slime', 'phantom', 'drowned'
  ];
  
  let nearest = null;
  let nearestDist = Infinity;
  
  for (const entity of Object.values(bot.entities)) {
    if (!entity || entity === bot.entity) continue;
    
    const entityName = (entity.name || '').toLowerCase();
    const isHostile = hostileMobs.some(mob => entityName.includes(mob));
    
    if (isHostile) {
      const dist = bot.entity.position.distanceTo(entity.position);
      if (dist < nearestDist) {
        nearestDist = dist;
        nearest = entity;
      }
    }
  }
  
  return nearest;
}

function findEntityByName(bot, name) {
  const lowerName = name.toLowerCase();
  
  for (const entity of Object.values(bot.entities)) {
    if (!entity || entity === bot.entity) continue;
    
    const entityName = (entity.name || entity.displayName || '').toLowerCase();
    const username = (entity.username || '').toLowerCase();
    
    if (entityName.includes(lowerName) || username.includes(lowerName)) {
      return entity;
    }
  }
  
  return null;
}

module.exports = {
  executeAttack,
  executeDefend,
  executeStopDefend,
  executeFlee,
  executeEquipBest
};
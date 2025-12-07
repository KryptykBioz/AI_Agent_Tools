/**
 * actions/movement.js - Movement and pathfinding actions
 */

const { goals, Movements } = require('mineflayer-pathfinder');
const { getNearestPlayer } = require('../world-info');
const { currentMcData } = require('../bot');

async function executeStop(bot) {
  console.log('[Movement] Stopping all activities');
  
  try {
    if (bot.pathfinder) {
      bot.pathfinder.setGoal(null);
    }
    
    if (bot.collectBlock && bot.collectBlock.cancelTask) {
      bot.collectBlock.cancelTask();
    }
    
    if (bot.pvp) {
      bot.pvp.stop();
    }
    
    return {
      status: 'success',
      action: 'stop',
      message: 'Stopped all activities'
    };
  } catch (err) {
    return {
      status: 'error',
      action: 'stop',
      message: `Failed to stop: ${err.message}`
    };
  }
}

async function executeFollow(bot, targetName) {
  console.log(`[Movement] Following ${targetName}`);
  
  if (!bot.pathfinder) {
    return {
      status: 'error',
      action: 'follow',
      message: 'Pathfinder not available'
    };
  }
  
  try {
    let target;
    const playerNames = Object.keys(bot.players);
    console.log(`[Movement] Available players: ${playerNames.join(', ') || 'none'}`);
    
    if (targetName === 'player' || targetName === 'nearest') {
      target = getNearestPlayer(bot);
      if (!target) {
        return {
          status: 'error',
          action: 'follow',
          message: `No players nearby. Available: ${playerNames.join(', ') || 'none'}`
        };
      }
      console.log(`[Movement] Found nearest player: ${target.username || 'unknown'}`);
    } else {
      target = bot.players[targetName]?.entity;
      if (!target) {
        return {
          status: 'error',
          action: 'follow',
          message: `Player "${targetName}" not found. Available: ${playerNames.join(', ') || 'none'}`
        };
      }
      console.log(`[Movement] Found player: ${targetName}`);
    }
    
    const mcData = currentMcData(bot);
    if (!mcData) {
      return {
        status: 'error',
        action: 'follow',
        message: 'Minecraft data not available'
      };
    }
    
    const movements = new Movements(bot, mcData);
    movements.canDig = true;
    movements.allow1by1towers = false;
    bot.pathfinder.setMovements(movements);
    
    const goal = new goals.GoalFollow(target, 2);
    bot.pathfinder.setGoal(goal, true);
    
    const targetDisplayName = target.username || target.displayName || targetName;
    
    return {
      status: 'success',
      action: 'follow',
      message: `Following ${targetDisplayName}`,
      target: targetDisplayName
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'follow',
      message: `Failed to follow: ${err.message}`
    };
  }
}

async function executeGoto(bot, x, y, z) {
  console.log(`[Movement] Going to (${x}, ${y}, ${z})`);
  
  if (!bot.pathfinder) {
    return {
      status: 'error',
      action: 'goto',
      message: 'Pathfinder not available'
    };
  }
  
  try {
    const mcData = currentMcData(bot);
    if (!mcData) {
      return {
        status: 'error',
        action: 'goto',
        message: 'Minecraft data not available'
      };
    }
    
    const movements = new Movements(bot, mcData);
    movements.canDig = true;
    bot.pathfinder.setMovements(movements);
    
    const goal = new goals.GoalBlock(Math.floor(x), Math.floor(y), Math.floor(z));
    bot.pathfinder.setGoal(goal);
    
    const botPos = bot.entity.position;
    const distance = Math.sqrt(
      Math.pow(x - botPos.x, 2) +
      Math.pow(y - botPos.y, 2) +
      Math.pow(z - botPos.z, 2)
    );
    
    return {
      status: 'success',
      action: 'goto',
      message: `Moving to (${x}, ${y}, ${z}) - ${Math.round(distance)} blocks away`,
      coordinates: { x, y, z },
      distance: Math.round(distance * 10) / 10
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'goto',
      message: `Failed to goto: ${err.message}`
    };
  }
}

async function executeCome(bot) {
  console.log(`[Movement] Coming to nearest player`);
  
  const target = getNearestPlayer(bot);
  if (!target) {
    return {
      status: 'error',
      action: 'come',
      message: 'No players nearby'
    };
  }
  
  const pos = target.position;
  return executeGoto(bot, pos.x, pos.y, pos.z);
}

module.exports = {
  executeStop,
  executeFollow,
  executeGoto,
  executeCome
};
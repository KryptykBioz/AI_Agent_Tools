/**
 * actions/player-interaction.js - Player interaction actions
 */

const { getNearestPlayer } = require('../world-info');
const { currentMcData } = require('../bot');

/**
 * Give an item to a player
 */
async function executeGive(bot, itemName, targetName) {
  console.log(`[Interaction] Giving ${itemName} to ${targetName}`);
  
  try {
    // Normalize target
    if (targetName === 'you' || targetName === 'me' || targetName === 'player') {
      const nearestPlayer = getNearestPlayer(bot);
      if (!nearestPlayer) {
        return { status: 'error', message: 'No players nearby' };
      }
      targetName = nearestPlayer.username;
    }
    
    // Find the player
    const targetPlayer = bot.players[targetName];
    if (!targetPlayer || !targetPlayer.entity) {
      return {
        status: 'error',
        message: `Player "${targetName}" not found or not nearby`
      };
    }
    
    // Find item in inventory
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
    
    // Toss the item toward the player
    await bot.toss(inventoryItem.type, null, inventoryItem.count);
    
    return {
      status: 'success',
      action: 'give',
      message: `Gave ${inventoryItem.count}x ${itemName} to ${targetName}`,
      item: itemName,
      count: inventoryItem.count,
      target: targetName
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'give',
      message: `Failed to give item: ${err.message}`
    };
  }
}

/**
 * Trade with a player or villager
 */
async function executeTrade(bot, targetName) {
  console.log(`[Interaction] Trading with ${targetName}`);
  
  return {
    status: 'error',
    action: 'trade',
    message: 'Trading system not yet implemented'
  };
}

/**
 * Send a chat message
 */
async function executeChat(bot, message) {
  console.log(`[Interaction] Saying: ${message}`);
  
  try {
    bot.chat(message);
    
    return {
      status: 'success',
      action: 'chat',
      message: `Said: "${message}"`
    };
  } catch (err) {
    return {
      status: 'error',
      action: 'chat',
      message: `Failed to send chat: ${err.message}`
    };
  }
}

/**
 * Whisper to a specific player
 */
async function executeWhisper(bot, targetName, message) {
  console.log(`[Interaction] Whispering to ${targetName}: ${message}`);
  
  try {
    bot.chat(`/msg ${targetName} ${message}`);
    
    return {
      status: 'success',
      action: 'whisper',
      message: `Whispered to ${targetName}: "${message}"`,
      target: targetName
    };
  } catch (err) {
    return {
      status: 'error',
      action: 'whisper',
      message: `Failed to whisper: ${err.message}`
    };
  }
}

/**
 * Wave or greet a player
 */
async function executeGreet(bot, targetName = null) {
  console.log(`[Interaction] Greeting ${targetName || 'everyone'}`);
  
  try {
    let message;
    
    if (targetName && targetName !== 'everyone') {
      message = `Hello ${targetName}!`;
    } else {
      message = 'Hello everyone!';
    }
    
    bot.chat(message);
    
    return {
      status: 'success',
      action: 'greet',
      message: `Greeted ${targetName || 'everyone'}`
    };
  } catch (err) {
    return {
      status: 'error',
      action: 'greet',
      message: `Failed to greet: ${err.message}`
    };
  }
}

/**
 * Point at something (look at it)
 */
async function executePoint(bot, targetName) {
  console.log(`[Interaction] Pointing at ${targetName}`);
  
  try {
    // Find target entity
    let target = null;
    
    if (targetName === 'player' || targetName === 'you') {
      const nearestPlayer = getNearestPlayer(bot);
      if (nearestPlayer) {
        target = nearestPlayer;
      }
    } else {
      const player = bot.players[targetName];
      if (player && player.entity) {
        target = player.entity;
      }
    }
    
    if (!target) {
      return {
        status: 'error',
        action: 'point',
        message: `Cannot find ${targetName} to point at`
      };
    }
    
    // Look at the target
    await bot.lookAt(target.position.offset(0, target.height, 0));
    
    return {
      status: 'success',
      action: 'point',
      message: `Pointed at ${target.username || targetName}`,
      target: target.username || targetName
    };
    
  } catch (err) {
    return {
      status: 'error',
      action: 'point',
      message: `Failed to point: ${err.message}`
    };
  }
}

module.exports = {
  executeGive,
  executeTrade,
  executeChat,
  executeWhisper,
  executeGreet,
  executePoint
};
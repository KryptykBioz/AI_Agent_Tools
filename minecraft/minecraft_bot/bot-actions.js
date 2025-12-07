/**
 * bot-actions.js - Hardcoded command execution
 * NO LLM - Agent decides everything, bot just executes
 */

const movementActions = require('./actions/movement');
const gatheringActions = require('./actions/gathering');
const buildingActions = require('./actions/building');
const playerInteractionActions = require('./actions/player-interaction');
const combatActions = require('./actions/combat');
const utilityActions = require('./actions/utility');

/**
 * Main action handler - Direct command routing
 * Expects structured input: { action: "gather", args: ["wood", 1] }
 */
async function handleAction(req, res, bot) {
  const { action, args = [] } = req.body;
  
  if (!action || typeof action !== 'string') {
    return res.status(400).json({
      status: 'error',
      error: 'Missing or invalid "action" field. Expected: {"action": "gather", "args": ["wood"]}'
    });
  }
  
  if (!bot?.entity) {
    return res.status(503).json({
      status: 'error',
      error: 'Bot not connected or not spawned'
    });
  }
  
  console.log(`[Action] Executing: ${action}`, args);
  
  try {
    let result;
    
    // Direct action routing - no parsing needed
    switch (action) {
      // =====================================================================
      // MOVEMENT ACTIONS
      // =====================================================================
      case 'stop':
        result = await movementActions.executeStop(bot);
        break;
      
      case 'follow':
        const followTarget = args[0] || 'player';
        result = await movementActions.executeFollow(bot, followTarget);
        break;
      
      case 'goto':
        if (args.length < 3) {
          return res.status(400).json({
            status: 'error',
            error: 'goto requires [x, y, z] coordinates',
            received: args
          });
        }
        const [x, y, z] = args;
        result = await movementActions.executeGoto(bot, x, y, z);
        break;
      
      case 'come':
        result = await movementActions.executeCome(bot);
        break;
      
      case 'move':
        const direction = args[0] || 'forward';
        const distance = args[1] || 5;
        result = await movementActions.executeMove(bot, direction, distance);
        break;
      
      // =====================================================================
      // GATHERING ACTIONS
      // =====================================================================
      case 'gather':
      case 'gather_resource':
        if (args.length < 1) {
          return res.status(400).json({
            status: 'error',
            error: 'gather requires resource name',
            received: args
          });
        }
        const resource = args[0];
        const count = args[1] || 1;
        console.log(`[Gather] Resource: ${resource}, Count: ${count}`);
        result = await gatheringActions.executeGather(bot, resource, count);
        break;
      
      // =====================================================================
      // BUILDING ACTIONS
      // =====================================================================
      case 'build':
        const structure = args[0] || 'wall';
        result = await buildingActions.executeBuild(bot, structure);
        break;
      
      // =====================================================================
      // PLAYER INTERACTION ACTIONS
      // =====================================================================
      case 'give':
        if (args.length < 2) {
          return res.status(400).json({
            status: 'error',
            error: 'give requires [item, target]',
            received: args
          });
        }
        const [giveItem, giveTarget] = args;
        result = await playerInteractionActions.executeGive(bot, giveItem, giveTarget);
        break;
      
      case 'trade':
        const tradeTarget = args[0] || 'nearest';
        result = await playerInteractionActions.executeTrade(bot, tradeTarget);
        break;
      
      case 'chat':
      case 'say':
        const message = args[0] || '';
        if (!message) {
          return res.status(400).json({
            status: 'error',
            error: 'chat requires message text'
          });
        }
        result = await playerInteractionActions.executeChat(bot, message);
        break;
      
      // =====================================================================
      // COMBAT ACTIONS
      // =====================================================================
      case 'attack':
      case 'attack_entity':
        const attackTarget = args[0] || 'nearest_hostile';
        result = await combatActions.executeAttack(bot, attackTarget);
        break;
      
      case 'defend':
        result = await combatActions.executeDefend(bot);
        break;
      
      case 'flee':
        result = await combatActions.executeFlee(bot);
        break;
      
      // =====================================================================
      // UTILITY ACTIONS
      // =====================================================================
      case 'equip':
        const equipItem = args[0] || '';
        if (!equipItem) {
          return res.status(400).json({
            status: 'error',
            error: 'equip requires item name'
          });
        }
        result = await utilityActions.executeEquip(bot, equipItem);
        break;
      
      case 'craft':
      case 'craft_item':
        const craftItem = args[0] || '';
        if (!craftItem) {
          return res.status(400).json({
            status: 'error',
            error: 'craft requires item name'
          });
        }
        result = await utilityActions.executeCraft(bot, craftItem);
        break;
      
      case 'use':
      case 'use_item':
        const useTarget = args[0] || '';
        if (!useTarget) {
          return res.status(400).json({
            status: 'error',
            error: 'use requires item name'
          });
        }
        result = await utilityActions.executeUse(bot, useTarget);
        break;
      
      case 'look':
        const lookTarget = args[0] || 'forward';
        result = await utilityActions.executeLook(bot, lookTarget);
        break;
      
      case 'status':
        result = await utilityActions.executeStatus(bot);
        break;
      
      // =====================================================================
      // UNKNOWN ACTION
      // =====================================================================
      default:
        console.warn(`[Action] Unknown action: ${action}`);
        return res.status(400).json({
          status: 'error',
          error: `Unknown action: ${action}`,
          available_actions: [
            'stop', 'follow', 'goto', 'come', 'move',
            'gather', 'build',
            'give', 'trade', 'chat',
            'attack', 'defend', 'flee',
            'equip', 'craft', 'use', 'look', 'status'
          ]
        });
    }
    
    // Return result
    return res.json(result);
    
  } catch (err) {
    console.error(`[Action] Execute error (${action}):`, err);
    return res.status(500).json({
      status: 'error',
      action: action,
      error: err.message,
      stack: process.env.NODE_ENV === 'development' ? err.stack : undefined
    });
  }
}

module.exports = {
  handleAction
};
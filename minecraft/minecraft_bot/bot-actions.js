/**
 * bot-actions.js - Complete action routing system
 * Routes structured commands to appropriate action modules
 */

const movementActions = require('./actions/movement');
const gatheringActions = require('./actions/gathering');
const buildingActions = require('./actions/building');
const playerInteractionActions = require('./actions/player-interaction');
const combatActions = require('./actions/combat');
const utilityActions = require('./actions/utility');
const interactionActions = require('./actions/interaction');

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
    
    // =================================================================
    // MOVEMENT ACTIONS
    // =================================================================
    switch (action) {
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
      
      // =================================================================
      // GATHERING ACTIONS
      // =================================================================
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
        result = await gatheringActions.executeGather(bot, resource, count);
        break;
      
      case 'chop_tree':
      case 'chop':
        const treeType = args[0] || 'oak';
        const logCount = args[1] || 16;
        result = await gatheringActions.executeChopTree(bot, treeType, logCount);
        break;
      
      case 'mine_ore':
      case 'mine':
        const oreType = args[0] || 'iron';
        const oreCount = args[1] || 1;
        result = await gatheringActions.executeMineOre(bot, oreType, oreCount);
        break;
      
      case 'farm_crop':
      case 'farm':
        const cropType = args[0] || 'wheat';
        const cropCount = args[1] || 8;
        result = await gatheringActions.executeFarmCrop(bot, cropType, cropCount);
        break;
      
      case 'fish':
        const duration = args[0] || 30000;
        result = await gatheringActions.executeFish(bot, duration);
        break;
      
      // =================================================================
      // BUILDING ACTIONS
      // =================================================================
      case 'build':
        const structure = args[0] || 'wall';
        const size = args[1] || 5;
        result = await buildingActions.executeBuild(bot, structure, size);
        break;
      
      case 'place_block':
      case 'place':
        if (args.length < 4) {
          return res.status(400).json({
            status: 'error',
            error: 'place_block requires [blockName, x, y, z]',
            received: args
          });
        }
        const [blockName, bx, by, bz] = args;
        result = await buildingActions.executePlaceBlock(bot, blockName, bx, by, bz);
        break;
      
      case 'break_block':
      case 'break':
        if (args.length < 3) {
          return res.status(400).json({
            status: 'error',
            error: 'break_block requires [x, y, z]',
            received: args
          });
        }
        const [breakX, breakY, breakZ] = args;
        result = await buildingActions.executeBreakBlock(bot, breakX, breakY, breakZ);
        break;
      
      case 'fill':
        if (args.length < 7) {
          return res.status(400).json({
            status: 'error',
            error: 'fill requires [x1, y1, z1, x2, y2, z2, blockName]',
            received: args
          });
        }
        const [fx1, fy1, fz1, fx2, fy2, fz2, fillBlock] = args;
        result = await buildingActions.executeFill(bot, fx1, fy1, fz1, fx2, fy2, fz2, fillBlock);
        break;
      
      // =================================================================
      // CONTAINER INTERACTIONS
      // =================================================================
      case 'open_chest':
        const [chestX, chestY, chestZ] = args;
        result = await interactionActions.executeOpenChest(bot, chestX, chestY, chestZ);
        break;
      
      case 'take_from_chest':
        const [takeItem, takeCount, takeX, takeY, takeZ] = args;
        result = await interactionActions.executeTakeFromChest(bot, takeItem, takeCount, takeX, takeY, takeZ);
        break;
      
      case 'put_in_chest':
        const [putItem, putCount, putX, putY, putZ] = args;
        result = await interactionActions.executePutInChest(bot, putItem, putCount, putX, putY, putZ);
        break;
      
      case 'open_furnace':
        const [furnaceX, furnaceY, furnaceZ] = args;
        result = await interactionActions.executeOpenFurnace(bot, furnaceX, furnaceY, furnaceZ);
        break;
      
      case 'smelt':
        if (args.length < 2) {
          return res.status(400).json({
            status: 'error',
            error: 'smelt requires [itemName, fuelName, optional count]',
            received: args
          });
        }
        const [smeltItem, smeltFuel, smeltCount] = args;
        result = await interactionActions.executeSmelt(bot, smeltItem, smeltFuel, smeltCount || 1);
        break;
      
      case 'activate':
      case 'activate_block':
        const [activateBlock, activateX, activateY, activateZ] = args;
        result = await interactionActions.executeActivateBlock(bot, activateBlock, activateX, activateY, activateZ);
        break;
      
      case 'open_door':
        const [doorX, doorY, doorZ] = args;
        result = await interactionActions.executeOpenDoor(bot, doorX, doorY, doorZ);
        break;
      
      case 'press_button':
        const [buttonX, buttonY, buttonZ] = args;
        result = await interactionActions.executePressButton(bot, buttonX, buttonY, buttonZ);
        break;
      
      case 'flip_lever':
        const [leverX, leverY, leverZ] = args;
        result = await interactionActions.executeFlipLever(bot, leverX, leverY, leverZ);
        break;
      
      // =================================================================
      // PLAYER INTERACTION ACTIONS
      // =================================================================
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
      
      // =================================================================
      // COMBAT ACTIONS
      // =================================================================
      case 'attack':
      case 'attack_entity':
        const attackTarget = args[0] || 'nearest_hostile';
        result = await combatActions.executeAttack(bot, attackTarget);
        break;
      
      case 'defend':
        result = await combatActions.executeDefend(bot);
        break;
      
      case 'stop_defend':
        result = await combatActions.executeStopDefend(bot);
        break;
      
      case 'flee':
        const fleeDistance = args[0] || 20;
        result = await combatActions.executeFlee(bot, fleeDistance);
        break;
      
      case 'equip_best':
        const equipType = args[0] || 'weapon';
        result = await combatActions.executeEquipBest(bot, equipType);
        break;
      
      // =================================================================
      // UTILITY ACTIONS
      // =================================================================
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
      
      case 'unequip':
        const unequipSlot = args[0] || 'hand';
        result = await utilityActions.executeUnequip(bot, unequipSlot);
        break;
      
      case 'craft':
      case 'craft_item':
        const craftItem = args[0] || '';
        const craftCount = args[1] || 1;
        if (!craftItem) {
          return res.status(400).json({
            status: 'error',
            error: 'craft requires item name'
          });
        }
        result = await utilityActions.executeCraft(bot, craftItem, craftCount);
        break;
      
      case 'place_crafting_table':
        result = await utilityActions.executePlaceCraftingTable(bot);
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
      
      case 'drop':
        const dropItem = args[0] || '';
        const dropCount = args[1] || null;
        if (!dropItem) {
          return res.status(400).json({
            status: 'error',
            error: 'drop requires item name'
          });
        }
        result = await utilityActions.executeDrop(bot, dropItem, dropCount);
        break;
      
      case 'eat':
        const foodName = args[0] || null;
        result = await utilityActions.executeEat(bot, foodName);
        break;
      
      case 'sleep':
        result = await utilityActions.executeSleep(bot);
        break;
      
      case 'wake':
        result = await utilityActions.executeWake(bot);
        break;
      
      case 'look':
        const lookTarget = args[0] || 'forward';
        result = await utilityActions.executeLook(bot, lookTarget);
        break;
      
      case 'status':
        result = await utilityActions.executeStatus(bot);
        break;
      
      // =================================================================
      // UNKNOWN ACTION
      // =================================================================
      default:
        console.warn(`[Action] Unknown action: ${action}`);
        return res.status(400).json({
          status: 'error',
          error: `Unknown action: ${action}`,
          available_actions: [
            // Movement
            'stop', 'follow', 'goto', 'come', 'move',
            // Gathering
            'gather', 'chop_tree', 'mine_ore', 'farm_crop', 'fish',
            // Building
            'build', 'place_block', 'break_block', 'fill',
            // Containers
            'open_chest', 'take_from_chest', 'put_in_chest', 'open_furnace', 'smelt',
            'activate_block', 'open_door', 'press_button', 'flip_lever',
            // Player interaction
            'give', 'trade', 'chat',
            // Combat
            'attack', 'defend', 'stop_defend', 'flee', 'equip_best',
            // Utility
            'equip', 'unequip', 'craft', 'place_crafting_table', 'drop', 
            'eat', 'sleep', 'wake', 'look', 'status'
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
      stack: process.env.NODE_ENV === 'development' ? err.stack : undefined,
    });
  }
}

module.exports = {
  handleAction
};
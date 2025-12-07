// world-info.js - Enhanced with full coordinate information

const { Vec3 } = require('vec3');

function getVisionData(bot) {
  if (!bot || !bot.entity) {
    throw new Error("Bot not available or not spawned");
  }

  try {
    const vision = {
      position: {
        x: Math.round(bot.entity.position.x * 100) / 100,
        y: Math.round(bot.entity.position.y * 100) / 100,
        z: Math.round(bot.entity.position.z * 100) / 100
      },
      rotation: {
        yaw: Math.round((bot.entity.yaw * 180 / Math.PI) * 100) / 100,
        pitch: Math.round((bot.entity.pitch * 180 / Math.PI) * 100) / 100
      },
      health: bot.health || 0,
      food: bot.food || 0,
      experience: bot.experience || 0,
      time: getTimeInfo(bot),
      weather: getWeatherInfo(bot),
      biome: getBiomeInfo(bot),
      targetBlock: getTargetBlock(bot),
      inventory: getEnhancedInventoryInfo(bot),
      capabilities: getMovementCapabilities(bot),
      blocksInSight: getEnhancedBlocksInSight(bot),
      entitiesInSight: getEnhancedEntitiesInSight(bot),
      surroundings: getSurroundings(bot),
      scanError: null
    };

    return vision;
  } catch (err) {
    console.error("[Vision] Fatal error in getVisionData:", err);
    return getMinimalSafeVision();
  }
}

function getMinimalSafeVision() {
  return {
    position: { x: 0, y: 0, z: 0 },
    rotation: { yaw: 0, pitch: 0 },
    health: 0,
    food: 0,
    experience: 0,
    time: { phase: "unknown", day: 0, timeOfDay: 0 },
    weather: { isRaining: false, isThundering: false, thunderState: 0 },
    biome: "unknown",
    targetBlock: null,
    inventory: {
      itemInHand: null,
      totalItems: 0,
      slots: [],
      categories: {
        tools: [], weapons: [], armor: [], food: [],
        blocks: [], ores: [], resources: [], other: []
      }
    },
    capabilities: {
      onGround: true, inWater: false, canFly: false,
      canSprint: false, isJumping: false
    },
    blocksInSight: [],
    entitiesInSight: [],
    surroundings: {
      ground: 'unknown', ceiling: 'unknown',
      walls: { north: 'unknown', south: 'unknown', east: 'unknown', west: 'unknown' }
    },
    scanError: "Vision system error"
  };
}

function getTimeInfo(bot) {
  try {
    if (bot.time && typeof bot.time === 'object') {
      const timeOfDay = bot.time.timeOfDay || 0;
      const day = Math.floor((bot.time.age || 0) / 24000);
      
      let phase = "unknown";
      if (timeOfDay >= 0 && timeOfDay < 6000) phase = "morning";
      else if (timeOfDay >= 6000 && timeOfDay < 12000) phase = "day";
      else if (timeOfDay >= 12000 && timeOfDay < 18000) phase = "evening";
      else if (timeOfDay >= 18000 && timeOfDay < 24000) phase = "night";
      
      return { timeOfDay, day, phase };
    }
    return { phase: "unknown", day: 0, timeOfDay: 0 };
  } catch (err) {
    console.warn("[Vision] Time info error:", err.message);
    return { phase: "unknown", day: 0, timeOfDay: 0 };
  }
}

function getWeatherInfo(bot) {
  try {
    return {
      isRaining: bot.isRaining || false,
      isThundering: (bot.thunderState || 0) > 0,
      thunderState: bot.thunderState || 0
    };
  } catch (err) {
    console.warn("[Vision] Weather info error:", err.message);
    return { isRaining: false, isThundering: false, thunderState: 0 };
  }
}

function getBiomeInfo(bot) {
  try {
    const block = bot.blockAt(bot.entity.position);
    return block && block.biome ? block.biome.name : "unknown";
  } catch (err) {
    console.warn("[Vision] Biome info error:", err.message);
    return "unknown";
  }
}

function getTargetBlock(bot) {
  try {
    const block = bot.blockAtCursor(5);
    if (block && block.name !== 'air') {
      return {
        name: block.name,
        position: {
          x: block.position.x,
          y: block.position.y,
          z: block.position.z
        },
        material: block.material || null,
        hardness: block.hardness || null
      };
    }
    return null;
  } catch (err) {
    return null;
  }
}

function getEnhancedInventoryInfo(bot) {
  try {
    const items = bot.inventory.items();
    const itemInHand = bot.heldItem;
    
    let handInfo = null;
    if (itemInHand) {
      handInfo = {
        name: itemInHand.name,
        displayName: itemInHand.displayName,
        count: itemInHand.count,
        durability: itemInHand.durabilityUsed || 0,
        maxDurability: itemInHand.maxDurability || null
      };
    }
    
    const categories = {
      tools: [],
      weapons: [],
      armor: [],
      food: [],
      blocks: [],
      ores: [],
      resources: [],
      other: []
    };
    
    items.forEach(item => {
      const name = item.name || '';
      const itemData = {
        name: name,
        count: item.count,
        slot: item.slot
      };
      
      if (name.includes('_pickaxe') || name.includes('_axe') || 
          name.includes('_shovel') || name.includes('_hoe')) {
        categories.tools.push(itemData);
      } else if (name.includes('_sword') || name === 'bow' || name === 'crossbow') {
        categories.weapons.push(itemData);
      } else if (name.includes('_helmet') || name.includes('_chestplate') || 
                 name.includes('_leggings') || name.includes('_boots')) {
        categories.armor.push(itemData);
      } else if (name.includes('bread') || name.includes('meat') || 
                 name.includes('fish') || name.includes('apple') ||
                 name.includes('carrot') || name.includes('potato') ||
                 name.includes('beetroot') || name.includes('stew')) {
        categories.food.push(itemData);
      } else if (name.includes('_ore')) {
        categories.ores.push(itemData);
      } else if (name.includes('_log') || name.includes('_planks') || 
                 name === 'cobblestone' || name === 'stone' || 
                 name === 'dirt' || name === 'sand' || name === 'gravel') {
        categories.blocks.push(itemData);
      } else if (name.includes('ingot') || name.includes('stick') || 
                 name.includes('coal') || name.includes('string') ||
                 name.includes('leather')) {
        categories.resources.push(itemData);
      } else {
        categories.other.push(itemData);
      }
    });
    
    return {
      itemInHand: handInfo,
      totalItems: items.length,
      slots: items.map(item => ({
        name: item.name,
        count: item.count,
        slot: item.slot
      })),
      categories: categories
    };
  } catch (err) {
    console.warn("[Vision] Inventory error:", err.message);
    return {
      itemInHand: null,
      totalItems: 0,
      slots: [],
      categories: {
        tools: [], weapons: [], armor: [], food: [],
        blocks: [], ores: [], resources: [], other: []
      }
    };
  }
}

function getMovementCapabilities(bot) {
  try {
    return {
      onGround: bot.entity.onGround || false,
      inWater: bot.entity.inWater || false,
      canFly: false,
      canSprint: (bot.food || 0) > 6,
      isJumping: bot.entity.velocity?.y > 0 || false
    };
  } catch (err) {
    console.warn("[Movement] Capabilities error:", err.message);
    return {
      onGround: true,
      inWater: false,
      canFly: false,
      canSprint: false,
      isJumping: false
    };
  }
}

function getEnhancedBlocksInSight(bot) {
  try {
    const botPos = bot.entity.position;
    const blocks = [];
    
    console.log(`[Vision] Bot position: (${botPos.x.toFixed(1)}, ${botPos.y.toFixed(1)}, ${botPos.z.toFixed(1)})`);
    
    // DIAGNOSTIC: Check block directly below
    const testBlock = bot.blockAt(new Vec3(Math.floor(botPos.x), Math.floor(botPos.y) - 1, Math.floor(botPos.z)));
    console.log(`[Vision] Block below bot:`, testBlock ? `${testBlock.name}` : 'null');
    
    // Scan in a cube around the bot
    const scanRadius = 20;
    const seen = new Set();
    
    for (let dx = -scanRadius; dx <= scanRadius; dx += 2) {
      for (let dy = -8; dy <= 8; dy += 2) {
        for (let dz = -scanRadius; dz <= scanRadius; dz += 2) {
          const x = Math.floor(botPos.x + dx);
          const y = Math.floor(botPos.y + dy);
          const z = Math.floor(botPos.z + dz);
          
          const blockKey = `${x},${y},${z}`;
          if (seen.has(blockKey)) continue;
          seen.add(blockKey);
          
          try {
            const block = bot.blockAt(new Vec3(x, y, z));
            
            // Check if block exists AND is not air
            if (block && block.name && block.name !== 'air' && block.name !== 'cave_air' && block.name !== 'void_air') {
              const distance = Math.sqrt(
                Math.pow(botPos.x - x, 2) +
                Math.pow(botPos.y - y, 2) +
                Math.pow(botPos.z - z, 2)
              );
              
              if (distance <= scanRadius) {
                blocks.push({
                  name: block.name,
                  position: { x, y, z },
                  distance: Math.round(distance * 10) / 10,
                  canBreak: canBreakBlock(bot, block),
                  type: categorizeBlock(block.name),
                  hardness: block.hardness || 0
                });
              }
            }
          } catch (e) {
            // Skip invalid positions
          }
        }
      }
    }
    
    console.log(`[Vision] Found ${blocks.length} blocks within ${scanRadius} blocks`);
    
    if (blocks.length === 0) {
      console.warn("[Vision] WARNING: No blocks found! Bot may be in void or chunks not loaded.");
      console.warn("[Vision] Bot onGround:", bot.entity.onGround);
      return [];
    }
    
    // STRATEGIC SELECTION: Provide actionable block data
    const strategicBlocks = selectStrategicBlocks(blocks, botPos);
    console.log(`[Vision] Selected ${strategicBlocks.length} strategic blocks for context`);
    
    return strategicBlocks;
    
  } catch (err) {
    console.warn("[Vision] Blocks scan error:", err.message);
    return [];
  }
}

function categorizeBlock(blockName) {
  if (!blockName) return 'other';
  
  if (blockName.includes('_ore')) return 'ore';
  if (blockName.includes('_log') || blockName === 'oak_log') return 'wood';
  if (blockName.includes('stone') || blockName === 'cobblestone' || 
      blockName === 'andesite' || blockName === 'diorite' || blockName === 'granite') return 'stone';
  if (blockName === 'dirt' || blockName === 'grass_block' || blockName === 'sand' || 
      blockName === 'gravel' || blockName === 'clay') return 'terrain';
  if (blockName.includes('_planks')) return 'crafted';
  if (blockName.includes('leaves')) return 'foliage';
  if (blockName.includes('water') || blockName.includes('lava')) return 'fluid';
  return 'other';
}

function selectStrategicBlocks(allBlocks, botPos) {
  /**
   * HUMAN-LIKE PROXIMITY-BASED SELECTION with random sampling
   * Agent gets natural situational awareness, not optimized mining routes
   */
  
  // Sort by distance for proximity-based selection
  const sorted = allBlocks.sort((a, b) => a.distance - b.distance);
  
  const selected = [];
  const seen = new Set();
  
  // PROXIMITY-BASED SAMPLING: Take blocks by distance ranges with randomization
  const ranges = [
    { name: 'immediate', min: 0, max: 5, sampleRate: 0.8 },      // 80% of blocks 0-5m
    { name: 'close', min: 5, max: 10, sampleRate: 0.5 },          // 50% of blocks 5-10m
    { name: 'nearby', min: 10, max: 15, sampleRate: 0.3 },        // 30% of blocks 10-15m
    { name: 'distant', min: 15, max: 20, sampleRate: 0.15 }       // 15% of blocks 15-20m
  ];
  
  ranges.forEach(range => {
    const blocksInRange = sorted.filter(b => 
      b.distance >= range.min && b.distance < range.max
    );
    
    // Shuffle for randomness
    const shuffled = blocksInRange.sort(() => Math.random() - 0.5);
    
    // Take sample based on rate
    const sampleSize = Math.ceil(shuffled.length * range.sampleRate);
    const sampled = shuffled.slice(0, sampleSize);
    
    sampled.forEach(block => {
      const blockKey = `${block.position.x},${block.position.y},${block.position.z}`;
      if (!seen.has(blockKey)) {
        selected.push(block);
        seen.add(blockKey);
      }
    });
    
    console.log(`[Vision] ${range.name} (${range.min}-${range.max}m): sampled ${sampled.length}/${blocksInRange.length} blocks`);
  });
  
  // Shuffle final selection for natural distribution
  const shuffledFinal = selected.sort(() => Math.random() - 0.5);
  
  console.log(`[Vision] Total blocks selected: ${shuffledFinal.length} (proximity-based random sampling)`);
  
  // Return with full position data and direction
  return shuffledFinal.map(block => ({
    name: block.name,
    type: block.type,
    position: block.position,
    distance: block.distance,
    direction: getRelativeDirection(botPos, block.position)
  }));
}

function getRelativeDirection(from, to) {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const dz = to.z - from.z;
  
  let dir = [];
  
  // Vertical
  if (dy > 1) dir.push('above');
  else if (dy < -1) dir.push('below');
  
  // Horizontal
  if (Math.abs(dx) > Math.abs(dz)) {
    dir.push(dx > 0 ? 'east' : 'west');
  } else {
    dir.push(dz > 0 ? 'south' : 'north');
  }
  
  return dir.join('-');
}

function getEnhancedEntitiesInSight(bot) {
  try {
    const botPos = bot.entity.position;
    const entities = [];
    
    Object.values(bot.entities).forEach(entity => {
      if (!entity || entity === bot.entity) return;
      
      try {
        const distance = Math.sqrt(
          Math.pow(botPos.x - entity.position.x, 2) +
          Math.pow(botPos.y - entity.position.y, 2) +
          Math.pow(botPos.z - entity.position.z, 2)
        );
        
        if (distance <= 50) {
          const entityType = entity.name || entity.displayName || 'unknown';
          const isHostile = isHostileEntity(entity);
          const isPassive = isPassiveAnimal(entity);
          
          const entityData = {
            type: entityType,
            position: entity.position,
            distance: Math.round(distance * 10) / 10,
            isPlayer: !!entity.username,
            isHostile: isHostile,
            isPassive: isPassive,
            inView: isEntityInView(bot, entity),
            health: entity.health || null,
            velocity: entity.velocity ? {
              x: Math.round(entity.velocity.x * 100) / 100,
              y: Math.round(entity.velocity.y * 100) / 100,
              z: Math.round(entity.velocity.z * 100) / 100
            } : null,
            coordinates: {
              x: Math.floor(entity.position.x),
              y: Math.floor(entity.position.y),
              z: Math.floor(entity.position.z)
            },
            direction: getRelativeDirection(botPos, entity.position)
          };
          
          if (entity.username) entityData.username = entity.username;
          if (entity.displayName) entityData.displayName = entity.displayName;
          if (isHostile) entityData.threatLevel = getThreatLevel(entity, distance);
          
          entities.push(entityData);
        }
      } catch (e) {
        // Skip problematic entities
      }
    });
    
    return entities.sort((a, b) => {
      if (a.isHostile && !b.isHostile) return -1;
      if (!a.isHostile && b.isHostile) return 1;
      return a.distance - b.distance;
    });
  } catch (err) {
    console.warn("[Vision] Entities in sight error:", err.message);
    return [];
  }
}

function getSurroundings(bot) {
  try {
    const pos = bot.entity.position;
    const x = Math.floor(pos.x);
    const y = Math.floor(pos.y);
    const z = Math.floor(pos.z);
    
    return {
      ground: getBlockName(bot, x, y - 1, z),
      ceiling: getBlockName(bot, x, y + 2, z),
      walls: {
        north: getBlockName(bot, x, y, z - 1),
        south: getBlockName(bot, x, y, z + 1),
        east: getBlockName(bot, x + 1, y, z),
        west: getBlockName(bot, x - 1, y, z)
      }
    };
  } catch (err) {
    console.warn("[Vision] Surroundings error:", err.message);
    return {
      ground: 'unknown',
      ceiling: 'unknown',
      walls: { north: 'unknown', south: 'unknown', east: 'unknown', west: 'unknown' }
    };
  }
}

function getNearestPlayer(bot) {
  try {
    if (!bot || !bot.entity) return null;
    
    const botPos = bot.entity.position;
    let nearestPlayer = null;
    let nearestDistance = Infinity;
    
    Object.values(bot.players).forEach(player => {
      if (!player.entity || player.username === bot.username) return;
      
      try {
        const playerPos = player.entity.position;
        const distance = Math.sqrt(
          Math.pow(botPos.x - playerPos.x, 2) +
          Math.pow(botPos.y - playerPos.y, 2) +
          Math.pow(botPos.z - playerPos.z, 2)
        );
        
        if (distance < nearestDistance) {
          nearestDistance = distance;
          nearestPlayer = player.entity;
        }
      } catch (e) {
        // Skip problematic players
      }
    });
    
    return nearestPlayer;
  } catch (err) {
    console.warn("[Vision] Get nearest player error:", err.message);
    return null;
  }
}

// Helper functions
function getBlockName(bot, x, y, z) {
  try {
    const block = bot.blockAt(new Vec3(x, y, z));
    return block ? block.name : 'air';
  } catch (err) {
    return 'unknown';
  }
}

function canBreakBlock(bot, block) {
  try {
    if (!block || !bot.mcData) return true;
    const unbreakableBlocks = ['bedrock', 'barrier', 'command_block', 'end_portal', 'end_portal_frame'];
    return !unbreakableBlocks.includes(block.name);
  } catch (err) {
    return true;
  }
}

function isHostileEntity(entity) {
  if (!entity) return false;
  if (entity.displayName === 'Hostile') return true;
  
  const hostileMobs = [
    'zombie', 'skeleton', 'creeper', 'spider', 'enderman', 'witch',
    'zombie_villager', 'husk', 'stray', 'cave_spider', 'silverfish',
    'blaze', 'ghast', 'magma_cube', 'slime', 'phantom', 'drowned',
    'pillager', 'vindicator', 'evoker', 'ravager', 'wither_skeleton',
    'piglin_brute', 'hoglin', 'zoglin'
  ];
  
  const entityName = (entity.name || '').toLowerCase();
  return hostileMobs.some(mob => entityName.includes(mob));
}

function isPassiveAnimal(entity) {
  if (!entity) return false;
  
  const passiveAnimals = [
    'cow', 'pig', 'sheep', 'chicken', 'rabbit', 'horse', 'donkey',
    'mule', 'cat', 'wolf', 'parrot', 'llama', 'fox', 'bee', 'panda',
    'turtle', 'cod', 'salmon', 'tropical_fish', 'pufferfish', 'squid',
    'mooshroom', 'strider', 'axolotl', 'goat', 'frog'
  ];
  
  const entityName = (entity.name || '').toLowerCase();
  return passiveAnimals.some(animal => entityName.includes(animal));
}

function getThreatLevel(entity, distance) {
  const entityName = (entity.name || '').toLowerCase();
  
  let baseThreat = 5;
  
  if (entityName.includes('creeper')) baseThreat = 9;
  else if (entityName.includes('skeleton')) baseThreat = 7;
  else if (entityName.includes('zombie')) baseThreat = 6;
  else if (entityName.includes('spider')) baseThreat = 6;
  else if (entityName.includes('enderman')) baseThreat = 8;
  else if (entityName.includes('blaze')) baseThreat = 8;
  else if (entityName.includes('ghast')) baseThreat = 7;
  
  if (distance < 5) baseThreat += 3;
  else if (distance < 10) baseThreat += 1;
  else if (distance > 20) baseThreat -= 2;
  
  return Math.max(1, Math.min(10, baseThreat));
}

function isEntityInView(bot, entity) {
  try {
    const botPos = bot.entity.position;
    const entityPos = entity.position;
    
    const dx = entityPos.x - botPos.x;
    const dy = entityPos.y - botPos.y;
    const dz = entityPos.z - botPos.z;
    const distance = Math.sqrt(dx*dx + dy*dy + dz*dz);
    
    if (distance > 20) return false;
    return distance < 10;
  } catch (err) {
    return false;
  }
}

module.exports = {
  getVisionData,
  getNearestPlayer
};
const mineflayer = require("mineflayer");
const pathfinderModule = require("mineflayer-pathfinder");
const collectBlockPlugin = require("mineflayer-collectblock").plugin;
const fs = require("fs");
const path = require("path");

// Function to find project root directory (Anna_AI/)
function findProjectRoot(startDir = __dirname) {
  let currentDir = startDir;
  const maxLevels = 10; // Prevent infinite loop
  
  for (let i = 0; i < maxLevels; i++) {
    // Check if this directory has the personality/ directory marker
    const personalityDir = path.join(currentDir, "personality");
    if (fs.existsSync(personalityDir) && fs.statSync(personalityDir).isDirectory()) {
      // Found it! This is the project root
      return currentDir;
    }
    
    // Move up one directory
    const parentDir = path.dirname(currentDir);
    if (parentDir === currentDir) {
      // Reached filesystem root
      break;
    }
    currentDir = parentDir;
  }
  
  console.warn("[WARNING]️ Could not find project root (looking for personality/ directory)");
  return null;
}

// Function to read bot name from agent_info.py
function getagentnameFromConfig() {
  // Find project root
  const projectRoot = findProjectRoot();
  
  if (!projectRoot) {
    console.warn("[WARNING]️ Could not find project root directory (Anna_AI/)");
    return null;
  }
  
  // Config path relative to project root
  const configPath = path.join(projectRoot, "personality", "agent_info.py");
  
  try {
    if (fs.existsSync(configPath)) {
      const content = fs.readFileSync(configPath, "utf8");
      const match = content.match(/agentname\s*=\s*["']([^"']+)["']/);
      if (match && match[1]) {
        console.log(`[SUCCESS] Bot name loaded from config: ${match[1]}`);
        console.log(`   Config path: ${configPath}`);
        return match[1];
      }
    } else {
      console.warn(`[WARNING]️ Config file not found at: ${configPath}`);
    }
  } catch (err) {
    console.warn("[WARNING]️ Could not read bot name from agent_info.py:", err.message);
  }
  
  return null;
}

// Function to get bot name (called when needed, not at module load time)
function getagentname() {
  const name = process.env.BOT_NAME || getagentnameFromConfig() || "MinecraftBot";
  
  // Validate bot name
  if (!name || name === "null" || name.trim() === "") {
    console.error("[FAILED] Invalid bot name! Please set agentname in agent_info.py or BOT_NAME environment variable");
    process.exit(1);
  }
  
  return name;
}

// Environment variables
const SERVER_HOST = process.env.MC_HOST || "localhost";
const SERVER_PORT = parseInt(process.env.MC_PORT || "55509", 10);
const MC_DATA_VERSION = process.env.MC_PROTOCOL || "1.16";

// Improved minecraft-data loading with better error handling
let minecraftDataFunc = null;
let minecraftDataExplicit = null;

try {
  minecraftDataFunc = require("minecraft-data");
  console.log("[SUCCESS] minecraft-data module loaded successfully");

  try {
    minecraftDataExplicit = minecraftDataFunc(MC_DATA_VERSION);
    console.log(`[SUCCESS] Pre-loaded minecraft-data for version ${MC_DATA_VERSION}`);
  } catch (err) {
    console.warn(
      `[WARNING]️ Could not pre-load minecraft-data for ${MC_DATA_VERSION}:`,
      err.message
    );
    minecraftDataExplicit = null;
  }
} catch (err) {
  console.error("[FAILED] Failed to load minecraft-data module:", err.message);
  minecraftDataFunc = null;
  minecraftDataExplicit = null;
}

// Better mcData initialization with proper attachment
function initializeMcData(bot) {
  if (!minecraftDataFunc) {
    console.warn("[WARNING]️ minecraft-data function not available");
    return null;
  }

  let data = null;

  // Try bot version first
  if (bot.version) {
    try {
      data = minecraftDataFunc(bot.version);
      console.log(`[SUCCESS] Loaded minecraft-data for bot version: ${bot.version}`);
    } catch (err) {
      console.warn(
        `[WARNING]️ Failed to load minecraft-data for bot version ${bot.version}:`,
        err.message
      );
    }
  }

  // Fall back to explicit version if bot version failed
  if (!data && minecraftDataExplicit) {
    try {
      data = minecraftDataExplicit;
      console.log(`[SUCCESS] Using pre-loaded minecraft-data version: ${MC_DATA_VERSION}`);
    } catch (err) {
      console.warn("[WARNING]️ Failed to use pre-loaded minecraft-data:", err.message);
    }
  }

  // Properly attach mcData to bot object
  if (data) {
    try {
      bot.mcData = data;
      console.log(`[SUCCESS] Attached mcData to bot object`);
      console.log(`  - Version: ${data.version || 'unknown'}`);
      console.log(
        `  - Blocks: ${data.blocks ? Object.keys(data.blocks).length : 0}`
      );
      console.log(
        `  - Items: ${data.items ? Object.keys(data.items).length : 0}`
      );
      console.log(`  - blocksByName available: ${!!data.blocksByName}`);
      console.log(`  - itemsByName available: ${!!data.itemsByName}`);
    } catch (err) {
      console.error("[FAILED] Failed to attach mcData to bot:", err.message);
    }
  }

  return data;
}

// Load plugins with proper error handling and mcData validation
function loadPlugins(bot, mcData) {
  let loadedCount = 0;

  // Validate mcData before loading plugins
  if (!mcData || !mcData.blocksByName) {
    console.error(
      "[FAILED] Cannot load plugins: mcData or blocksByName not available"
    );
    return false;
  }

  // Load pathfinder with proper validation
  try {
    if (pathfinderModule && typeof pathfinderModule.pathfinder === "function") {
      bot.loadPlugin(pathfinderModule.pathfinder);
      console.log("[SUCCESS] Pathfinder plugin loaded successfully");
      loadedCount++;
    } else if (typeof pathfinderModule === "function") {
      bot.loadPlugin(pathfinderModule);
      console.log("[SUCCESS] Pathfinder plugin (direct) loaded successfully");
      loadedCount++;
    } else if (pathfinderModule && pathfinderModule.Movements && pathfinderModule.goals) {
      // Alternative loading method for some pathfinder versions
      bot.pathfinder = pathfinderModule;
      console.log("[SUCCESS] Pathfinder plugin (manual) loaded successfully");
      loadedCount++;
    } else {
      console.warn("[WARNING]️ Pathfinder plugin not found or invalid format");
    }
  } catch (err) {
    console.error("[FAILED] Failed to load pathfinder plugin:", err.message);
  }

  // Load collectblock
  try {
    if (typeof collectBlockPlugin === "function") {
      bot.loadPlugin(collectBlockPlugin);
      console.log("[SUCCESS] Collectblock plugin loaded successfully");
      loadedCount++;
    } else {
      console.warn("[WARNING]️ Collectblock plugin not found or invalid format");
    }
  } catch (err) {
    console.error("[FAILED] Failed to load collectblock plugin:", err.message);
  }

  const success = loadedCount > 0;
  console.log(
    `${success ? "[SUCCESS]" : "[FAILED]"} Loaded ${loadedCount} plugins successfully`
  );
  return success;
}

// Create bot function
function createBot() {
  const agentname = getagentname(); // Get bot name when creating bot, not at module load
  
  const botOptions = {
    host: SERVER_HOST,
    port: SERVER_PORT,
    username: agentname,
  };
  
  // Version override options
  if (process.env.FORCE_MC_VERSION) {
    botOptions.version = process.env.FORCE_MC_VERSION;
    console.log(`🎮 Forcing Minecraft version: ${process.env.FORCE_MC_VERSION}`);
  }
  if (process.env.MC_PROTOCOL_FORCE) {
    botOptions.version = process.env.MC_PROTOCOL_FORCE;
    console.log(`🎮 Forcing protocol version: ${process.env.MC_PROTOCOL_FORCE}`);
  }

  console.log(`🎮 Creating bot with options:`, {
    host: botOptions.host,
    port: botOptions.port,
    username: botOptions.username,
    version: botOptions.version || 'auto-detect'
  });

  const bot = mineflayer.createBot(botOptions);
  
  // Initialize state properties
  bot.pluginsLoaded = false;
  bot.botReady = false;
  bot.mcData = null;
  bot.agentname = agentname; // Store bot name on the bot instance
  
  return bot;
}

// Initialize bot function
function initializeBot(bot) {
  // Bot initialization logic
  bot.once("spawn", () => {
    console.log("🚀 Bot spawned, initializing mcData and plugins...");

    // Initialize mcData with proper error handling
    const mcData = initializeMcData(bot);

    // Add a short delay to ensure bot.version is fully synced
    setTimeout(() => {
      if (mcData && mcData.blocksByName) {
        console.log("[SUCCESS] mcData initialized successfully with blocksByName");

        // Load plugins after mcData is confirmed working
        try {
          bot.pluginsLoaded = loadPlugins(bot, mcData);
          if (bot.pluginsLoaded) {
            console.log("🎉 Bot is ready with all systems operational!");
            bot.botReady = true;
          } else {
            console.warn("[WARNING]️ Bot is ready but some plugins failed to load");
            bot.botReady = true; // Still mark as ready for basic functionality
          }
        } catch (err) {
          console.error("[FAILED] Error during plugin loading:", err.message);
          bot.pluginsLoaded = false;
          bot.botReady = true; // Mark ready for basic functionality
        }
      } else {
        console.error(
          "[FAILED] Failed to initialize mcData properly - limited functionality"
        );
        console.warn("    - mcData availability:", !!mcData);
        if (mcData) {
          console.warn("    - blocksByName availability:", !!mcData.blocksByName);
          console.warn("    - itemsByName availability:", !!mcData.itemsByName);
        }
        bot.pluginsLoaded = false;
        bot.botReady = true; // Allow basic functionality
      }
    }, 1000); // 1 second delay
  });

  // Bot event handlers with better logging
  bot.on("login", () => {
    console.log(`[SUCCESS] Bot logged in as ${bot.agentname || bot.username}`);
    console.log(`🌍 Server: ${SERVER_HOST}:${SERVER_PORT}`);
    if (bot.version) {
      console.log(`🎮 Minecraft version: ${bot.version}`);
    }
  });
  
  bot.on("spawn", () => {
    console.log("🌍 Bot spawned in the world");
    if (bot.entity && bot.entity.position) {
      console.log(`📍 Position: ${bot.entity.position.x}, ${bot.entity.position.y}, ${bot.entity.position.z}`);
    }
  });
  
  bot.on("kicked", (reason) => {
    console.warn("⛔ Bot kicked:", reason);
    bot.botReady = false;
    bot.pluginsLoaded = false;
    bot.mcData = null;
  });
  
  bot.on("error", (err) => {
    console.error("🚨 Bot error:", err && err.stack ? err.stack : err);
  });
  
  bot.on("end", () => {
    console.warn("🔌 Bot disconnected. Restart the service to reconnect.");
    bot.botReady = false;
    bot.pluginsLoaded = false;
    bot.mcData = null;
  });

  // Health and status monitoring
  bot.on("health", () => {
    if (bot.health <= 5) {
      console.warn(`[WARNING]️ Low health: ${bot.health}/20`);
    }
  });

  bot.on("death", () => {
    console.warn("💀 Bot died! Respawning...");
  });
}

// Utility function to get current mcData
function currentMcData(bot) {
  if (bot && bot.mcData) return bot.mcData;
  
  if (minecraftDataFunc && bot && bot.version) {
    try {
      const data = minecraftDataFunc(bot.version);
      // Cache it on the bot for future use
      if (bot) bot.mcData = data;
      return data;
    } catch (e) {
      console.warn("[WARNING]️ Failed to get mcData from bot version:", e.message);
    }
  }
  
  return minecraftDataExplicit || null;
}

// Utility function to check if bot is ready for actions
function isBotReady(bot) {
  return !!(bot && bot.entity && bot.botReady && bot.mcData);
}

module.exports = {
  createBot,
  initializeBot,
  currentMcData,
  isBotReady,
  pathfinderModule,
  getagentname // Export the function so server.js can use it
};
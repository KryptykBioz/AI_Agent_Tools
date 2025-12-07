const express = require("express");
const cors = require("cors");
const { createBot, initializeBot, getBotName } = require('./bot');
const { handleAction } = require('./bot-actions');
const { getVisionData } = require('./world-info');
const fs = require("fs");
const path = require("path");

// Memory monitoring and management
let memoryWarningCount = 0;
const MEMORY_WARNING_THRESHOLD = 0.85;
const MEMORY_CRITICAL_THRESHOLD = 0.95;

function checkMemoryUsage() {
  const usage = process.memoryUsage();
  const heapUsedPercent = usage.heapUsed / usage.heapTotal;
  
  if (heapUsedPercent > MEMORY_CRITICAL_THRESHOLD) {
    console.error(`🔴 CRITICAL: Memory usage at ${(heapUsedPercent * 100).toFixed(1)}%`);
    console.error(`   Heap: ${Math.round(usage.heapUsed / 1024 / 1024)}MB / ${Math.round(usage.heapTotal / 1024 / 1024)}MB`);
    
    if (global.gc) {
      console.log('⚠️  Forcing garbage collection...');
      global.gc();
    } else {
      console.log('⚠️  Run with --expose-gc flag to enable forced garbage collection');
    }
    
    memoryWarningCount++;
    
    if (memoryWarningCount > 5) {
      console.error('💥 Memory critically high for extended period. Consider restarting.');
    }
  } else if (heapUsedPercent > MEMORY_WARNING_THRESHOLD) {
    console.warn(`⚠️  Memory usage at ${(heapUsedPercent * 100).toFixed(1)}%`);
    memoryWarningCount++;
  } else {
    memoryWarningCount = 0;
  }
}

const memoryCheckInterval = setInterval(checkMemoryUsage, 30000);

console.log('💾 Memory limits:');
console.log(`   Total heap: ${Math.round(process.memoryUsage().heapTotal / 1024 / 1024)}MB`);
console.log(`   Used heap: ${Math.round(process.memoryUsage().heapUsed / 1024 / 1024)}MB`);
if (!global.gc) {
  console.log('ℹ️  Tip: Run with NODE_OPTIONS="--expose-gc --max-old-space-size=4096" for better memory management');
}

// Find project root directory
function findProjectRoot(startDir = __dirname) {
  let currentDir = startDir;
  const maxLevels = 10;
  
  for (let i = 0; i < maxLevels; i++) {
    const personalityDir = path.join(currentDir, "personality");
    if (fs.existsSync(personalityDir) && fs.statSync(personalityDir).isDirectory()) {
      return currentDir;
    }
    
    const parentDir = path.dirname(currentDir);
    if (parentDir === currentDir) {
      break;
    }
    currentDir = parentDir;
  }
  
  console.warn("⚠️ Could not find project root (looking for personality/ directory)");
  return null;
}

// Read bot name from config
function getBotNameFromConfig() {
  const projectRoot = findProjectRoot();
  
  if (!projectRoot) {
    console.warn("⚠️ Could not find project root directory (Anna_AI/)");
    return null;
  }
  
  const configPath = path.join(projectRoot, "personality", "bot_info.py");
  
  try {
    if (fs.existsSync(configPath)) {
      const content = fs.readFileSync(configPath, "utf8");
      const match = content.match(/botname\s*=\s*["']([^"']+)["']/);
      if (match && match[1]) {
        console.log(`✅ Bot name loaded from config: ${match[1]}`);
        console.log(`   Config path: ${configPath}`);
        return match[1];
      }
    } else {
      console.warn(`⚠️ Config file not found at: ${configPath}`);
    }
  } catch (err) {
    console.warn("⚠️ Could not read bot name from bot_info.py:", err.message);
  }
  
  return null;
}

// Environment variables
const LISTEN_PORT = parseInt(process.env.LISTEN_PORT || "3001", 10);
const API_KEY = process.env.API_KEY || null;
const BOT_NAME = process.env.BOT_NAME || getBotNameFromConfig() || "MinecraftBot";

// Validate bot name
if (!BOT_NAME || BOT_NAME === "null" || BOT_NAME.trim() === "") {
  console.error("❌ Invalid bot name! Please set botname in bot_info.py or BOT_NAME environment variable");
  process.exit(1);
}

// Create Express app
const app = express();
app.use(express.json());
app.use(cors());

// Optional authentication middleware
function requireAuth(req, res, next) {
  if (!API_KEY) return next();
  const key = req.header("X-API-Key");
  if (!key || key !== API_KEY) {
    return res.status(401).json({ 
      error: "Unauthorized", 
      message: "Valid API key required" 
    });
  }
  next();
}

// Global bot instance
let bot = null;
let botInitialized = false;
let lastError = null;

// Initialize bot with retry logic
async function initializeBotWithRetry(maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`🎮 Bot initialization attempt ${attempt}/${maxRetries}`);
      bot = createBot();
      initializeBot(bot);
      
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error("Bot initialization timeout"));
        }, 30000);
        
        bot.once('spawn', () => {
          setTimeout(() => {
            clearTimeout(timeout);
            botInitialized = true;
            lastError = null;
            console.log("✅ Bot initialized successfully");
            resolve();
          }, 2000);
        });
        
        bot.once('error', (err) => {
          clearTimeout(timeout);
          lastError = err;
          reject(err);
        });
      });
      
      break;
      
    } catch (err) {
      console.error(`❌ Bot initialization attempt ${attempt} failed:`, err.message);
      lastError = err;
      botInitialized = false;
      
      if (bot) {
        try {
          bot.end();
        } catch (e) {
          // Ignore cleanup errors
        }
      }
      bot = null;
      
      if (attempt < maxRetries) {
        console.log(`⏳ Retrying in 5 seconds...`);
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
    }
  }
  
  if (!botInitialized) {
    console.error("💥 Failed to initialize bot after all attempts");
  }
}

// ============================================================================
// API ENDPOINTS
// ============================================================================

// Health check
app.get("/api/health", (req, res) => {
  const mem = process.memoryUsage();
  const heapUsedPercent = (mem.heapUsed / mem.heapTotal * 100).toFixed(1);
  
  res.json({
    status: "online",
    botConnected: !!bot,
    botSpawned: !!(bot && bot.entity),
    botReady: !!(bot && bot.botReady),
    lastError: lastError ? lastError.message : null,
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: {
      heapUsed: Math.round(mem.heapUsed / 1024 / 1024) + 'MB',
      heapTotal: Math.round(mem.heapTotal / 1024 / 1024) + 'MB',
      heapPercent: heapUsedPercent + '%',
      rss: Math.round(mem.rss / 1024 / 1024) + 'MB'
    }
  });
});

// Vision endpoint
app.get("/api/vision", (req, res) => {
  try {
    if (!bot) {
      return res.status(503).json({
        status: "error",
        error: "Bot not connected",
        lastError: lastError ? lastError.message : null
      });
    }
    
    if (!bot.entity) {
      return res.status(503).json({
        status: "error",
        error: "Bot not spawned in world yet"
      });
    }
    
    const visionData = getVisionData(bot);
    res.json({
      status: "success",
      vision: visionData
    });
    console.log("✅ Sent vision data");
    
  } catch (err) {
    console.error("[Vision] Error:", err);
    return res.status(500).json({
      status: "error",
      error: "Failed to get bot vision: " + (err.message || String(err)),
      stack: process.env.NODE_ENV === "development" ? err.stack : undefined,
    });
  }
});

// Action endpoint - UPDATED FOR STRUCTURED COMMANDS
app.post("/api/action", async (req, res) => {
  const { action, args } = req.body;
  
  // Validate request format
  if (!action) {
    return res.status(400).json({
      status: 'error',
      error: 'Missing "action" field',
      expected_format: {
        action: "gather",
        args: ["wood", 1]
      },
      received: req.body
    });
  }
  
  if (!bot || !bot.entity) {
    return res.status(503).json({
      status: 'error',
      error: 'Bot not ready',
      botConnected: !!bot,
      botSpawned: !!(bot && bot.entity)
    });
  }
  
  // Execute action
  await handleAction(req, res, bot);
});

// Legacy endpoint (for backward compatibility with old natural language format)
app.post("/api/act", async (req, res) => {
  const { text } = req.body;
  
  if (text) {
    // Legacy natural language format - not supported anymore
    return res.status(400).json({
      status: 'error',
      error: 'Natural language commands no longer supported',
      message: 'Use structured format instead',
      expected_format: {
        action: "gather",
        args: ["wood", 1]
      },
      received: { text }
    });
  }
  
  // Try new format
  return app.post("/api/action")(req, res);
});

// Status endpoint
app.get("/api/status", (req, res) => {
  const inv = bot && bot.inventory
    ? bot.inventory.items().map((i) => ({ 
        id: i.type, 
        count: i.count, 
        name: i.name,
        displayName: i.displayName
      }))
    : [];
    
  const pos = bot && bot.entity ? {
    x: Math.round(bot.entity.position.x * 100) / 100,
    y: Math.round(bot.entity.position.y * 100) / 100,
    z: Math.round(bot.entity.position.z * 100) / 100
  } : null;

  res.json({
    connected: !!bot,
    spawned: !!bot?.entity,
    ready: bot?.botReady || false,
    initialized: botInitialized,
    
    position: pos,
    health: bot?.health || null,
    food: bot?.food || null,
    experience: bot?.experience || null,
    gameMode: bot?.game?.gameMode || null,
    dimension: bot?.game?.dimension || null,
    
    inventory: inv,
    inventoryCount: inv.length,
    
    version: bot?.version || null,
    pluginsLoaded: bot?.pluginsLoaded || false,
    mcDataAvailable: !!(bot?.mcData),
    mcDataVersion: bot?.mcData?.version || null,
    
    serverInfo: {
      host: process.env.MC_HOST || "localhost",
      port: parseInt(process.env.MC_PORT || "63968", 10),
      botName: BOT_NAME,
    },
    
    lastError: lastError ? lastError.message : null,
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error("[Server] Unhandled error:", err);
  res.status(500).json({
    status: "error",
    error: "Internal server error",
    message: err.message,
    timestamp: new Date().toISOString()
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    status: "error",
    error: "Endpoint not found",
    available_endpoints: [
      "GET /api/health",
      "GET /api/vision", 
      "POST /api/action",
      "GET /api/status"
    ]
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('🛑 SIGTERM received, shutting down gracefully');
  clearInterval(memoryCheckInterval);
  if (bot) {
    bot.end();
  }
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('🛑 SIGINT received, shutting down gracefully');
  clearInterval(memoryCheckInterval);
  if (bot) {
    bot.end();
  }
  process.exit(0);
});

// Start server
async function start() {
  const server = app.listen(LISTEN_PORT, "127.0.0.1", () => {
    console.log(
      `🌐 Minecraft Bot API listening on http://127.0.0.1:${LISTEN_PORT}` +
      (API_KEY ? " (API key required)" : " (no API key configured)")
    );
    console.log(`🤖 Bot name configured as: ${BOT_NAME}`);
    console.log(`📝 NOTE: Now accepts structured commands: {"action": "gather", "args": ["wood"]}`);
  });
  
  await initializeBotWithRetry();
  
  return { app, bot, server };
}

module.exports = { app, bot: () => bot, start };

if (require.main === module) {
  start().catch(err => {
    console.error("💥 Failed to start server:", err);
    process.exit(1);
  });
}
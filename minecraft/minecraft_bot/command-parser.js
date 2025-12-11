/**
 * command-parser.js - Robust LLM-based command parsing
 */

const axios = require('axios');

const OLLAMA_HOST = process.env.OLLAMA_HOST || 'http://localhost:11434';
const OLLAMA_MODEL = process.env.OLLAMA_MODEL || 'llama3.2:3b-instruct-q4_K_M';
const OLLAMA_TIMEOUT = 8000;

let errorCount = 0;

async function parseCommandWithLLM(text, context = {}) {
  const startTime = Date.now();
  
  try {
    const systemPrompt = "You are a Minecraft command parser. Extract ONE action from text and return ONLY valid JSON.";
    const userPrompt = buildImprovedPrompt(text, context);
    
    const response = await axios.post(
      `${OLLAMA_HOST}/api/chat`,
      {
        model: OLLAMA_MODEL,
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: userPrompt }
        ],
        stream: false,
        options: {
          temperature: 0.1,
          num_predict: 100,
          top_p: 0.9
        }
      },
      { timeout: OLLAMA_TIMEOUT }
    );
    
    const responseText = response.data?.message?.content?.trim() || '';
    
    if (!responseText) {
      return { action: 'none', reason: 'empty_response' };
    }
    
    const parsed = parseJSONResponse(responseText, context);
    const duration = Date.now() - startTime;
    
    console.log(`[LLM Parser] ${duration}ms: "${text.substring(0, 40)}..." -> ${parsed.action}`);
    
    return parsed;
    
  } catch (err) {
    errorCount++;
    if (errorCount % 5 === 1) {
      console.warn(`[LLM Parser] Error:`, err.message);
    }
    throw err;
  }
}

function buildImprovedPrompt(text, context) {
  return `Extract ONE Minecraft action from user text. Return ONLY ONE JSON object.

EXAMPLES:
"Let's gather some sand" → {"action": "gather", "resource": "sand", "count": 1}
"Get me 5 wood" → {"action": "gather", "resource": "oak_log", "count": 5}
"Collect stone" → {"action": "gather", "resource": "stone", "count": 1}
"Follow me" → {"action": "follow", "target": "player"}
"Stop" → {"action": "stop"}

RESOURCE MAPPING (use exact names):
- wood/tree/log → "oak_log"
- stone/rock → "stone"
- sand → "sand"
- gravel → "gravel"
- dirt → "dirt"
- cobblestone/cobble → "cobblestone"
- coal → "coal_ore"
- iron → "iron_ore"

USER TEXT: "${text}"

RULES:
1. Return ONLY ONE action (the first/primary one)
2. Use exact resource names from mapping
3. If no clear action → {"action": "none"}
4. Return ONLY JSON, no extra text or arrays

JSON:`;
}

function parseJSONResponse(responseText, context = {}) {
  try {
    // Extract first JSON object only
    let jsonText = responseText;
    
    // Remove markdown code blocks
    jsonText = jsonText.replace(/```json\s*/g, '').replace(/```\s*/g, '');
    
    // Find first complete JSON object
    const firstBrace = jsonText.indexOf('{');
    if (firstBrace === -1) {
      return { action: 'none', reason: 'no_json' };
    }
    
    let braceCount = 0;
    let endPos = firstBrace;
    
    for (let i = firstBrace; i < jsonText.length; i++) {
      if (jsonText[i] === '{') braceCount++;
      if (jsonText[i] === '}') braceCount--;
      if (braceCount === 0) {
        endPos = i + 1;
        break;
      }
    }
    
    jsonText = jsonText.substring(firstBrace, endPos);
    
    let parsed = JSON.parse(jsonText);
    
    // Validate action
    const validActions = [
      'stop', 'follow', 'goto', 'come', 'gather', 'build',
      'give', 'attack', 'defend', 'flee', 'equip', 'craft',
      'use', 'look', 'status', 'chat', 'none'
    ];
    
    if (!validActions.includes(parsed.action)) {
      return { action: 'none', reason: 'invalid_action' };
    }
    
    // Normalize parameters
    parsed = normalizeParameters(parsed, context);
    
    return parsed;
    
  } catch (err) {
    console.warn('[LLM Parser] JSON parse error:', err.message);
    return { action: 'none', reason: 'parse_error' };
  }
}

function normalizeParameters(parsed, context) {
  // Normalize follow target
  if (parsed.action === 'follow') {
    if (!parsed.target || parsed.target === 'me' || parsed.target === 'you') {
      parsed.target = context.nearbyPlayers?.[0] || 'player';
    }
  }
  
  // Normalize gather
  if (parsed.action === 'gather') {
    if (!parsed.resource) {
      return { action: 'none', reason: 'missing_resource' };
    }
    
    parsed.resource = normalizeResourceName(parsed.resource);
    parsed.count = parsed.count || 1;
  }
  
  // Normalize goto coordinates
  if (parsed.action === 'goto') {
    parsed.x = parseFloat(parsed.x || 0);
    parsed.y = parseFloat(parsed.y || 0);
    parsed.z = parseFloat(parsed.z || 0);
  }
  
  return parsed;
}

function normalizeResourceName(name) {
  const normalized = name.toLowerCase().trim().replace(/[^a-z_]/g, '');
  
  const aliases = {
    'wood': 'oak_log',
    'woods': 'oak_log',
    'log': 'oak_log',
    'logs': 'oak_log',
    'tree': 'oak_log',
    'trees': 'oak_log',
    'oak': 'oak_log',
    'oaklog': 'oak_log',
    'woodtreelog': 'oak_log',
    'treelog': 'oak_log',
    'cobble': 'cobblestone',
    'rock': 'stone',
    'rocks': 'stone',
    'coal': 'coal_ore',
    'iron': 'iron_ore',
    'gold': 'gold_ore',
    'diamond': 'diamond_ore',
    'diamonds': 'diamond_ore'
  };
  
  return aliases[normalized] || normalized || name;
}

async function checkOllamaAvailability() {
  try {
    const response = await axios.get(`${OLLAMA_HOST}/api/tags`, { timeout: 3000 });
    
    const models = response.data?.models || [];
    const modelExists = models.some(m => 
      m.name === OLLAMA_MODEL || m.name.startsWith(OLLAMA_MODEL.split(':')[0])
    );
    
    if (!modelExists) {
      console.warn(`[WARNING] Model '${OLLAMA_MODEL}' not found`);
      return false;
    }
    
    console.log(`[SUCCESS] Ollama ready (${OLLAMA_HOST}, model: ${OLLAMA_MODEL})`);
    return true;
    
  } catch (err) {
    console.warn('[WARNING] Ollama unavailable:', err.message);
    return false;
  }
}

module.exports = {
  parseCommandWithLLM,
  checkOllamaAvailability
};
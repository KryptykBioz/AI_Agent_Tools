# Filename: BASE/tools/mindcraft_connector.py
import re
import json
import time
import requests
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ActionPattern:
    """Represents a pattern to match and its corresponding Mindcraft action"""
    pattern: str
    action_type: str
    parameters: Dict
    priority: int = 1
    
class MindcraftConnector:
    """
    Isolated connector that translates natural language responses into Mindcraft commands.
    Integrates with existing bot.py with minimal modifications.
    """
    
    def __init__(self, mindcraft_host: str = "localhost", mindcraft_port: int = 3000, 
                 bot_name: str = "assistant", debug: bool = False):
        self.mindcraft_host = mindcraft_host
        self.mindcraft_port = mindcraft_port
        self.mindcraft_url = f"http://{mindcraft_host}:{mindcraft_port}"
        self.bot_name = bot_name
        self.debug = debug
        
        # Connection state
        self.connected = False
        self.last_health_check = 0
        self.health_check_interval = 30  # seconds
        
        # Action patterns - maps natural language to Mindcraft commands
        self.action_patterns = self._initialize_action_patterns()
        
        # Compile regex patterns for efficiency
        self.compiled_patterns = []
        for pattern_data in self.action_patterns:
            try:
                compiled = re.compile(pattern_data.pattern, re.IGNORECASE)
                self.compiled_patterns.append((compiled, pattern_data))
            except re.error as e:
                print(f"[MindcraftConnector] Warning: Invalid regex pattern '{pattern_data.pattern}': {e}")
        
        # Sort by priority (higher priority first)
        self.compiled_patterns.sort(key=lambda x: x[1].priority, reverse=True)
        
        print(f"[MindcraftConnector] Initialized with {len(self.compiled_patterns)} action patterns")
        
        # Test connection on startup
        self._test_connection()
    
    def _initialize_action_patterns(self) -> List[ActionPattern]:
        """Initialize the action patterns that map natural language to Mindcraft commands"""
        patterns = [
            # Resource gathering - High priority
            ActionPattern(
                r"(?:i'll|i will|let me|going to|gonna)?\s*(?:go\s+)?(?:get|gather|collect|harvest|mine|chop)\s+(?:some\s+)?(\w+)(?:\s+from\s+(?:a\s+)?(\w+))?",
                "gather_resource",
                {"resource_type": 1, "source_type": 2},
                priority=10
            ),
            ActionPattern(
                r"(?:mine|dig)\s+(?:for\s+)?(?:some\s+)?(\w+)",
                "mine_resource", 
                {"resource": 1},
                priority=9
            ),
            ActionPattern(
                r"(?:chop|cut)\s+(?:down\s+)?(?:a\s+|some\s+)?(?:tree|wood|log)",
                "chop_wood",
                {},
                priority=9
            ),
            
            # Movement - Medium priority
            ActionPattern(
                r"(?:go\s+to|travel\s+to|head\s+to|move\s+to|walk\s+to)\s+(.+)",
                "goto",
                {"location": 1},
                priority=8
            ),
            ActionPattern(
                r"(?:follow\s+me|come\s+here|come\s+to\s+me)",
                "follow",
                {"target": "player"},
                priority=7
            ),
            ActionPattern(
                r"(?:stop|halt|wait|pause)",
                "stop",
                {},
                priority=6
            ),
            
            # Building - Medium priority
            ActionPattern(
                r"(?:build|construct|make)\s+(?:a\s+)?(\w+)(?:\s+(?:with|using|from)\s+(\w+))?",
                "build",
                {"structure": 1, "material": 2},
                priority=7
            ),
            ActionPattern(
                r"(?:place|put)\s+(?:a\s+|some\s+)?(\w+)(?:\s+(?:at|on|in)\s+(.+))?",
                "place_block",
                {"block_type": 1, "location": 2},
                priority=6
            ),
            
            # Combat - High priority
            ActionPattern(
                r"(?:attack|fight|kill)\s+(?:the\s+)?(\w+)",
                "attack",
                {"target": 1},
                priority=9
            ),
            ActionPattern(
                r"(?:defend|protect)\s+(?:me|us|yourself)",
                "defend",
                {},
                priority=8
            ),
            
            # Crafting - Medium priority  
            ActionPattern(
                r"(?:craft|make)\s+(?:a\s+|some\s+)?(\w+)(?:\s+(?:with|using)\s+(.+))?",
                "craft",
                {"item": 1, "materials": 2},
                priority=6
            ),
            
            # Exploration - Low priority
            ActionPattern(
                r"(?:explore|search)\s+(?:the\s+)?(\w+)",
                "explore",
                {"area": 1},
                priority=5
            ),
            ActionPattern(
                r"(?:find|look\s+for|search\s+for)\s+(?:a\s+|some\s+)?(\w+)",
                "find",
                {"target": 1},
                priority=5
            ),
            
            # Inventory management - Low priority
            ActionPattern(
                r"(?:drop|throw\s+away|discard)\s+(?:the\s+|some\s+|my\s+)?(\w+)",
                "drop_item",
                {"item": 1},
                priority=4
            ),
            ActionPattern(
                r"(?:equip|wear|hold)\s+(?:the\s+|my\s+)?(\w+)",
                "equip",
                {"item": 1},
                priority=4
            ),
        ]
        return patterns
    
    def _test_connection(self) -> bool:
        """Test connection to Mindcraft server"""
        try:
            response = requests.get(f"{self.mindcraft_url}/health", timeout=5)
            if response.status_code == 200:
                self.connected = True
                self.last_health_check = time.time()
                if self.debug:
                    print(f"[MindcraftConnector] Successfully connected to Mindcraft at {self.mindcraft_url}")
                return True
            else:
                self.connected = False
                if self.debug:
                    print(f"[MindcraftConnector] Mindcraft server returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.connected = False
            if self.debug:
                print(f"[MindcraftConnector] Failed to connect to Mindcraft: {e}")
            return False
    
    def _check_connection(self) -> bool:
        """Check if we need to test connection again"""
        if not self.connected or (time.time() - self.last_health_check) > self.health_check_interval:
            return self._test_connection()
        return self.connected
    
    def _send_mindcraft_command(self, command: Dict) -> bool:
        """Send a command to Mindcraft server"""
        if not self._check_connection():
            print(f"[MindcraftConnector] Cannot send command - not connected to Mindcraft")
            return False
        
        try:
            # Add bot identification
            command["bot_name"] = self.bot_name
            command["timestamp"] = time.time()
            
            if self.debug:
                print(f"[MindcraftConnector] Sending command: {json.dumps(command, indent=2)}")
            
            response = requests.post(
                f"{self.mindcraft_url}/command",
                json=command,
                timeout=10
            )
            
            if response.status_code == 200:
                if self.debug:
                    print(f"[MindcraftConnector] Command sent successfully")
                return True
            else:
                print(f"[MindcraftConnector] Command failed with status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"[MindcraftConnector] Failed to send command: {e}")
            return False
    
    def _extract_parameters(self, match, param_config: Dict) -> Dict:
        """Extract parameters from regex match based on configuration"""
        params = {}
        for param_name, group_index in param_config.items():
            if isinstance(group_index, int) and group_index <= len(match.groups()):
                value = match.group(group_index)
                if value:
                    params[param_name] = value.strip()
            elif isinstance(group_index, str):
                params[param_name] = group_index
        return params
    
    def _translate_resource_name(self, resource: str) -> str:
        """Translate common resource names to Minecraft equivalents"""
        translation_map = {
            "wood": "oak_log",
            "stone": "stone",
            "iron": "iron_ore", 
            "gold": "gold_ore",
            "diamond": "diamond_ore",
            "coal": "coal_ore",
            "tree": "oak_log",
            "logs": "oak_log",
            "rocks": "stone",
            "dirt": "dirt",
            "sand": "sand",
            "cobblestone": "cobblestone",
            "planks": "oak_planks"
        }
        return translation_map.get(resource.lower(), resource.lower())
    
    def _create_mindcraft_command(self, action_type: str, params: Dict) -> Optional[Dict]:
        """Create a Mindcraft command from action type and parameters"""
        
        if action_type == "gather_resource":
            resource = params.get("resource_type", "")
            source = params.get("source_type", "")
            
            # Translate resource names
            minecraft_resource = self._translate_resource_name(resource)
            
            if source and "tree" in source.lower():
                return {
                    "action": "gather",
                    "target": "oak_log",
                    "method": "chop",
                    "quantity": 10
                }
            elif "ore" in minecraft_resource:
                return {
                    "action": "mine",
                    "target": minecraft_resource,
                    "quantity": 5
                }
            else:
                return {
                    "action": "gather", 
                    "target": minecraft_resource,
                    "quantity": 5
                }
        
        elif action_type == "mine_resource":
            resource = self._translate_resource_name(params.get("resource", ""))
            return {
                "action": "mine",
                "target": resource,
                "quantity": 5
            }
        
        elif action_type == "chop_wood":
            return {
                "action": "gather",
                "target": "oak_log", 
                "method": "chop",
                "quantity": 10
            }
        
        elif action_type == "goto":
            location = params.get("location", "")
            return {
                "action": "goto",
                "target": location
            }
        
        elif action_type == "follow":
            return {
                "action": "follow",
                "target": params.get("target", "player")
            }
        
        elif action_type == "stop":
            return {
                "action": "stop"
            }
        
        elif action_type == "build":
            structure = params.get("structure", "")
            material = params.get("material", "")
            return {
                "action": "build",
                "structure": structure,
                "material": self._translate_resource_name(material) if material else "oak_planks"
            }
        
        elif action_type == "place_block":
            block_type = self._translate_resource_name(params.get("block_type", ""))
            location = params.get("location", "")
            return {
                "action": "place",
                "block": block_type,
                "location": location
            }
        
        elif action_type == "attack":
            target = params.get("target", "")
            return {
                "action": "attack",
                "target": target
            }
        
        elif action_type == "defend":
            return {
                "action": "defend"
            }
        
        elif action_type == "craft":
            item = params.get("item", "")
            materials = params.get("materials", "")
            return {
                "action": "craft",
                "item": item,
                "materials": materials
            }
        
        elif action_type == "explore":
            area = params.get("area", "")
            return {
                "action": "explore",
                "area": area
            }
        
        elif action_type == "find":
            target = params.get("target", "")
            return {
                "action": "find",
                "target": target
            }
        
        elif action_type == "drop_item":
            item = params.get("item", "")
            return {
                "action": "drop",
                "item": item
            }
        
        elif action_type == "equip":
            item = params.get("item", "")
            return {
                "action": "equip",
                "item": item
            }
        
        return None
    
    def process_response(self, response_text: str) -> List[Dict]:
        """
        Process a natural language response and extract Mindcraft commands.
        Returns a list of commands to execute.
        """
        if not response_text or not response_text.strip():
            return []
        
        commands = []
        text = response_text.strip()
        
        if self.debug:
            print(f"[MindcraftConnector] Processing response: '{text}'")
        
        # Try to match patterns (sorted by priority)
        for compiled_pattern, pattern_data in self.compiled_patterns:
            match = compiled_pattern.search(text)
            if match:
                if self.debug:
                    print(f"[MindcraftConnector] Matched pattern: {pattern_data.pattern}")
                    print(f"[MindcraftConnector] Match groups: {match.groups()}")
                
                # Extract parameters
                params = self._extract_parameters(match, pattern_data.parameters)
                
                if self.debug:
                    print(f"[MindcraftConnector] Extracted parameters: {params}")
                
                # Create Mindcraft command
                command = self._create_mindcraft_command(pattern_data.action_type, params)
                if command:
                    commands.append(command)
                    if self.debug:
                        print(f"[MindcraftConnector] Created command: {json.dumps(command, indent=2)}")
                
                # For now, only process the first match to avoid conflicting commands
                break
        
        if not commands and self.debug:
            print(f"[MindcraftConnector] No action patterns matched for: '{text}'")
        
        return commands
    
    def execute_commands(self, commands: List[Dict]) -> bool:
        """Execute a list of Mindcraft commands"""
        if not commands:
            return True
        
        success = True
        for command in commands:
            if not self._send_mindcraft_command(command):
                success = False
        
        return success
    
    def process_and_execute(self, response_text: str) -> bool:
        """
        Convenience method to process a response and execute any resulting commands.
        Returns True if all commands were sent successfully.
        """
        commands = self.process_response(response_text)
        if commands:
            print(f"[MindcraftConnector] Executing {len(commands)} command(s) for response")
            return self.execute_commands(commands)
        return True
    
    def get_status(self) -> Dict:
        """Get connector status information"""
        return {
            "connected": self.connected,
            "mindcraft_url": self.mindcraft_url,
            "bot_name": self.bot_name,
            "patterns_loaded": len(self.compiled_patterns),
            "last_health_check": self.last_health_check
        }

# Integration helper functions for bot.py

def create_mindcraft_connector(config: Optional[Dict] = None) -> MindcraftConnector:
    """Factory function to create a MindcraftConnector with configuration"""
    if config is None:
        config = {}
    
    return MindcraftConnector(
        mindcraft_host=config.get("host", "localhost"),
        mindcraft_port=config.get("port", 3000),
        bot_name=config.get("bot_name", "assistant"),
        debug=config.get("debug", False)
    )

def process_response_for_minecraft(connector: MindcraftConnector, response: str) -> None:
    """
    Helper function to process a bot response for Minecraft actions.
    This can be called from bot.py after generating a response.
    """
    try:
        connector.process_and_execute(response)
    except Exception as e:
        print(f"[MindcraftConnector] Error processing response for Minecraft: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Test the connector
    connector = MindcraftConnector(debug=True)
    
    test_responses = [
        "I'll go get some wood from a tree",
        "Let me mine some iron ore",
        "I'll gather coal for you",
        "Going to build a house with stone",
        "I'll follow you",
        "Let me craft some tools",
        "I'll attack that zombie",
        "Going to explore the cave"
    ]
    
    print("\n=== Testing Action Pattern Matching ===")
    for response in test_responses:
        print(f"\nTesting: '{response}'")
        commands = connector.process_response(response)
        if commands:
            print(f"Generated {len(commands)} command(s):")
            for cmd in commands:
                print(f"  {json.dumps(cmd, indent=2)}")
        else:
            print("  No commands generated")
    
    print(f"\n=== Connector Status ===")
    status = connector.get_status()
    for key, value in status.items():
        print(f"{key}: {value}")
# Filename: BASE/tools/installed/warudo/tool.py
"""
Warudo Animation Tool - FIXED Connection Logic
Ensures proper WebSocket connection on initialization
"""
from typing import List, Dict, Any
import asyncio
from BASE.handlers.base_tool import BaseTool
from BASE.tools.installed.warudo.animate_avatar import WarudoManager


class WarudoAnimationTool(BaseTool):
    """
    Warudo animation tool for controlling avatar expressions and animations
    Manages WebSocket connection to Warudo and executes emotion/animation commands
    
    FIXES:
    - Actually connect during initialization
    - Fail initialization if Warudo not running (tool will be disabled)
    - Auto-reconnect on execute if connection drops
    """
    
    __slots__ = (
        'manager', '_websocket_url', '_agent_name', 
        '_connection_attempts', '_max_attempts'
    )
    
    @property
    def name(self) -> str:
        return "warudo"
    
    async def initialize(self) -> bool:
        """
        Initialize Warudo WebSocket connection
        
        FIXED: Actually establish connection during init
        Returns False if connection fails (tool will be disabled)
        """
        websocket_url = getattr(
            self._config, 
            'warudo_websocket_url', 
            'ws://127.0.0.1:19190'
        )
        
        agent_name = None
        
        if hasattr(self._config, 'agentname'):
            agent_name = self._config.agentname
        
        if not agent_name:
            try:
                from personality.bot_info import agentname
                agent_name = agentname
            except:
                pass
        
        if not agent_name:
            try:
                from BASE.personality.bot_info import agentname
                agent_name = agentname
            except:
                pass
        
        if not agent_name:
            agent_name = 'agent'
        
        if self._logger:
            self._logger.system(f"[Warudo] Initializing for agent '{agent_name}' at {websocket_url}")
        
        try:
            self.manager = WarudoManager(
                websocket_url=websocket_url,
                agent_name=agent_name,
                auto_connect=True,
                timeout=3.0
            )
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Warudo] Failed to create manager: {e}")
            return False
        
        self._websocket_url = websocket_url
        self._agent_name = agent_name
        self._connection_attempts = 0
        self._max_attempts = 3
        
        if not self.manager.controller.ws_connected:
            if self._logger:
                self._logger.warning(
                    "[Warudo] Initial connection failed. "
                    "Ensure Warudo is running with WebSocket enabled."
                )
            return False
        
        if self._logger:
            emotions = len(self.manager.controller.available_emotions)
            animations = len(self.manager.controller.available_animations)
            self._logger.success(
                f"[Warudo] Connected successfully!\n"
                f"  Agent: {agent_name}\n"
                f"  Available: {emotions} emotions, {animations} animations"
            )
        
        return True
    
    async def _ensure_connection(self) -> bool:
        """
        Ensure WebSocket connection is active
        Attempts reconnection if needed
        
        Returns:
            True if connected, False otherwise
        """
        if self.manager.controller.ws_connected:
            return True
        
        if self._connection_attempts >= self._max_attempts:
            if self._logger:
                self._logger.error(
                    f"[Warudo] Max connection attempts ({self._max_attempts}) exceeded"
                )
            return False
        
        self._connection_attempts += 1
        
        if self._logger:
            self._logger.system(
                f"[Warudo] Reconnecting (attempt {self._connection_attempts}/{self._max_attempts})..."
            )
        
        try:
            loop = asyncio.get_event_loop()
            connected = await loop.run_in_executor(
                None, 
                self.manager.connect,
                3.0
            )
            
            if connected:
                self._connection_attempts = 0
                if self._logger:
                    self._logger.success("[Warudo] Reconnected successfully")
                return True
            else:
                if self._logger:
                    self._logger.warning("[Warudo] Reconnection failed")
                return False
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Warudo] Reconnection error: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup Warudo resources"""
        if hasattr(self, 'manager') and self.manager:
            if hasattr(self.manager, 'controller'):
                self.manager.controller.shutdown()
        
        if self._logger:
            self._logger.system("[Warudo] Cleaned up WebSocket connection")
    
    def is_available(self) -> bool:
        """
        Check if Warudo WebSocket is connected
        
        Returns:
            True if connected and ready, False otherwise
        """
        if not hasattr(self, 'manager'):
            return False
        
        if not self.manager:
            return False
        
        if not hasattr(self.manager, 'controller'):
            return False
        
        return self.manager.controller.ws_connected
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute Warudo animation command
        
        Commands:
        - emotion: [emotion_name: str] - Set avatar emotion/expression
        - animation: [animation_name: str] - Play avatar animation
        
        Auto-reconnects if connection dropped
        
        Args:
            command: Command name ('emotion' or 'animation')
            args: Command arguments
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[Warudo] Command: '{command}', args: {args}")
        
        connected = await self._ensure_connection()
        
        if not connected:
            return self._error_result(
                'Failed to connect to Warudo',
                metadata={
                    'websocket_url': self._websocket_url,
                    'attempts': self._connection_attempts
                },
                guidance=(
                    'Ensure Warudo is running and WebSocket server is enabled. '
                    'Check Settings -> Plugins -> WebSocket API in Warudo.'
                )
            )
        
        if not command:
            return self._error_result(
                'No command provided',
                guidance='Use: warudo.emotion or warudo.animation'
            )
        
        if command == 'emotion':
            return await self._handle_emotion(args)
        elif command == 'animation':
            return await self._handle_animation(args)
        else:
            return self._error_result(
                f'Unknown command: {command}',
                guidance='Available commands: emotion, animation'
            )
    
    async def _handle_emotion(self, args: List[Any]) -> Dict[str, Any]:
        """Handle emotion command"""
        if not args:
            available = self.manager.controller.available_emotions
            return self._error_result(
                'No emotion specified',
                metadata={'available_emotions': available},
                guidance=f'Available emotions: {", ".join(available)}'
            )
        
        emotion = str(args[0]).lower()
        available = self.manager.controller.available_emotions
        
        if emotion not in available:
            return self._error_result(
                f'Unknown emotion: {emotion}',
                metadata={'available_emotions': available},
                guidance=f'Available emotions: {", ".join(available)}'
            )
        
        if self._logger:
            self._logger.tool(f"[Warudo] Setting emotion: {emotion}")
        
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(
            None,
            self.manager.send_emotion,
            emotion
        )
        
        if success:
            if self._logger:
                self._logger.success(f"[Warudo] Emotion set: {emotion}")
            return self._success_result(
                f'Set emotion to {emotion}', 
                metadata={'emotion': emotion}
            )
        else:
            if self._logger:
                self._logger.error(f"[Warudo] Failed to set emotion: {emotion}")
            
            self.manager.controller.ws_connected = False
            
            return self._error_result(
                'Failed to set emotion (WebSocket send failed)',
                metadata={'emotion': emotion},
                guidance='Connection may have been lost - will reconnect on next attempt'
            )
    
    async def _handle_animation(self, args: List[Any]) -> Dict[str, Any]:
        """Handle animation command"""
        if not args:
            available = self.manager.controller.available_animations
            return self._error_result(
                'No animation specified',
                metadata={'available_animations': available},
                guidance=f'Available animations: {", ".join(available)}'
            )
        
        animation = str(args[0]).lower()
        available = self.manager.controller.available_animations
        
        if animation not in available:
            return self._error_result(
                f'Unknown animation: {animation}',
                metadata={'available_animations': available},
                guidance=f'Available animations: {", ".join(available)}'
            )
        
        if self._logger:
            self._logger.tool(f"[Warudo] Playing animation: {animation}")
        
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(
            None,
            self.manager.send_animation,
            animation
        )
        
        if success:
            if self._logger:
                self._logger.success(f"[Warudo] Animation played: {animation}")
            return self._success_result(
                f'Played animation: {animation}', 
                metadata={'animation': animation}
            )
        else:
            if self._logger:
                self._logger.error(f"[Warudo] Failed to play animation: {animation}")
            
            self.manager.controller.ws_connected = False
            
            return self._error_result(
                'Failed to play animation (WebSocket send failed)',
                metadata={'animation': animation},
                guidance='Connection may have been lost - will reconnect on next attempt'
            )
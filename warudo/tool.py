# Filename: BASE/tools/installed/warudo/tool.py
"""
Warudo Animation Tool - Simplified Architecture
Single master class for controlling Warudo avatar animations and emotions
"""
from typing import List, Dict, Any
from BASE.handlers.base_tool import BaseTool
from BASE.tools.installed.warudo.animate_avatar import WarudoManager


class WarudoAnimationTool(BaseTool):
    """
    Warudo animation tool for controlling avatar expressions and animations
    Manages WebSocket connection to Warudo and executes emotion/animation commands
    """
    
    @property
    def name(self) -> str:
        return "warudo"
    
    async def initialize(self) -> bool:
        """Initialize Warudo WebSocket connection"""
        # Get WebSocket URL from config
        websocket_url = getattr(
            self._config, 
            'warudo_websocket_url', 
            'ws://127.0.0.1:19190'
        )
        
        # Create WarudoManager
        self.manager = WarudoManager(
            websocket_url=websocket_url,
            auto_connect=True,
            timeout=2.0,
            gui_logger=None
        )
        
        # Check connection status
        connected = self.manager.controller.ws_connected
        
        if self._logger:
            if connected:
                emotions = len(self.manager.controller.available_emotions)
                animations = len(self.manager.controller.available_animations)
                self._logger.system(
                    f"[Warudo] Connected: {emotions} emotions, "
                    f"{animations} animations available"
                )
            else:
                self._logger.warning(
                    "[Warudo] Not connected - will attempt reconnection on use"
                )
        
        # Return True even if not connected - tool can retry later
        return True
    
    async def cleanup(self):
        """Cleanup Warudo resources"""
        if hasattr(self, 'manager') and self.manager:
            if hasattr(self.manager, 'controller'):
                self.manager.controller.shutdown()
        
        if self._logger:
            self._logger.system("[Warudo] Cleaned up WebSocket connection")
    
    def is_available(self) -> bool:
        """Check if Warudo WebSocket is connected"""
        if not hasattr(self, 'manager'):
            return False
        return self.manager.controller.ws_connected
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute Warudo animation command
        
        Commands:
        - emotion: [emotion_name: str] - Set avatar emotion/expression
        - animation: [animation_name: str] - Play avatar animation
        
        Args:
            command: Command name ('emotion' or 'animation')
            args: Command arguments
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[Warudo] Command: '{command}', args: {args}")
        
        # Check connection
        if not self.is_available():
            # Attempt reconnection
            websocket_url = getattr(
                self._config, 
                'warudo_websocket_url', 
                'ws://127.0.0.1:19190'
            )
            
            if self._logger:
                self._logger.warning("[Warudo] Not connected - attempting reconnection")
            
            connected = self.manager.connect(timeout=2.0)
            
            if not connected:
                return self._error_result(
                    'Warudo not connected',
                    metadata={'websocket_url': websocket_url},
                    guidance='Ensure Warudo is running and WebSocket server is active'
                )
        
        # Validate command
        if not command:
            return self._error_result(
                'No command provided',
                guidance='Use: warudo.emotion or warudo.animation'
            )
        
        # Route to appropriate handler
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
        
        success = self.manager.send_emotion(emotion)
        
        if success:
            if self._logger:
                self._logger.success(f"[Warudo] Emotion set: {emotion}")
            return self._success_result(f'Set emotion to {emotion}', metadata={'emotion': emotion})
        else:
            if self._logger:
                self._logger.error(f"[Warudo] Failed to set emotion: {emotion}")
            return self._error_result(
                'Failed to set emotion (WebSocket send failed)',
                metadata={'emotion': emotion},
                guidance='Check Warudo WebSocket connection'
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
        
        success = self.manager.send_animation(animation)
        
        if success:
            if self._logger:
                self._logger.success(f"[Warudo] Animation played: {animation}")
            return self._success_result(f'Played animation: {animation}', metadata={'animation': animation})
        else:
            if self._logger:
                self._logger.error(f"[Warudo] Failed to play animation: {animation}")
            return self._error_result(
                'Failed to play animation (WebSocket send failed)',
                metadata={'animation': animation},
                guidance='Check Warudo WebSocket connection'
            )
# Filename: BASE/tools/installed/unity_animation/tool.py
"""
Unity Animation Tool - Simplified Architecture
Single master class for controlling Unity VRM character animations and emotions
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
from BASE.handlers.base_tool import BaseTool

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False


class UnityAnimationTool(BaseTool):
    """
    Unity animation tool for controlling VRM character via WebSocket
    Manages connection to Unity and executes emotion/animation commands
    """
    
    # Default available emotions and animations
    DEFAULT_EMOTIONS = [
        'happy', 'sad', 'angry', 'surprised', 'neutral', 
        'relaxed', 'excited', 'confused'
    ]
    
    DEFAULT_ANIMATIONS = [
        'wave', 'nod', 'shake_head', 'bow', 'dance',
        'jump', 'sit', 'stand', 'idle'
    ]
    
    @property
    def name(self) -> str:
        return "unity"
    
    async def initialize(self) -> bool:
        """Initialize Unity WebSocket connection"""
        if not WEBSOCKETS_AVAILABLE:
            if self._logger:
                self._logger.warning(
                    "[Unity] websockets library not installed - pip install websockets"
                )
            return False
        
        # Get WebSocket configuration
        self.websocket_url = getattr(
            self._config, 
            'unity_websocket_url', 
            'ws://127.0.0.1:19192'
        )
        self.connection_timeout = getattr(
            self._config,
            'unity_connection_timeout',
            5.0
        )
        
        # Initialize state
        self.websocket = None
        self.is_connected = False
        
        # Available commands (updated from Unity on connect)
        self.emotions = self.DEFAULT_EMOTIONS.copy()
        self.animations = self.DEFAULT_ANIMATIONS.copy()
        
        # Avatar info
        self.avatar_name = "Unknown"
        self.vrm_connected = False
        
        # Attempt initial connection
        try:
            await self._connect()
            
            if self._logger:
                if self.is_connected:
                    self._logger.system(
                        f"[Unity] Connected: {self.avatar_name}, "
                        f"{len(self.emotions)} emotions, {len(self.animations)} animations"
                    )
                else:
                    self._logger.warning(
                        "[Unity] Not connected - will attempt reconnection on use"
                    )
        except Exception as e:
            if self._logger:
                self._logger.warning(f"[Unity] Initial connection failed: {e}")
        
        # Return True even if not connected - tool can retry later
        return True
    
    async def cleanup(self):
        """Cleanup Unity resources"""
        await self._disconnect()
        
        if self._logger:
            self._logger.system("[Unity] Cleaned up WebSocket connection")
    
    def is_available(self) -> bool:
        """Check if Unity WebSocket is connected"""
        return WEBSOCKETS_AVAILABLE and self.is_connected
    
    async def _connect(self) -> bool:
        """Connect to Unity WebSocket server"""
        if not WEBSOCKETS_AVAILABLE:
            return False
        
        if self.is_connected:
            return True
        
        try:
            if self._logger:
                self._logger.system(f"[Unity] Connecting to {self.websocket_url}")
            
            self.websocket = await asyncio.wait_for(
                websockets.connect(self.websocket_url),
                timeout=self.connection_timeout
            )
            
            self.is_connected = True
            
            # Perform health check to get avatar info
            await self._health_check()
            
            if self._logger:
                self._logger.success(f"[Unity] Connected: {self.avatar_name}")
            
            return True
        
        except asyncio.TimeoutError:
            if self._logger:
                self._logger.warning(f"[Unity] Connection timeout")
            self.is_connected = False
            return False
        
        except Exception as e:
            if self._logger:
                self._logger.warning(f"[Unity] Connection failed: {e}")
            self.is_connected = False
            return False
    
    async def _disconnect(self):
        """Disconnect from Unity WebSocket"""
        if self.websocket and self.is_connected:
            try:
                await self.websocket.close()
                if self._logger:
                    self._logger.system("[Unity] Disconnected")
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[Unity] Disconnect error: {e}")
            finally:
                self.websocket = None
                self.is_connected = False
    
    async def _health_check(self) -> Dict[str, Any]:
        """Perform health check and update avatar info"""
        if not self.is_connected or not self.websocket:
            return {}
        
        try:
            cmd = json.dumps({"type": "health"})
            await self.websocket.send(cmd)
            
            response = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=2.0
            )
            
            data = json.loads(response)
            
            if data.get("status") == "success":
                self.avatar_name = data.get("avatarName", "Unknown")
                self.vrm_connected = data.get("vrmConnected", False)
                
                # Update available emotions/animations from Unity
                if "emotions" in data:
                    self.emotions = data["emotions"]
                if "animations" in data:
                    self.animations = data["animations"]
            
            return data
        
        except Exception as e:
            if self._logger:
                self._logger.warning(f"[Unity] Health check failed: {e}")
            return {}
    
    async def _send_command(
        self, 
        command_type: str, 
        value: str, 
        intensity: float = 0.8
    ) -> Dict[str, Any]:
        """Send command to Unity"""
        # Ensure connection
        if not self.is_connected:
            await self._connect()
        
        if not self.is_connected:
            return self._error_result(
                'Not connected to Unity',
                guidance='Ensure Unity is running with WebSocket server'
            )
        
        try:
            cmd = json.dumps({
                "type": command_type,
                "value": value,
                "intensity": intensity
            })
            
            await self.websocket.send(cmd)
            
            response = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=2.0
            )
            
            data = json.loads(response)
            
            if data.get("status") == "success":
                if self._logger:
                    self._logger.success(f"[Unity] {command_type.title()}: {value}")
                
                return self._success_result(
                    f'{command_type.title()} set: {value}',
                    metadata={
                        'type': command_type,
                        'value': value,
                        'intensity': intensity,
                        'avatar': self.avatar_name
                    }
                )
            else:
                error_msg = data.get("message", "Unknown error")
                if self._logger:
                    self._logger.warning(f"[Unity] Command rejected: {error_msg}")
                
                return self._error_result(
                    f'Unity rejected {command_type}: {error_msg}',
                    metadata={'type': command_type, 'value': value, 'error': error_msg},
                    guidance='Check Unity console for errors'
                )
        
        except asyncio.TimeoutError:
            return self._error_result(
                f'{command_type.title()} command timeout',
                guidance='Unity may be unresponsive'
            )
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Unity] Send error: {e}")
            
            return self._error_result(
                f'Failed to send {command_type}: {str(e)}',
                metadata={'error': str(e)},
                guidance='Check WebSocket connection'
            )
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute Unity animation command
        
        Commands:
        - emotion: [emotion_name: str, intensity: Optional[float]]
        - animation: [animation_name: str, intensity: Optional[float]]
        
        Args:
            command: Command name ('emotion' or 'animation')
            args: Command arguments
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[Unity] Command: '{command}', args: {args}")
        
        # Validate command
        if not command:
            if not args:
                return self._error_result(
                    'No command or arguments provided',
                    guidance='Use: unity.emotion or unity.animation'
                )
            
            # Infer command from first argument
            value = str(args[0]).lower()
            if value in self.emotions:
                command = 'emotion'
            elif value in self.animations:
                command = 'animation'
            else:
                return self._error_result(
                    f'Unknown emotion/animation: {value}',
                    metadata={
                        'tried': value,
                        'available_emotions': self.emotions,
                        'available_animations': self.animations
                    },
                    guidance='Check available emotions/animations'
                )
        
        # Route to appropriate handler
        if command == 'emotion':
            return await self._handle_emotion(args)
        elif command == 'animation':
            return await self._handle_animation(args)
        elif command == 'connect':
            return await self._handle_connect()
        elif command == 'disconnect':
            return await self._handle_disconnect()
        elif command == 'health':
            return await self._handle_health()
        else:
            return self._error_result(
                f'Unknown command: {command}',
                guidance='Available commands: emotion, animation'
            )
    
    async def _handle_emotion(self, args: List[Any]) -> Dict[str, Any]:
        """
        Handle emotion command
        
        Args:
            args: [emotion_name: str, intensity: Optional[float]]
            
        Returns:
            Result dict
        """
        if not args:
            return self._error_result(
                'No emotion specified',
                metadata={'available': self.emotions},
                guidance=f'Available emotions: {", ".join(self.emotions)}'
            )
        
        emotion = str(args[0]).lower()
        
        # Parse intensity (optional)
        intensity = 0.8
        if len(args) > 1:
            try:
                intensity = float(args[1])
                if not (0.0 <= intensity <= 1.0):
                    return self._error_result(
                        f'Intensity must be between 0.0 and 1.0, got {intensity}',
                        guidance='Provide intensity in range 0.0 to 1.0'
                    )
            except (ValueError, TypeError):
                return self._error_result(
                    f'Invalid intensity value: {args[1]}',
                    guidance='Intensity must be a number between 0.0 and 1.0'
                )
        
        # Validate emotion
        if emotion not in self.emotions:
            return self._error_result(
                f'Unknown emotion: {emotion}',
                metadata={'available': self.emotions},
                guidance=f'Available emotions: {", ".join(self.emotions)}'
            )
        
        return await self._send_command('emotion', emotion, intensity)
    
    async def _handle_animation(self, args: List[Any]) -> Dict[str, Any]:
        """
        Handle animation command
        
        Args:
            args: [animation_name: str, intensity: Optional[float]]
            
        Returns:
            Result dict
        """
        if not args:
            return self._error_result(
                'No animation specified',
                metadata={'available': self.animations},
                guidance=f'Available animations: {", ".join(self.animations)}'
            )
        
        animation = str(args[0]).lower()
        
        # Parse intensity (optional)
        intensity = 0.8
        if len(args) > 1:
            try:
                intensity = float(args[1])
                if not (0.0 <= intensity <= 1.0):
                    return self._error_result(
                        f'Intensity must be between 0.0 and 1.0, got {intensity}',
                        guidance='Provide intensity in range 0.0 to 1.0'
                    )
            except (ValueError, TypeError):
                return self._error_result(
                    f'Invalid intensity value: {args[1]}',
                    guidance='Intensity must be a number between 0.0 and 1.0'
                )
        
        # Validate animation
        if animation not in self.animations:
            return self._error_result(
                f'Unknown animation: {animation}',
                metadata={'available': self.animations},
                guidance=f'Available animations: {", ".join(self.animations)}'
            )
        
        return await self._send_command('animation', animation, intensity)
    
    async def _handle_connect(self) -> Dict[str, Any]:
        """Handle connect command"""
        success = await self._connect()
        
        if success:
            return self._success_result(
                f'Connected to Unity: {self.avatar_name}',
                metadata={
                    'avatar': self.avatar_name,
                    'vrm_connected': self.vrm_connected
                }
            )
        else:
            return self._error_result(
                'Failed to connect to Unity',
                guidance='Ensure Unity is running with WebSocket server'
            )
    
    async def _handle_disconnect(self) -> Dict[str, Any]:
        """Handle disconnect command"""
        await self._disconnect()
        return self._success_result('Disconnected from Unity')
    
    async def _handle_health(self) -> Dict[str, Any]:
        """Handle health check command"""
        data = await self._health_check()
        
        if data.get("status") == "success":
            return self._success_result(
                f'Unity healthy: {self.avatar_name}',
                metadata={
                    'avatar': self.avatar_name,
                    'vrm_connected': self.vrm_connected,
                    'emotions': self.emotions,
                    'animations': self.animations
                }
            )
        else:
            return self._error_result(
                'Health check failed',
                guidance='Check Unity connection'
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get Unity system status (for debugging/monitoring)"""
        return {
            'available': self.is_available(),
            'websockets_available': WEBSOCKETS_AVAILABLE,
            'connected': self.is_connected,
            'websocket_url': self.websocket_url,
            'avatar_name': self.avatar_name,
            'vrm_connected': self.vrm_connected,
            'emotions': self.emotions,
            'animations': self.animations
        }
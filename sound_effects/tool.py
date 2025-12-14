# Filename: BASE/tools/installed/sound_effects/tool.py
"""
Sound Effects Tool - Simplified Architecture
Single master class with start() and end() lifecycle
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from BASE.handlers.base_tool import BaseTool

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class SoundEffectsTool(BaseTool):
    """
    Sound effects playback tool
    Plays .mp3 sound effects from library to enhance interactions
    """
    
    @property
    def name(self) -> str:
        return "sound"
    
    async def initialize(self) -> bool:
        """
        Initialize sound system
        
        Returns:
            True if initialization successful (always returns True for graceful degradation)
        """
        # Get sound directory from config with fallback
        default_sound_dir = Path(__file__).parent / 'effects'
        self.sound_dir = Path(getattr(
            self._config, 
            'sound_effects_dir',
            str(default_sound_dir)
        ))
        
        # Track last played for throttling
        self._last_played = {}
        
        # Initialize pygame mixer
        self._initialized = False
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                self._initialized = True
                if self._logger:
                    self._logger.system("[Sound] pygame mixer initialized")
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[Sound] Failed to initialize pygame: {e}")
        else:
            if self._logger:
                self._logger.warning("[Sound] pygame not available - install with: pip install pygame")
        
        # Scan available sounds
        self.available_sounds = self._scan_sounds()
        
        # Log status
        if self._logger:
            if not self.is_available():
                status = self.get_status()
                reasons = []
                if not status.get('pygame_available'):
                    reasons.append("pygame not installed")
                if not status.get('initialized'):
                    reasons.append("mixer initialization failed")
                if status.get('sound_count', 0) == 0:
                    reasons.append("no sound files found")
                
                reason_str = ", ".join(reasons) if reasons else "unknown reason"
                self._logger.warning(f"[Sound] Not available: {reason_str}")
            else:
                sound_count = len(self.available_sounds)
                sound_names = ', '.join(sorted(self.available_sounds.keys())[:5])
                more = f" (+{sound_count - 5} more)" if sound_count > 5 else ""
                self._logger.system(
                    f"[Sound] System ready: {sound_count} effects available: {sound_names}{more}"
                )
        
        # Always return True - tool registration should succeed
        # Execution will fail gracefully if sound is unavailable
        return True
    
    async def cleanup(self):
        """Cleanup sound resources"""
        if self._initialized:
            try:
                pygame.mixer.stop()
                pygame.mixer.quit()
                if self._logger:
                    self._logger.system("[Sound] Cleanup complete")
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[Sound] Cleanup error: {e}")
        
        self._last_played.clear()
        self.available_sounds.clear()
    
    def is_available(self) -> bool:
        """
        Check if sound system is ready
        
        Returns:
            True if pygame is available, initialized, and sounds exist
        """
        return PYGAME_AVAILABLE and self._initialized and len(self.available_sounds) > 0
    

    def get_status(self) -> Dict[str, Any]:
        """
        Get sound system status
        
        Returns:
            Status dictionary with availability info
        """
        return {
            'available': self.is_available(),
            'pygame_available': PYGAME_AVAILABLE,
            'initialized': self._initialized,
            'sound_count': len(self.available_sounds),
            'sound_dir': str(self.sound_dir),
            'sounds': list(self.available_sounds.keys()) if self.available_sounds else []
        }
    
    def get_available_sounds(self) -> Dict[str, Path]:
        """
        Get available sounds for GUI
        
        Returns:
            Dict mapping sound names to file paths
        """
        return self.available_sounds.copy()
    
    def _scan_sounds(self) -> Dict[str, Path]:
        """
        Scan sound directory for .mp3 files
        
        Returns:
            Dict mapping sound names (lowercase) to file paths
        """
        sounds = {}
        
        if not self.sound_dir.exists():
            if self._logger:
                self._logger.warning(f"[Sound] Directory not found: {self.sound_dir}")
            return sounds
        
        for file in self.sound_dir.glob("*.mp3"):
            sound_name = file.stem.lower()
            sounds[sound_name] = file
            
            if self._logger:
                self._logger.system(f"[Sound] Registered: {sound_name} ({file.name})")
        
        return sounds
    
    def _get_volume(self, volume_override: Optional[float] = None) -> float:
        """
        Calculate final volume from global setting and override
        
        Args:
            volume_override: Optional volume multiplier (0.0 to 1.0)
            
        Returns:
            Final volume value (0.0 to 1.0)
        """
        # Get global volume from controls
        global_volume = getattr(self._controls, 'SOUND_EFFECT_VOLUME', 1.0)
        
        # Apply override if provided
        if volume_override is not None:
            try:
                volume_override = float(volume_override)
                final_volume = global_volume * volume_override
            except (ValueError, TypeError):
                if self._logger:
                    self._logger.warning(f"[Sound] Invalid volume override: {volume_override}, using global")
                final_volume = global_volume
        else:
            final_volume = global_volume
        
        # Clamp to valid range
        return max(0.0, min(1.0, final_volume))
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute sound command
        
        Commands:
        - play: Play a sound effect with optional volume
        - list: List available sounds
        - stop: Stop all sounds
        
        Args:
            command: Command name ('play', 'list', 'stop')
            args: Command arguments as defined in information.json
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[Sound] Command: '{command}', args: {args}")
        
        # Check availability first
        if not self.is_available():
            status = self.get_status()
            reasons = []
            if not status['pygame_available']:
                reasons.append("pygame not installed")
            if not status['initialized']:
                reasons.append("mixer failed to initialize")
            if status['sound_count'] == 0:
                reasons.append("no sound files found")
            
            reason_str = ", ".join(reasons) if reasons else "unknown reason"
            
            return self._error_result(
                f'Sound system unavailable: {reason_str}',
                metadata=status,
                guidance='Check pygame installation and sound directory'
            )
        
        # Validate command
        if not command:
            return self._error_result(
                'No command provided',
                guidance='Use: sound.play, sound.list, or sound.stop'
            )
        
        try:
            # Route to appropriate handler
            if command == 'play':
                return await self._handle_play_command(args)
            elif command == 'list':
                return await self._handle_list_command(args)
            elif command == 'stop':
                return await self._handle_stop_command(args)
            else:
                return self._error_result(
                    f'Unknown command: {command}',
                    guidance='Available commands: play, list, stop'
                )
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Sound] Command execution error: {e}")
            import traceback
            traceback.print_exc()
            
            return self._error_result(
                f'Command execution failed: {str(e)}',
                metadata={'error': str(e)},
                guidance='Check logs for details'
            )
    
    async def _handle_play_command(self, args: List[Any]) -> Dict[str, Any]:
        """
        Handle play command: sound.play with [sound_name: str, volume: Optional[float]]
        
        Args:
            args: [sound_name] or [sound_name, volume]
            
        Returns:
            Result dict
        """
        # Validate arguments
        if not args:
            available_preview = ', '.join(sorted(self.available_sounds.keys())[:5])
            return self._error_result(
                'No sound name provided',
                metadata={'available_sounds': list(self.available_sounds.keys())},
                guidance=f'Provide sound name. Available: {available_preview}...'
            )
        
        # Extract arguments
        sound_name = str(args[0])
        volume_override = None
        
        if len(args) > 1:
            try:
                volume_override = float(args[1])
                # Validate range
                if not (0.0 <= volume_override <= 1.0):
                    return self._error_result(
                        f'Volume must be between 0.0 and 1.0, got {volume_override}',
                        metadata={'invalid_volume': volume_override},
                        guidance='Provide volume in range 0.0 to 1.0'
                    )
            except (ValueError, TypeError) as e:
                return self._error_result(
                    f'Invalid volume value: {args[1]}',
                    metadata={'error': str(e)},
                    guidance='Volume must be a number between 0.0 and 1.0'
                )
        
        sound_name_lower = sound_name.lower()
        
        # Validate sound exists
        if sound_name_lower not in self.available_sounds:
            available_preview = ', '.join(sorted(self.available_sounds.keys())[:5])
            more = f" (+{len(self.available_sounds) - 5} more)" if len(self.available_sounds) > 5 else ""
            
            return self._error_result(
                f'Sound "{sound_name}" not found',
                metadata={
                    'requested': sound_name,
                    'available_count': len(self.available_sounds),
                    'available_sounds': list(self.available_sounds.keys())
                },
                guidance=f'Available sounds: {available_preview}{more}. Use sound.list for full list'
            )
        
        try:
            # Get sound file
            sound_path = self.available_sounds[sound_name_lower]
            sound = pygame.mixer.Sound(str(sound_path))
            
            # Set volume
            final_volume = self._get_volume(volume_override)
            sound.set_volume(final_volume)
            
            # Play sound (non-blocking)
            sound.play()
            
            # Track for throttling
            self._last_played[sound_name_lower] = time.time()
            
            if self._logger:
                volume_pct = int(final_volume * 100)
                self._logger.success(
                    f"[Sound] ♪ Playing: {sound_name} (volume: {volume_pct}%)"
                )
            
            return self._success_result(
                f'♪ Playing sound: {sound_name}',
                metadata={
                    'sound': sound_name,
                    'volume': final_volume,
                    'volume_percent': int(final_volume * 100),
                    'file': sound_path.name
                }
            )
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Sound] Playback error for '{sound_name}': {e}")
            
            return self._error_result(
                f'Failed to play sound: {sound_name}',
                metadata={'error': str(e), 'sound': sound_name},
                guidance='Sound playback error occurred'
            )
    
    async def _handle_list_command(self, args: List[Any]) -> Dict[str, Any]:
        """
        Handle list command: sound.list with no args
        Lists all available sounds
        
        Args:
            args: Should be empty per information.json
            
        Returns:
            Result dict with sound list
        """
        if not self.available_sounds:
            return self._error_result(
                'No sound effects found',
                metadata={
                    'count': 0,
                    'sound_dir': str(self.sound_dir)
                },
                guidance=f'Check sound directory: {self.sound_dir}'
            )
        
        sounds_list = sorted(self.available_sounds.keys())
        sounds_str = ', '.join(sounds_list)
        
        if self._logger:
            self._logger.system(f"[Sound] Listed {len(sounds_list)} available sounds")
        
        return self._success_result(
            f'Available sounds ({len(sounds_list)}): {sounds_str}',
            metadata={
                'count': len(sounds_list),
                'sounds': sounds_list,
                'sound_dir': str(self.sound_dir)
            }
        )
    
    async def _handle_stop_command(self, args: List[Any]) -> Dict[str, Any]:
        """
        Handle stop command: sound.stop with no args
        Stops all playing sounds
        
        Args:
            args: Should be empty per information.json
            
        Returns:
            Result dict
        """
        try:
            pygame.mixer.stop()
            
            if self._logger:
                self._logger.system("[Sound] Stopped all sounds")
            
            return self._success_result(
                'All sounds stopped',
                metadata={}
            )
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Sound] Stop error: {e}")
            
            return self._error_result(
                f'Failed to stop sounds: {str(e)}',
                metadata={'error': str(e)},
                guidance='Error stopping sounds'
            )
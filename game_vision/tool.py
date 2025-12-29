# Filename: BASE/tools/installed/game_vision/tool.py
"""
Game Vision Tool - Continuous Screen Monitoring
Captures and analyzes gameplay screenshots every 10 seconds
Provides real-time game state awareness to the agent
"""
import asyncio
import base64
import time
from typing import List, Dict, Any, Optional
from io import BytesIO
from BASE.handlers.base_tool import BaseTool

try:
    import pyautogui
    import screeninfo
    from PIL import Image
    SCREENSHOT_AVAILABLE = True
except ImportError:
    SCREENSHOT_AVAILABLE = False


class GameVisionTool(BaseTool):
    """
    Continuous game screen monitoring tool
    Captures screenshots every 10 seconds and analyzes game state
    Proactively injects game context into thought buffer
    """
    
    @property
    def name(self) -> str:
        return "game_vision"
    
    def has_context_loop(self) -> bool:
        """Enable background context loop for continuous monitoring"""
        return True
    
    async def initialize(self) -> bool:
        """
        Initialize game vision system
        
        Returns:
            True if initialization successful (always returns True for graceful degradation)
        """
        # Get vision model configuration
        self.vision_model = getattr(self._config, 'vision_model', 'llava:latest')
        self.ollama_endpoint = getattr(self._config, 'ollama_endpoint', 'http://localhost:11434')
        
        # Monitoring settings
        self.capture_interval = 10.0  # 10 seconds between captures
        self.last_capture_time = 0.0
        
        # Screenshot tracking
        self.screenshot_count = 0
        self.last_analysis = None
        
        # Check screenshot availability
        if not SCREENSHOT_AVAILABLE:
            if self._logger:
                self._logger.warning(
                    "[Game Vision] Screenshot libraries not available - "
                    "install with: pip install pyautogui screeninfo pillow"
                )
            # Still return True for graceful degradation
            return True
        
        # Get monitor info
        try:
            monitors = screeninfo.get_monitors()
            monitor_count = len(monitors)
            
            if self._logger:
                primary = next((m for m in monitors if m.is_primary), monitors[0] if monitors else None)
                if primary:
                    self._logger.system(
                        f"[Game Vision] System ready: {monitor_count} monitor{'s' if monitor_count != 1 else ''}, "
                        f"primary: {primary.width}x{primary.height}, "
                        f"model: {self.vision_model}, "
                        f"interval: {self.capture_interval}s"
                    )
                else:
                    self._logger.warning("[Game Vision] No monitors detected")
        except Exception as e:
            if self._logger:
                self._logger.warning(f"[Game Vision] Could not detect monitors: {e}")
        
        # Always return True - tool registration should succeed
        return True
    
    async def cleanup(self):
        """Cleanup game vision resources"""
        self.last_analysis = None
        self.screenshot_count = 0
        
        if self._logger:
            self._logger.system("[Game Vision] Cleanup complete")
    
    def is_available(self) -> bool:
        """
        Check if game vision system is ready
        
        Returns:
            True if screenshot libraries are available
        """
        return SCREENSHOT_AVAILABLE
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get game vision system status
        
        Returns:
            Status dictionary with availability info
        """
        status = {
            'available': SCREENSHOT_AVAILABLE,
            'vision_model': self.vision_model,
            'ollama_endpoint': self.ollama_endpoint,
            'capture_interval': self.capture_interval,
            'screenshot_count': self.screenshot_count,
            'last_capture': self.last_capture_time,
            'monitors': 0
        }
        
        if SCREENSHOT_AVAILABLE:
            try:
                monitors = screeninfo.get_monitors()
                status['monitors'] = len(monitors)
                
                if monitors:
                    primary = next((m for m in monitors if m.is_primary), monitors[0])
                    status['primary_monitor'] = {
                        'width': primary.width,
                        'height': primary.height,
                        'is_primary': primary.is_primary
                    }
            except Exception:
                pass
        
        return status
    
    async def context_loop(self, thought_buffer):
        """
        Background loop for continuous game monitoring
        Captures and analyzes screen every 10 seconds
        
        Args:
            thought_buffer: ThoughtBuffer instance for injecting game state
        """
        if self._logger:
            self._logger.system(
                f"[Game Vision] Context loop started - "
                f"capturing every {self.capture_interval}s"
            )
        
        while self._running:
            try:
                current_time = time.time()
                
                # Check if it's time for next capture
                if current_time - self.last_capture_time >= self.capture_interval:
                    if not self.is_available():
                        if self._logger:
                            self._logger.warning(
                                "[Game Vision] Screenshot libraries not available"
                            )
                        await asyncio.sleep(self.capture_interval)
                        continue
                    
                    # Capture screenshot
                    screenshot_b64 = self._capture_screenshot()
                    
                    if screenshot_b64:
                        # Analyze with vision model
                        analysis = await self._analyze_game_screen(screenshot_b64)
                        
                        if analysis:
                            self.last_analysis = analysis
                            self.screenshot_count += 1
                            self.last_capture_time = current_time
                            
                            # Inject game state into thought buffer (HIGH priority)
                            context = self._format_game_context(analysis)
                            
                            thought_buffer.add_processed_thought(
                                content=context,
                                source='game_vision',
                                priority_override="HIGH"
                            )
                            
                            if self._logger:
                                self._logger.tool(
                                    f"[Game Vision] Injected game state "
                                    f"(capture #{self.screenshot_count}, "
                                    f"{len(analysis)} chars)"
                                )
                        else:
                            if self._logger:
                                self._logger.warning(
                                    "[Game Vision] Analysis failed, will retry next interval"
                                )
                    else:
                        if self._logger:
                            self._logger.warning(
                                "[Game Vision] Screenshot capture failed"
                            )
                    
                    # Update last capture time even if failed to maintain interval
                    self.last_capture_time = current_time
                
                # Sleep for a short duration and check again
                await asyncio.sleep(1.0)
                
            except asyncio.CancelledError:
                # Normal cancellation when tool stops
                break
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[Game Vision] Context loop error: {e}")
                # Continue running despite errors
                await asyncio.sleep(self.capture_interval)
        
        if self._logger:
            self._logger.system(
                f"[Game Vision] Context loop stopped "
                f"(total captures: {self.screenshot_count})"
            )
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute game vision command
        
        Commands:
        - get_status: Get current monitoring status
        - capture_now: Force immediate capture and analysis
        
        Args:
            command: Command name
            args: Command arguments
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[Game Vision] Command: '{command}', args: {args}")
        
        # Check availability
        if not self.is_available():
            return self._error_result(
                'Screenshot libraries not available',
                guidance='Install: pip install pyautogui screeninfo pillow'
            )
        
        # Validate command
        if not command:
            return self._error_result(
                'No command provided',
                guidance='Available commands: get_status, capture_now'
            )
        
        try:
            if command == 'get_status':
                return await self._handle_status_command()
            elif command == 'capture_now':
                return await self._handle_capture_now_command()
            else:
                return self._error_result(
                    f'Unknown command: {command}',
                    guidance='Available commands: get_status, capture_now'
                )
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Game Vision] Command execution error: {e}")
            import traceback
            traceback.print_exc()
            
            return self._error_result(
                f'Command execution failed: {str(e)}',
                metadata={'error': str(e)},
                guidance='Check logs for details'
            )
    
    async def _handle_status_command(self) -> Dict[str, Any]:
        """
        Handle get_status command
        Returns current monitoring status
        """
        status = self.get_status()
        
        status_text = (
            f"Game Vision Monitoring Status:\n"
            f"- Screenshots captured: {self.screenshot_count}\n"
            f"- Capture interval: {self.capture_interval}s\n"
            f"- Vision model: {self.vision_model}\n"
            f"- Available: {status['available']}\n"
        )
        
        if self.last_capture_time > 0:
            time_since_last = time.time() - self.last_capture_time
            status_text += f"- Last capture: {time_since_last:.1f}s ago\n"
        
        return self._success_result(
            status_text,
            metadata=status
        )
    
    async def _handle_capture_now_command(self) -> Dict[str, Any]:
        """
        Handle capture_now command
        Force immediate screenshot capture and analysis
        """
        # Capture screenshot
        screenshot_b64 = self._capture_screenshot()
        
        if not screenshot_b64:
            return self._error_result(
                'Failed to capture screenshot',
                guidance='Check screenshot library installation and monitor availability'
            )
        
        # Analyze with vision model
        analysis = await self._analyze_game_screen(screenshot_b64)
        
        if not analysis:
            return self._error_result(
                'Failed to analyze screenshot',
                guidance='Check Ollama connection and vision model availability'
            )
        
        self.last_analysis = analysis
        self.screenshot_count += 1
        self.last_capture_time = time.time()
        
        return self._success_result(
            analysis,
            metadata={
                'capture_number': self.screenshot_count,
                'analysis_length': len(analysis)
            }
        )
    
    def _capture_screenshot(self) -> Optional[str]:
        """
        Capture screenshot of primary monitor and return as base64
        
        Returns:
            Base64 encoded PNG image or None if capture fails
        """
        if not SCREENSHOT_AVAILABLE:
            if self._logger:
                self._logger.error("[Game Vision] Screenshot libraries not available")
            return None
        
        try:
            # Get primary monitor
            monitors = screeninfo.get_monitors()
            
            if not monitors:
                if self._logger:
                    self._logger.error("[Game Vision] No monitors detected")
                return None
            
            # Select primary monitor
            monitor = next((m for m in monitors if m.is_primary), monitors[0])
            
            # Capture screenshot
            screenshot = pyautogui.screenshot(region=(
                monitor.x, monitor.y, monitor.width, monitor.height
            ))
            
            # Convert to base64
            buf = BytesIO()
            screenshot.save(buf, format="PNG")
            base64_image = base64.b64encode(buf.getvalue()).decode('utf-8')
            
            if self._logger:
                self._logger.system(
                    f"[Game Vision] Captured screenshot: {monitor.width}x{monitor.height} "
                    f"(primary monitor)"
                )
            
            return base64_image
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Game Vision] Screenshot capture failed: {e}")
            return None
    
    async def _analyze_game_screen(self, screenshot_b64: str) -> Optional[str]:
        """
        Analyze game screenshot using vision model
        
        Args:
            screenshot_b64: Base64 encoded screenshot
            
        Returns:
            Analysis text or None if analysis fails
        """
        # Prepare game-specific analysis prompt
        prompt = (
            "You are analyzing a gaming screenshot for a gaming assistant AI. "
            "Provide a detailed description of the game state focusing on:\n"
            "- What game is being played (if identifiable)\n"
            "- Player status: health, resources, inventory, stats\n"
            "- Current objectives or mission\n"
            "- Enemies, threats, or opponents visible\n"
            "- Important UI elements: minimap, notifications, alerts\n"
            "- Environmental context: location, time, conditions\n"
            "- Any critical information the player should be aware of\n\n"
            "Be concise but thorough. Focus on actionable information.\n"
            "Do not offer advice or assistance, ask questions, or make assumptions beyond what is visible in the screenshot.\n"
            "Simply describe the game state based on the visual information provided."
        )
        
        try:
            import requests
            
            if self._logger:
                self._logger.tool(
                    f"[Game Vision] Analyzing with vision model: {self.vision_model}"
                )
            
            # Call Ollama vision model
            response = requests.post(
                f"{self.ollama_endpoint}/api/generate",
                json={
                    "model": self.vision_model,
                    "prompt": prompt,
                    "images": [screenshot_b64],
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get('response', 'No response from vision model')
                
                if self._logger:
                    self._logger.success(
                        f"[Game Vision] Analysis complete ({len(analysis)} chars)"
                    )
                
                return analysis
            
            else:
                error_msg = f"Vision model request failed: HTTP {response.status_code}"
                
                # Try to get error details
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail.get('error', 'Unknown error')}"
                except:
                    pass
                
                if self._logger:
                    self._logger.error(f"[Game Vision] {error_msg}")
                
                return None
                
        except requests.exceptions.Timeout:
            if self._logger:
                self._logger.error("[Game Vision] Vision model request timed out (30s)")
            return None
        
        except requests.exceptions.ConnectionError:
            if self._logger:
                self._logger.error(
                    f"[Game Vision] Cannot connect to Ollama at {self.ollama_endpoint}"
                )
            return None
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Game Vision] Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _format_game_context(self, analysis: str) -> str:
        """
        Format game analysis into context for thought buffer
        
        Args:
            analysis: Raw analysis text from vision model
            
        Returns:
            Formatted context string
        """
        timestamp = time.strftime("%H:%M:%S")
        
        context = (
            f"## [Game Vision] SCREEN ANALYSIS ({timestamp})\n"
            f"**Capture:** #{self.screenshot_count}\n\n"
            f"{analysis}\n"
        )
        
        return context
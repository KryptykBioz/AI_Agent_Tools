# Filename: BASE/tools/installed/screenshot_vision/tool.py
"""
Screenshot Vision Tool - Simplified Architecture
Single master class with start() and end() lifecycle
"""
import asyncio
import base64
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


class ScreenshotVisionTool(BaseTool):
    """
    Screenshot capture and vision analysis tool
    Captures screens and analyzes them using vision models
    """
    
    @property
    def name(self) -> str:
        return "vision"
    
    async def initialize(self) -> bool:
        """
        Initialize vision system
        
        Returns:
            True if initialization successful (always returns True for graceful degradation)
        """
        # Get vision model configuration
        self.vision_model = getattr(self._config, 'vision_model', 'llava:latest')
        self.ollama_endpoint = getattr(self._config, 'ollama_endpoint', 'http://localhost:11434')
        
        # Check screenshot availability
        if not SCREENSHOT_AVAILABLE:
            if self._logger:
                self._logger.warning(
                    "[Vision] Screenshot libraries not available - "
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
                        f"[Vision] System ready: {monitor_count} monitor{'s' if monitor_count != 1 else ''}, "
                        f"primary: {primary.width}x{primary.height}, model: {self.vision_model}"
                    )
                else:
                    self._logger.warning("[Vision] No monitors detected")
        except Exception as e:
            if self._logger:
                self._logger.warning(f"[Vision] Could not detect monitors: {e}")
        
        # Always return True - tool registration should succeed
        return True
    
    async def cleanup(self):
        """Cleanup vision resources"""
        if self._logger:
            self._logger.system("[Vision] Cleanup complete")
    
    def is_available(self) -> bool:
        """
        Check if vision system is ready
        
        Returns:
            True if screenshot libraries are available
        """
        return SCREENSHOT_AVAILABLE
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get vision system status
        
        Returns:
            Status dictionary with availability info
        """
        status = {
            'available': SCREENSHOT_AVAILABLE,
            'vision_model': self.vision_model,
            'ollama_endpoint': self.ollama_endpoint,
            'monitors': 0
        }
        
        if SCREENSHOT_AVAILABLE:
            try:
                monitors = screeninfo.get_monitors()
                status['monitors'] = len(monitors)
                
                if monitors:
                    status['monitor_info'] = [
                        {
                            'index': i,
                            'width': m.width,
                            'height': m.height,
                            'is_primary': m.is_primary
                        }
                        for i, m in enumerate(monitors)
                    ]
            except Exception:
                pass
        
        return status
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute vision command
        
        Commands:
        - screenshot: Capture and analyze screenshot (no args)
        - analyze: Analyze with specific question [query: str, monitor: Optional[int]]
        
        Args:
            command: Command name ('screenshot' or 'analyze')
            args: Command arguments as defined in information.json
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[Vision] Command: '{command}', args: {args}")
        
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
                guidance='Use: vision.screenshot or vision.analyze'
            )
        
        try:
            # Route to appropriate handler
            if command == 'screenshot':
                return await self._handle_screenshot_command(args)
            elif command == 'analyze':
                return await self._handle_analyze_command(args)
            else:
                return self._error_result(
                    f'Unknown command: {command}',
                    guidance='Available commands: screenshot, analyze'
                )
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Vision] Command execution error: {e}")
            import traceback
            traceback.print_exc()
            
            return self._error_result(
                f'Command execution failed: {str(e)}',
                metadata={'error': str(e)},
                guidance='Check logs for details'
            )
    
    async def _handle_screenshot_command(self, args: List[Any]) -> Dict[str, Any]:
        """
        Handle screenshot command: vision.screenshot with no args
        Captures screenshot of primary monitor and analyzes with general description
        
        Args:
            args: Should be empty list per information.json
            
        Returns:
            Result dict with analysis
        """
        # Screenshot command takes no arguments - always use primary monitor
        monitor_index = -1  # Primary monitor
        
        # Capture screenshot
        screenshot_b64 = self._capture_screenshot(monitor_index)
        
        if not screenshot_b64:
            return self._error_result(
                'Failed to capture screenshot',
                guidance='Check screenshot library installation and monitor availability'
            )
        
        # Analyze with general description (no specific query)
        return await self._analyze_screenshot_with_vision(screenshot_b64, query=None)
    
    async def _handle_analyze_command(self, args: List[Any]) -> Dict[str, Any]:
        """
        Handle analyze command: vision.analyze with [query: str, monitor: Optional[int]]
        Captures screenshot and analyzes with specific query
        
        Args:
            args: [query, optional_monitor_index]
            
        Returns:
            Result dict with analysis
        """
        # Validate arguments
        if not args:
            return self._error_result(
                'analyze command requires at least a query argument',
                guidance='Format: {"tool": "vision.analyze", "args": ["your question"]}'
            )
        
        # Extract arguments
        query = str(args[0]) if args else None
        monitor_index = int(args[1]) if len(args) > 1 else -1  # Default to primary
        
        if not query:
            return self._error_result(
                'Query cannot be empty',
                guidance='Provide a specific question about the screenshot'
            )
        
        # Capture screenshot
        screenshot_b64 = self._capture_screenshot(monitor_index)
        
        if not screenshot_b64:
            return self._error_result(
                'Failed to capture screenshot',
                guidance='Check screenshot library and monitor availability'
            )
        
        # Analyze with specific query
        return await self._analyze_screenshot_with_vision(screenshot_b64, query=query)
    
    def _capture_screenshot(self, monitor_index: int = -1) -> Optional[str]:
        """
        Capture screenshot and return as base64
        
        Args:
            monitor_index: Monitor to capture (-1 for primary, 0+ for specific monitor)
            
        Returns:
            Base64 encoded PNG image or None if capture fails
        """
        if not SCREENSHOT_AVAILABLE:
            if self._logger:
                self._logger.error("[Vision] Screenshot libraries not available")
            return None
        
        try:
            # Get monitors
            monitors = screeninfo.get_monitors()
            
            if not monitors:
                if self._logger:
                    self._logger.error("[Vision] No monitors detected")
                return None
            
            # Select monitor
            if monitor_index == -1:
                # Primary monitor
                monitor = next((m for m in monitors if m.is_primary), monitors[0])
            elif 0 <= monitor_index < len(monitors):
                monitor = monitors[monitor_index]
            else:
                if self._logger:
                    self._logger.warning(
                        f"[Vision] Invalid monitor index {monitor_index}, using primary"
                    )
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
                    f"[Vision] Captured screenshot: {monitor.width}x{monitor.height} "
                    f"(monitor: {'primary' if monitor.is_primary else monitor_index})"
                )
            
            return base64_image
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Vision] Screenshot capture failed: {e}")
            return None
    
    async def _analyze_screenshot_with_vision(
        self, 
        screenshot_b64: str, 
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze screenshot using vision model
        
        Args:
            screenshot_b64: Base64 encoded screenshot
            query: Optional specific question
            
        Returns:
            Result dict with analysis
        """
        # Prepare prompt
        if query:
            prompt = f"Analyze this screenshot and answer: {query}"
        else:
            prompt = (
                "Describe what you see in this screenshot in detail. "
                "Include information about applications, UI elements, text content, "
                "and overall context."
            )
        
        try:
            import requests
            
            if self._logger:
                self._logger.tool(
                    f"[Vision] Calling vision model: {self.vision_model} "
                    f"with query: {query if query else 'general description'}"
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
                        f"[Vision] Analysis complete ({len(analysis)} chars)"
                    )
                
                return self._success_result(
                    analysis,
                    metadata={
                        'model': self.vision_model,
                        'query': query or 'general description',
                        'image_size_bytes': len(screenshot_b64),
                        'analysis_length': len(analysis)
                    }
                )
            
            else:
                error_msg = f"Vision model request failed: HTTP {response.status_code}"
                
                # Try to get error details
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail.get('error', 'Unknown error')}"
                except:
                    pass
                
                if self._logger:
                    self._logger.error(f"[Vision] {error_msg}")
                
                return self._error_result(
                    error_msg,
                    metadata={'status_code': response.status_code},
                    guidance='Check if Ollama is running and vision model is available'
                )
                
        except requests.exceptions.Timeout:
            error_msg = 'Vision model request timed out (30s)'
            if self._logger:
                self._logger.error(f"[Vision] {error_msg}")
            
            return self._error_result(
                error_msg,
                guidance='Vision model may be slow or unresponsive'
            )
        
        except requests.exceptions.ConnectionError:
            error_msg = f'Cannot connect to Ollama at {self.ollama_endpoint}'
            if self._logger:
                self._logger.error(f"[Vision] {error_msg}")
            
            return self._error_result(
                error_msg,
                guidance='Ensure Ollama is running and accessible'
            )
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Vision] Analysis error: {e}")
            import traceback
            traceback.print_exc()
            
            return self._error_result(
                f'Vision analysis failed: {str(e)}',
                metadata={'error': str(e)},
                guidance='Check Ollama connection and vision model availability'
            )
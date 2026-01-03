# Filename: BASE/tools/installed/opencv_vision/tool.py
"""
OpenCV Vision Tool - High-Performance Continuous Monitoring
============================================================
Uses MSS + OpenCV for fast, non-blocking screen capture
Integrates with thought buffer via context_loop
Optimized for VTuber real-time awareness
"""
import asyncio
import base64
import time
from typing import List, Dict, Any, Optional
from io import BytesIO
from collections import deque
from threading import Thread, Lock
from queue import Queue, Full

from BASE.handlers.base_tool import BaseTool

try:
    import cv2
    import numpy as np
    import mss
    from PIL import Image
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


class OpenCVVisionTool(BaseTool):
    """
    High-performance continuous vision monitoring
    
    Features:
    - Fast MSS capture (10-50ms vs 200ms PyAutoGUI)
    - Non-blocking threaded capture
    - Configurable FPS (5-30+)
    - Change detection triggers
    - Continuous thought buffer injection
    """
    
    @property
    def name(self) -> str:
        return "opencv_vision"
    
    async def initialize(self) -> bool:
        """Initialize OpenCV vision system"""
        # Configuration
        self.vision_model = getattr(self._config, 'vision_model', 'llava:latest')
        self.ollama_endpoint = getattr(self._config, 'ollama_endpoint', 'http://localhost:11434')
        self.target_fps = getattr(self._config, 'opencv_vision_fps', 10)
        self.capture_width = getattr(self._config, 'opencv_vision_width', 1024)
        self.capture_height = getattr(self._config, 'opencv_vision_height', 768)
        self.analysis_interval = getattr(self._config, 'opencv_vision_interval', 5.0)
        self.change_threshold = getattr(self._config, 'opencv_vision_change_threshold', 50000)
        
        # Check availability
        if not OPENCV_AVAILABLE:
            if self._logger:
                self._logger.warning(
                    "[OpenCV Vision] Libraries not available - "
                    "install with: pip install mss opencv-python numpy"
                )
            return True  # Graceful degradation
        
        # Capture state
        self.monitor_index = 1  # Store index instead of monitor dict
        self.monitor_info = None  # Store for status reporting
        self.capture_thread = None
        self.capture_running = False
        
        # Frame buffer
        self.frame_buffer = Queue(maxsize=5)
        self.latest_frame = None
        self.frame_lock = Lock()
        
        # Performance tracking
        self.capture_count = 0
        self.last_capture_time = 0
        self.fps_counter = deque(maxlen=30)
        
        # Analysis tracking
        self.last_analysis_time = 0
        self.last_frame_for_change = None
        
        # Detect monitors (but don't keep MSS instance)
        try:
            with mss.mss() as sct:
                monitors = sct.monitors
                
                # Use primary monitor (index 1, 0 is all monitors)
                if len(monitors) > 1:
                    self.monitor_info = monitors[1]
                else:
                    if self._logger:
                        self._logger.error("[OpenCV Vision] No monitors detected")
                    return True
            
            if self._logger:
                self._logger.system(
                    f"[OpenCV Vision] Initialized: {self.monitor_info['width']}x{self.monitor_info['height']}, "
                    f"target {self.target_fps} FPS, analysis every {self.analysis_interval}s, "
                    f"model: {self.vision_model}"
                )
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"[OpenCV Vision] Initialization error: {e}")
            return True  # Still return True for graceful degradation
    
    async def cleanup(self):
        """Cleanup vision resources"""
        # Stop capture thread
        if self.capture_running:
            self.capture_running = False
            if self.capture_thread:
                self.capture_thread.join(timeout=2.0)
        
        if self._logger:
            self._logger.system(
                f"[OpenCV Vision] Cleanup complete - captured {self.capture_count} frames"
            )
    
    def is_available(self) -> bool:
        """Check if OpenCV vision is available"""
        return OPENCV_AVAILABLE and self.monitor_info is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get vision system status"""
        fps = self._calculate_fps()
        
        return {
            'available': self.is_available(),
            'capture_running': self.capture_running,
            'capture_count': self.capture_count,
            'current_fps': fps,
            'target_fps': self.target_fps,
            'last_capture': self.last_capture_time,
            'analysis_interval': self.analysis_interval,
            'vision_model': self.vision_model,
            'monitor': {
                'width': self.monitor_info['width'] if self.monitor_info else 0,
                'height': self.monitor_info['height'] if self.monitor_info else 0
            }
        }
    
    # ========================================================================
    # CONTEXT LOOP (Continuous Monitoring)
    # ========================================================================
    
    def has_context_loop(self) -> bool:
        """Enable continuous monitoring via context loop"""
        return True
    
    async def context_loop(self, thought_buffer):
        """
        Background loop for continuous screen monitoring
        
        This runs while the tool is active and:
        1. Starts threaded screen capture
        2. Periodically analyzes frames
        3. Injects analysis into thought buffer
        4. Detects significant changes
        """
        if not self.is_available():
            if self._logger:
                self._logger.warning("[OpenCV Vision] Not available, context loop exiting")
            return
        
        # Start capture thread
        self._start_capture_thread()
        
        if self._logger:
            self._logger.system(
                f"[OpenCV Vision] Context loop started - "
                f"monitoring at {self.target_fps} FPS, analyzing every {self.analysis_interval}s"
            )
        
        try:
            while self._running:
                current_time = time.time()
                
                # Check if time for analysis
                time_since_analysis = current_time - self.last_analysis_time
                
                if time_since_analysis >= self.analysis_interval:
                    # Get latest frame
                    frame = self._get_latest_frame()
                    
                    if frame is not None:
                        # Check for significant changes (optional optimization)
                        should_analyze = True
                        
                        if self.last_frame_for_change is not None:
                            change_amount = self._calculate_frame_difference(
                                frame, 
                                self.last_frame_for_change
                            )
                            
                            # Only analyze if significant change
                            if change_amount < self.change_threshold:
                                should_analyze = False
                                # if self._logger:
                                #     self._logger.system(
                                #         f"[OpenCV Vision] Skipping analysis - "
                                #         f"change amount {change_amount:.0f} < threshold"
                                #     )
                        
                        if should_analyze:
                            # Analyze frame with vision model
                            analysis = await self._analyze_frame_with_vision(frame)
                            
                            if analysis:
                                # Inject into thought buffer with HIGH priority
                                thought_buffer.add_processed_thought(
                                    content=analysis,
                                    source='vision_result',
                                    timestamp=current_time
                                )
                                
                                if self._logger:
                                    self._logger.tool(
                                        f"[OpenCV Vision] Analysis injected to thought buffer"
                                    )
                            
                            self.last_frame_for_change = frame.copy()
                        
                        self.last_analysis_time = current_time
                
                # Sleep briefly
                await asyncio.sleep(0.5)
        
        except asyncio.CancelledError:
            if self._logger:
                self._logger.system("[OpenCV Vision] Context loop cancelled")
        except Exception as e:
            if self._logger:
                self._logger.error(f"[OpenCV Vision] Context loop error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Stop capture thread
            self.capture_running = False
            if self.capture_thread:
                self.capture_thread.join(timeout=2.0)
    
    # ========================================================================
    # THREADED SCREEN CAPTURE
    # ========================================================================
    
    def _start_capture_thread(self):
        """Start background capture thread"""
        self.capture_running = True
        self.capture_thread = Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        if self._logger:
            self._logger.system(f"[OpenCV Vision] Capture thread started at {self.target_fps} FPS")
    
    def _capture_loop(self):
        """Main capture loop (runs in separate thread)"""
        # Create MSS instance in this thread (thread-safe)
        with mss.mss() as sct:
            # Get monitor info
            monitors = sct.monitors
            if len(monitors) <= self.monitor_index:
                if self._logger:
                    self._logger.error(
                        f"[OpenCV Vision] Monitor index {self.monitor_index} not available"
                    )
                return
            
            monitor = monitors[self.monitor_index]
            frame_delay = 1.0 / self.target_fps
            last_capture = 0
            
            while self.capture_running:
                loop_start = time.perf_counter()
                
                # Throttle to target FPS
                elapsed = loop_start - last_capture
                if elapsed < frame_delay:
                    time.sleep(frame_delay - elapsed)
                    continue
                
                try:
                    # Capture screen with MSS (fast!)
                    screenshot = sct.grab(monitor)
                    
                    # Convert to numpy array (BGR for OpenCV)
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    
                    # Resize for performance
                    frame = cv2.resize(
                        frame, 
                        (self.capture_width, self.capture_height),
                        interpolation=cv2.INTER_AREA
                    )
                    
                    # Update latest frame (thread-safe)
                    with self.frame_lock:
                        self.latest_frame = frame.copy()
                    
                    # Add to buffer (non-blocking)
                    try:
                        self.frame_buffer.put_nowait(frame)
                    except Full:
                        # Buffer full, remove oldest
                        try:
                            self.frame_buffer.get_nowait()
                            self.frame_buffer.put_nowait(frame)
                        except:
                            pass
                    
                    # Track stats
                    self.capture_count += 1
                    self.last_capture_time = time.time()
                    self.fps_counter.append(time.perf_counter())
                    last_capture = loop_start
                    
                except Exception as e:
                    if self._logger:
                        self._logger.error(f"[OpenCV Vision] Capture error: {e}")
                    time.sleep(0.1)
    
    def _get_latest_frame(self) -> Optional[np.ndarray]:
        """Get most recent captured frame"""
        with self.frame_lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None
    
    def _calculate_fps(self) -> float:
        """Calculate actual capture FPS"""
        if len(self.fps_counter) < 2:
            return 0.0
        time_span = self.fps_counter[-1] - self.fps_counter[0]
        return len(self.fps_counter) / time_span if time_span > 0 else 0.0
    
    def _calculate_frame_difference(
        self, 
        frame1: np.ndarray, 
        frame2: np.ndarray
    ) -> float:
        """Calculate difference between frames for change detection"""
        try:
            diff = cv2.absdiff(frame1, frame2)
            return float(diff.sum())
        except:
            return 0.0
    
    # ========================================================================
    # VISION ANALYSIS
    # ========================================================================
    
    async def _analyze_frame_with_vision(self, frame: np.ndarray) -> Optional[str]:
        """
        Analyze frame using vision model
        
        Returns concise description for thought buffer
        """
        try:
            # Convert to base64 JPEG
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            buffer = BytesIO()
            pil_image.save(buffer, format="JPEG", quality=85, optimize=True)
            base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Prepare prompt for continuous monitoring
            prompt = (
                "You are monitoring a screen for an AI agent. "
                "Provide a description of what's currently visible on the screen. "
                "Focus on: active application, main content, any user interactions, "
                "and significant changes. Be concise." \
                "Keep the summary under 1000 characters."
            )
            
            # Add current context if available
            if hasattr(self._config, 'current_context') and self._config.current_context:
                prompt += f"\n\nCURRENT CONTEXT: {self._config.current_context}"
            
            # Call Ollama (non-blocking)
            import requests
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.post(
                    f"{self.ollama_endpoint}/api/generate",
                    json={
                        "model": self.vision_model,
                        "prompt": prompt,
                        "images": [base64_image],
                        "stream": False
                    },
                    timeout=20
                )
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get('response', '').strip()
                
                if analysis:
                    # Format for thought buffer
                    formatted = f"SCREEN VISION: {analysis}"
                    
                    if self._logger:
                        self._logger.success(
                            f"[Vision] Analysis: {analysis}..."
                        )
                    
                    return formatted
            
            else:
                if self._logger:
                    self._logger.error(
                        f"[OpenCV Vision] Vision model error: HTTP {response.status_code}"
                    )
                return None
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[OpenCV Vision] Analysis error: {e}")
            return None
    
    # ========================================================================
    # COMMAND EXECUTION
    # ========================================================================
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute vision commands
        
        Commands:
        - get_status: Get current monitoring status
        - capture_now: Force immediate capture and analysis
        - set_fps: Change capture frame rate [fps: int]
        - set_interval: Change analysis interval [seconds: float]
        """
        if not self.is_available():
            return self._error_result(
                'OpenCV Vision not available',
                guidance='Install: pip install mss opencv-python numpy'
            )
        
        if command == 'get_status':
            status = self.get_status()
            status_text = (
                f"OpenCV Vision Status:\n"
                f"- Capturing: {status['capture_running']}\n"
                f"- FPS: {status['current_fps']:.1f} / {status['target_fps']}\n"
                f"- Captures: {status['capture_count']}\n"
                f"- Analysis interval: {status['analysis_interval']}s\n"
                f"- Model: {status['vision_model']}"
            )
            return self._success_result(status_text, metadata=status)
        
        elif command == 'capture_now':
            frame = self._get_latest_frame()
            if frame is None:
                return self._error_result('No frame available')
            
            analysis = await self._analyze_frame_with_vision(frame)
            if analysis:
                return self._success_result(analysis)
            else:
                return self._error_result('Analysis failed')
        
        elif command == 'set_fps':
            if not args or not isinstance(args[0], (int, float)):
                return self._error_result(
                    'set_fps requires FPS value',
                    guidance='Format: {"tool": "opencv_vision.set_fps", "args": [15]}'
                )
            
            new_fps = max(1, min(60, int(args[0])))
            self.target_fps = new_fps
            
            return self._success_result(
                f'FPS set to {new_fps}',
                metadata={'fps': new_fps}
            )
        
        elif command == 'set_interval':
            if not args or not isinstance(args[0], (int, float)):
                return self._error_result(
                    'set_interval requires seconds value',
                    guidance='Format: {"tool": "opencv_vision.set_interval", "args": [3.0]}'
                )
            
            new_interval = max(1.0, float(args[0]))
            self.analysis_interval = new_interval
            
            return self._success_result(
                f'Analysis interval set to {new_interval}s',
                metadata={'interval': new_interval}
            )
        
        else:
            return self._error_result(
                f'Unknown command: {command}',
                guidance='Available: get_status, capture_now, set_fps, set_interval'
            )
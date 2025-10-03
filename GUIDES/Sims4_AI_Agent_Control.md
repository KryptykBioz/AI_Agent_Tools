# Step-by-Step Sims 4 AI Agent Implementation

## Phase 1: Environment Setup and Game Detection

### Step 1: Install Dependencies and Setup Window Detection

```bash
pip install pyautogui pynput opencv-python pillow numpy pywin32 pytesseract mss
```

### Step 2: Create Game Window Detector

```python
import win32gui
import win32con
import win32api
from mss import mss
import numpy as np

class GameWindowManager:
    def __init__(self):
        self.sims_hwnd = None
        self.window_rect = None
        self.sct = mss()
        
    def find_sims4_window(self):
        """Locate The Sims 4 window handle"""
        def enum_callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                
                # Sims 4 window detection
                if ("sims" in window_text.lower() and "4" in window_text) or \
                   "ts4" in window_text.lower() or \
                   class_name == "Sims4WndClass":  # Actual Sims 4 window class
                    results.append((hwnd, window_text))
        
        windows = []
        win32gui.EnumWindows(enum_callback, windows)
        
        if windows:
            self.sims_hwnd = windows[0][0]
            self.update_window_rect()
            print(f"Found Sims 4 window: {windows[0][1]}")
            return True
        else:
            print("Sims 4 window not found. Make sure the game is running.")
            return False
    
    def update_window_rect(self):
        """Get current window position and size"""
        if self.sims_hwnd:
            self.window_rect = win32gui.GetWindowRect(self.sims_hwnd)
            print(f"Window rect: {self.window_rect}")
    
    def capture_window(self):
        """Capture the Sims 4 window content"""
        if not self.sims_hwnd or not self.window_rect:
            return None
            
        # Bring window to foreground if needed
        win32gui.SetForegroundWindow(self.sims_hwnd)
        
        # Capture using mss for better performance
        left, top, right, bottom = self.window_rect
        monitor = {
            "top": top,
            "left": left, 
            "width": right - left,
            "height": bottom - top
        }
        
        screenshot = self.sct.grab(monitor)
        return np.array(screenshot)[:,:,:3]  # Remove alpha channel
```

### Step 3: Test Window Detection

```python
# Test the window detection
window_manager = GameWindowManager()
if window_manager.find_sims4_window():
    screenshot = window_manager.capture_window()
    if screenshot is not None:
        print(f"Screenshot captured: {screenshot.shape}")
        # Save test image
        from PIL import Image
        Image.fromarray(screenshot).save("sims4_test_capture.png")
    else:
        print("Failed to capture screenshot")
else:
    print("Please start The Sims 4 and try again")
```

## Phase 2: UI Element Recognition

### Step 4: Create UI Template Matcher

```python
import cv2
import os

class Sims4UIDetector:
    def __init__(self):
        self.templates = {}
        self.load_ui_templates()
    
    def load_ui_templates(self):
        """Load UI element templates for matching"""
        # You'll need to create these template images
        template_files = {
            'needs_panel': 'templates/needs_panel.png',
            'pie_menu_center': 'templates/pie_menu_center.png',
            'plumbob': 'templates/plumbob.png',
            'pause_button': 'templates/pause_button.png',
            'speed_controls': 'templates/speed_controls.png'
        }
        
        for name, file_path in template_files.items():
            if os.path.exists(file_path):
                template = cv2.imread(file_path, cv2.IMREAD_COLOR)
                self.templates[name] = template
                print(f"Loaded template: {name}")
    
    def find_needs_panel(self, screenshot):
        """Locate the Sim needs panel"""
        # Convert to OpenCV format
        screenshot_cv = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        
        # Needs panel is typically in bottom-left corner
        height, width = screenshot.shape[:2]
        search_region = screenshot_cv[height-250:height-50, 0:400]
        
        # Look for characteristic needs panel elements
        needs_region = self.detect_needs_region(search_region)
        
        if needs_region:
            # Convert back to original coordinates
            x, y, w, h = needs_region
            return (x, height-250+y, w, h)
        
        return None
    
    def detect_needs_region(self, region):
        """Detect needs panel using color and pattern matching"""
        # Needs bars typically have specific colors
        # Green (high), Yellow (medium), Red (low)
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        
        # Define color ranges for needs bars
        green_lower = np.array([35, 100, 100])
        green_upper = np.array([85, 255, 255])
        
        red_lower = np.array([0, 120, 100])
        red_upper = np.array([10, 255, 255])
        
        # Find colored regions
        green_mask = cv2.inRange(hsv, green_lower, green_upper)
        red_mask = cv2.inRange(hsv, red_lower, red_upper)
        
        # Combine masks and find contours
        combined_mask = cv2.bitwise_or(green_mask, red_mask)
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Find the largest rectangular region
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # Validate size (needs panel should be reasonably sized)
            if w > 50 and h > 100:
                return (x, y, w, h)
        
        return None
    
    def detect_pie_menu(self, screenshot):
        """Detect if a pie menu is currently open"""
        # Pie menus have a distinctive circular pattern
        # Look for radial arrangement of menu items
        
        gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)
        
        # Use HoughCircles to detect circular patterns
        circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, 1, 100,
            param1=50, param2=30, minRadius=30, maxRadius=150
        )
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                # Validate this looks like a pie menu
                if self.validate_pie_menu(screenshot, x, y, r):
                    return {'center': (x, y), 'radius': r}
        
        return None
    
    def validate_pie_menu(self, screenshot, x, y, r):
        """Validate that detected circle is actually a pie menu"""
        # Extract region around detected circle
        roi = screenshot[max(0, y-r):min(screenshot.shape[0], y+r),
                        max(0, x-r):min(screenshot.shape[1], x+r)]
        
        # Look for text elements (menu options have text)
        import pytesseract
        text = pytesseract.image_to_string(roi)
        
        # Common Sims 4 pie menu words
        pie_menu_keywords = ['talk', 'use', 'view', 'sit', 'eat', 'sleep', 'watch']
        
        return any(keyword in text.lower() for keyword in pie_menu_keywords)
```

### Step 5: Test UI Detection

```python
# Test UI detection
ui_detector = Sims4UIDetector()

# Capture and analyze
screenshot = window_manager.capture_window()
if screenshot is not None:
    # Test needs panel detection
    needs_panel = ui_detector.find_needs_panel(screenshot)
    if needs_panel:
        print(f"Needs panel found at: {needs_panel}")
    
    # Test pie menu detection
    pie_menu = ui_detector.detect_pie_menu(screenshot)
    if pie_menu:
        print(f"Pie menu detected at: {pie_menu}")
```

## Phase 3: Input Command System

### Step 6: Create Coordinate Transformation System

```python
import pyautogui

class Sims4InputController:
    def __init__(self, window_manager):
        self.window_manager = window_manager
        pyautogui.FAILSAFE = True  # Move mouse to corner to stop
        pyautogui.PAUSE = 0.1
        
    def screen_to_game_coords(self, rel_x, rel_y):
        """Convert relative coordinates to absolute screen coordinates"""
        if not self.window_manager.window_rect:
            return None
            
        left, top, right, bottom = self.window_manager.window_rect
        
        # Convert relative coordinates (0-1) to absolute
        if isinstance(rel_x, float) and isinstance(rel_y, float):
            abs_x = left + int(rel_x * (right - left))
            abs_y = top + int(rel_y * (bottom - top))
        else:
            # Direct pixel coordinates relative to game window
            abs_x = left + rel_x
            abs_y = top + rel_y
            
        return (abs_x, abs_y)
    
    def safe_click(self, x, y, button='left', duration=0.1):
        """Safely click at coordinates with validation"""
        # Ensure game window is active
        if self.window_manager.sims_hwnd:
            win32gui.SetForegroundWindow(self.window_manager.sims_hwnd)
            time.sleep(0.1)
        
        # Convert coordinates
        screen_coords = self.screen_to_game_coords(x, y)
        if not screen_coords:
            return False
            
        abs_x, abs_y = screen_coords
        
        # Validate coordinates are within game window
        left, top, right, bottom = self.window_manager.window_rect
        if not (left <= abs_x <= right and top <= abs_y <= bottom):
            print(f"Click coordinates outside game window: {abs_x}, {abs_y}")
            return False
        
        try:
            if button == 'left':
                pyautogui.click(abs_x, abs_y, duration=duration)
            elif button == 'right':
                pyautogui.rightClick(abs_x, abs_y)
            
            print(f"Clicked at game coords: ({x}, {y}) -> screen coords: ({abs_x}, {abs_y})")
            return True
            
        except Exception as e:
            print(f"Click failed: {e}")
            return False
    
    def send_movement_command(self, target_x, target_y):
        """Send movement command to Sim"""
        # In Sims 4, left-click moves the Sim to that location
        return self.safe_click(target_x, target_y, 'left')
    
    def send_interaction_command(self, object_x, object_y):
        """Send interaction command (right-click on object)"""
        # Right-click opens pie menu for interactions
        return self.safe_click(object_x, object_y, 'right')
    
    def select_pie_menu_option(self, option_text, menu_center, menu_radius):
        """Select specific option from pie menu"""
        # After right-clicking, pie menu appears
        # We need to click on the appropriate segment
        
        # Wait for menu to appear
        time.sleep(0.3)
        
        # Take new screenshot to see menu options
        screenshot = self.window_manager.capture_window()
        if screenshot is None:
            return False
        
        # Analyze pie menu segments
        pie_options = self.analyze_pie_menu_options(screenshot, menu_center, menu_radius)
        
        # Find matching option
        for option in pie_options:
            if self.text_matches_intent(option['text'], option_text):
                # Click on the option
                return self.safe_click(option['x'], option['y'], 'left')
        
        # If no match found, click center to cancel
        self.safe_click(menu_center[0], menu_center[1], 'left')
        return False
    
    def analyze_pie_menu_options(self, screenshot, center, radius):
        """Analyze individual pie menu options"""
        # Extract pie menu region
        cx, cy = center
        x1, y1 = max(0, cx - radius), max(0, cy - radius)
        x2, y2 = min(screenshot.shape[1], cx + radius), min(screenshot.shape[0], cy + radius)
        
        pie_region = screenshot[y1:y2, x1:x2]
        
        # Use OCR to extract text from pie menu
        import pytesseract
        
        # Improve OCR accuracy with preprocessing
        gray = cv2.cvtColor(pie_region, cv2.COLOR_RGB2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # OCR configuration for menu text
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz '
        
        try:
            ocr_data = pytesseract.image_to_data(gray, config=custom_config, output_type=pytesseract.Output.DICT)
            
            options = []
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                if text and len(text) > 2:  # Filter out noise
                    # Convert coordinates back to original screenshot
                    x = x1 + (ocr_data['left'][i] // 2)  # Account for 2x scaling
                    y = y1 + (ocr_data['top'][i] // 2)
                    
                    options.append({
                        'text': text,
                        'x': x,
                        'y': y,
                        'confidence': ocr_data['conf'][i]
                    })
            
            return options
            
        except Exception as e:
            print(f"OCR error: {e}")
            return []
    
    def text_matches_intent(self, detected_text, intended_action):
        """Match detected pie menu text with intended action"""
        detected_lower = detected_text.lower()
        intended_lower = intended_action.lower()
        
        # Define common action mappings
        action_synonyms = {
            'use': ['use', 'interact'],
            'sit': ['sit', 'sit down', 'relax'],
            'eat': ['eat', 'have meal', 'grab food'],
            'sleep': ['sleep', 'nap', 'rest'],
            'watch': ['watch', 'view'],
            'talk': ['talk', 'chat', 'socialize'],
            'woo': ['flirt', 'woo', 'romantic'],
            'repair': ['repair', 'fix'],
            'clean': ['clean', 'tidy']
        }
        
        # Check direct match
        if intended_lower in detected_lower or detected_lower in intended_lower:
            return True
        
        # Check synonym matches
        for action, synonyms in action_synonyms.items():
            if any(syn in intended_lower for syn in synonyms):
                if action in detected_lower or any(syn in detected_lower for syn in synonyms):
                    return True
        
        return False
    
    def send_keyboard_shortcut(self, key_combination):
        """Send keyboard shortcuts to game"""
        # Ensure game window is active
        if self.window_manager.sims_hwnd:
            win32gui.SetForegroundWindow(self.window_manager.sims_hwnd)
            time.sleep(0.1)
        
        try:
            if isinstance(key_combination, str):
                pyautogui.press(key_combination)
            elif isinstance(key_combination, list):
                pyautogui.hotkey(*key_combination)
            
            print(f"Sent keyboard shortcut: {key_combination}")
            return True
            
        except Exception as e:
            print(f"Keyboard shortcut failed: {e}")
            return False
```

## Phase 4: Command Execution Flow

### Step 7: Create Command Execution Pipeline

```python
import time
from enum import Enum

class ActionType(Enum):
    MOVE = "move"
    INTERACT = "interact" 
    SOCIAL = "social"
    SHORTCUT = "shortcut"
    WAIT = "wait"

class Sims4CommandExecutor:
    def __init__(self, window_manager, input_controller, ui_detector):
        self.window_manager = window_manager
        self.input_controller = input_controller
        self.ui_detector = ui_detector
        self.last_action_time = 0
        self.action_timeout = 10  # seconds
        
    def execute_action(self, action_description):
        """Execute a natural language action"""
        print(f"Executing: {action_description}")
        
        # Parse action type and parameters
        action = self.parse_action(action_description)
        if not action:
            print("Could not parse action")
            return False
        
        # Execute based on action type
        success = False
        if action['type'] == ActionType.MOVE:
            success = self.execute_move_action(action)
        elif action['type'] == ActionType.INTERACT:
            success = self.execute_interact_action(action)
        elif action['type'] == ActionType.SOCIAL:
            success = self.execute_social_action(action)
        elif action['type'] == ActionType.SHORTCUT:
            success = self.execute_shortcut_action(action)
        elif action['type'] == ActionType.WAIT:
            success = self.execute_wait_action(action)
        
        # Record action timing
        if success:
            self.last_action_time = time.time()
            print(f"Action completed: {action_description}")
        else:
            print(f"Action failed: {action_description}")
        
        return success
    
    def parse_action(self, description):
        """Parse natural language action into structured command"""
        desc_lower = description.lower().strip()
        
        # Movement actions
        if any(word in desc_lower for word in ['go to', 'walk to', 'move to']):
            # Extract target location
            target = self.extract_location_from_text(desc_lower)
            return {
                'type': ActionType.MOVE,
                'target': target,
                'coordinates': self.find_location_on_screen(target)
            }
        
        # Interaction actions  
        if any(word in desc_lower for word in ['use', 'interact with', 'click on']):
            # Extract object name
            obj = self.extract_object_from_text(desc_lower)
            return {
                'type': ActionType.INTERACT,
                'object': obj,
                'action': self.extract_specific_action(desc_lower),
                'coordinates': self.find_object_on_screen(obj)
            }
        
        # Social actions
        if any(word in desc_lower for word in ['talk to', 'chat with', 'socialize']):
            sim_name = self.extract_sim_name_from_text(desc_lower)
            return {
                'type': ActionType.SOCIAL,
                'target_sim': sim_name,
                'action': self.extract_social_action(desc_lower),
                'coordinates': self.find_sim_on_screen(sim_name)
            }
        
        # Keyboard shortcuts
        if any(word in desc_lower for word in ['pause', 'speed', 'build mode', 'buy mode']):
            shortcut = self.map_to_shortcut(desc_lower)
            return {
                'type': ActionType.SHORTCUT,
                'keys': shortcut
            }
        
        return None
    
    def execute_interact_action(self, action):
        """Execute object interaction"""
        if not action.get('coordinates'):
            print(f"Could not locate object: {action.get('object')}")
            return False
        
        x, y = action['coordinates']
        
        # Right-click on object to open pie menu
        if not self.input_controller.send_interaction_command(x, y):
            return False
        
        # Wait for pie menu to appear
        time.sleep(0.5)
        
        # Capture screenshot to analyze pie menu
        screenshot = self.window_manager.capture_window()
        if screenshot is None:
            return False
        
        # Detect pie menu
        pie_menu = self.ui_detector.detect_pie_menu(screenshot)
        if not pie_menu:
            print("Pie menu not detected")
            return False
        
        # Select appropriate action from pie menu
        specific_action = action.get('action', 'use')
        return self.input_controller.select_pie_menu_option(
            specific_action, 
            pie_menu['center'], 
            pie_menu['radius']
        )
    
    def wait_for_action_completion(self, timeout=None):
        """Wait for current action to complete before next action"""
        if timeout is None:
            timeout = self.action_timeout
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Take screenshot to check if action is still in progress
            screenshot = self.window_manager.capture_window()
            if screenshot is None:
                break
            
            # Check for action queue or busy indicators
            if self.is_sim_busy(screenshot):
                time.sleep(1)
                continue
            else:
                print("Action completed")
                return True
        
        print("Action timeout")
        return False
    
    def is_sim_busy(self, screenshot):
        """Check if Sim is currently performing an action"""
        # Look for action queue indicators
        # Check if there's a progress bar or action icon visible
        # This would need to be calibrated based on UI elements
        
        # Simple implementation: assume Sim is busy if pie menu is not visible
        pie_menu = self.ui_detector.detect_pie_menu(screenshot)
        return pie_menu is None  # If no pie menu available, Sim might be busy
```

### Step 8: Test Complete Command Flow

```python
def test_command_execution():
    """Test the complete command execution pipeline"""
    
    # Initialize components
    window_manager = GameWindowManager()
    if not window_manager.find_sims4_window():
        print("Please start The Sims 4")
        return
    
    ui_detector = Sims4UIDetector()
    input_controller = Sims4InputController(window_manager)
    executor = Sims4CommandExecutor(window_manager, input_controller, ui_detector)
    
    # Test sequence of actions
    test_actions = [
        "use the toilet",
        "go to the kitchen", 
        "use the refrigerator",
        "sit on the couch",
        "watch tv"
    ]
    
    for action in test_actions:
        print(f"\n--- Testing: {action} ---")
        
        # Execute action
        success = executor.execute_action(action)
        
        if success:
            # Wait for action to complete
            executor.wait_for_action_completion()
        else:
            print(f"Failed to execute: {action}")
        
        # Pause between actions
        time.sleep(2)

# Run the test
if __name__ == "__main__":
    test_command_execution()
```

## Critical Implementation Notes

### How Commands Are Actually Sent to The Game:

1. **No Direct Game API**: The Sims 4 doesn't expose an API, so all commands go through:
   - **Mouse clicks** at specific screen coordinates
   - **Keyboard shortcuts** using Windows input simulation
   - **Window focus management** to ensure inputs reach the game

2. **Command Flow**:
   ```
   AI Decision → Parse Action → Find Screen Location → Send Input → Validate Result
   ```

3. **Timing is Critical**:
   - Must wait for animations to complete
   - Pie menus take ~300ms to appear
   - Actions can take 5-30 seconds to execute
   - Game speed affects timing

4. **Coordinate System**:
   - Capture game window boundaries
   - Convert relative coordinates to absolute screen positions
   - Validate clicks are within game window

5. **Input Validation**:
   - Always check if game window is active
   - Verify coordinates are valid before clicking
   - Handle cases where UI elements move or disappear

This system essentially "plays" the game exactly like a human would - by looking at the screen and clicking/typing, but automated through your AI agent's decision-making.
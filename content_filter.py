# Filename: BASE/tools/content_filter.py
"""
Content filtering system for AI responses
Detects profanity, hate speech, and controversial content
"""

import re
import requests
from typing import Tuple, Optional
from pathlib import Path

class ContentFilter:
    def __init__(self, ollama_endpoint: str = "http://127.0.0.1:11434", use_ai_filter: bool = True):
        """
        Initialize content filter
        
        Args:
            ollama_endpoint: Ollama API endpoint for AI-based filtering
            use_ai_filter: Whether to use AI model for semantic analysis
        """
        self.ollama_endpoint = ollama_endpoint
        self.use_ai_filter = use_ai_filter
        
        # Keyword-based filter lists
        self.profanity_patterns = self._load_profanity_patterns()
        self.hate_speech_patterns = self._load_hate_speech_patterns()
        self.controversial_patterns = self._load_controversial_patterns()
        
    def _load_profanity_patterns(self) -> list:
        """Load profanity detection patterns"""
        # Common profanity patterns (case-insensitive)
        patterns = [
            r'\bf+u+c+k+',
            r'\bs+h+i+t+',
            r'\bb+i+t+c+h+',
            r'\ba+s+s+h+o+l+e+',
            r'\bd+a+m+n+',
            r'\bh+e+l+l+',
            r'\bc+r+a+p+',
            r'\bp+i+s+s+',
            r'\bc+u+n+t+',
            r'\bd+i+c+k+',
            r'\bc+o+c+k+',
            r'\bp+u+s+s+y+',
            r'\bs+l+u+t+',
            r'\bw+h+o+r+e+',
        ]
        return [re.compile(p, re.IGNORECASE) for p in patterns]
    
    def _load_hate_speech_patterns(self) -> list:
        """Load hate speech detection patterns"""
        # Patterns for hate speech (intentionally limited to avoid false positives)
        patterns = [
            r'\bn+i+g+g+e+r+',
            r'\bf+a+g+g+o+t+',
            r'\br+e+t+a+r+d+',
            r'\bk+i+k+e+',
            r'\bg+o+o+k+',
            r'\bc+h+i+n+k+',
            r'kill yourself',
            r'kys',
            r'die in a fire',
        ]
        return [re.compile(p, re.IGNORECASE) for p in patterns]
    
    def _load_controversial_patterns(self) -> list:
        """Load controversial topic patterns"""
        # High-risk controversial patterns
        patterns = [
            r'holocaust.{0,20}(hoax|fake|didn)',
            r'(white|black|racial).{0,30}supremac',
            r'(nazi|hitler).{0,20}(right|good|based)',
            r'(genocide|ethnic cleansing).{0,20}(justified|good)',
        ]
        return [re.compile(p, re.IGNORECASE) for p in patterns]
    
    def _check_keywords(self, text: str) -> Tuple[bool, str]:
        """
        Check text against keyword patterns
        
        Returns:
            (is_filtered, reason)
        """
        # Check profanity
        for pattern in self.profanity_patterns:
            if pattern.search(text):
                return True, "profanity"
        
        # Check hate speech
        for pattern in self.hate_speech_patterns:
            if pattern.search(text):
                return True, "hate_speech"
        
        # Check controversial content
        for pattern in self.controversial_patterns:
            if pattern.search(text):
                return True, "controversial"
        
        return False, ""
    
    def _check_with_ai(self, text: str) -> Tuple[bool, str]:
        """
        Use AI model to detect harmful content semantically
        
        Returns:
            (is_filtered, reason)
        """
        if not self.use_ai_filter:
            return False, ""
        
        try:
            filter_prompt = f"""Analyze this text for harmful content. Respond with ONLY ONE WORD:
- "SAFE" if the text is acceptable (playful banter, teasing, humor are OK)
- "PROFANITY" if it contains explicit profanity
- "HATE" if it contains hate speech or slurs
- "CONTROVERSIAL" if it promotes harmful ideologies or extreme views
- "SAFE" for all other cases

Text to analyze: "{text}"

Response (one word only):"""

            payload = {
                "model": "llama3.2:3b",  # Use fast, small model for filtering
                "prompt": filter_prompt,
                "stream": False,
                "temperature": 0.1,  # Low temperature for consistent filtering
                "max_tokens": 10,
                "stop": ["\n", ".", ","]
            }
            
            response = requests.post(
                f"{self.ollama_endpoint}/api/generate",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "").strip().upper()
                
                if "PROFANITY" in ai_response:
                    return True, "profanity"
                elif "HATE" in ai_response:
                    return True, "hate_speech"
                elif "CONTROVERSIAL" in ai_response:
                    return True, "controversial"
            
            return False, ""
            
        except Exception as e:
            print(f"[Filter] AI check error: {e}")
            return False, ""
    
    def filter_content(self, text: str, log_callback=None) -> Tuple[str, bool, str]:
        """
        Filter content and return sanitized version
        
        Args:
            text: Text to filter
            log_callback: Optional function to log filter actions
        
        Returns:
            (filtered_text, was_filtered, reason)
        """
        if not text or not text.strip():
            return text, False, ""
        
        # First check with keywords (fast)
        is_filtered, reason = self._check_keywords(text)
        
        # If keywords didn't catch it, try AI filter
        if not is_filtered and self.use_ai_filter:
            is_filtered, reason = self._check_with_ai(text)
        
        if is_filtered:
            if log_callback:
                log_callback(f"[Filter] Content filtered - Reason: {reason}")
                log_callback(f"[Filter] Original length: {len(text)} chars")
            return "Filtered", True, reason
        
        return text, False, ""
    
    def update_ai_filter_setting(self, enabled: bool):
        """Update whether to use AI-based filtering"""
        self.use_ai_filter = enabled
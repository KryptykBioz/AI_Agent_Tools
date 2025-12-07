# Filename: BASE/tools/installed/bing_search/tool.py
"""
Bing Search Tool - Simplified Architecture
Single master class with start() and end() lifecycle
Web search using Bing API for current information
"""
import asyncio
from typing import List, Dict, Any, Optional
from BASE.handlers.base_tool import BaseTool
import requests


class BingSearchTool(BaseTool):
    """
    Bing web search for current information
    Provides top 5 most relevant results from Bing Search API
    """
    
    @property
    def name(self) -> str:
        return "bing"
    
    async def initialize(self) -> bool:
        """
        Initialize Bing search system
        
        Returns:
            True if initialization successful (always returns True for graceful degradation)
        """
        # Get Bing API key from config
        self.api_key = getattr(self._config, 'bing_search_api_key', None)
        self.endpoint = getattr(
            self._config, 
            'bing_search_endpoint', 
            'https://api.bing.microsoft.com/v7.0/search'
        )
        
        if self._logger:
            if self.api_key:
                self._logger.system(
                    f"[Bing] Search system ready (endpoint: {self.endpoint})"
                )
            else:
                self._logger.warning(
                    "[Bing] Not available: No API key configured. "
                    "Set bing_search_api_key in config.json"
                )
        
        # Always return True for graceful degradation
        return True
    
    async def cleanup(self):
        """Cleanup search resources"""
        if self._logger:
            self._logger.system("[Bing] Cleanup complete")
    
    def is_available(self) -> bool:
        """
        Check if Bing search is available
        
        Returns:
            True if API key is configured
        """
        return bool(self.api_key)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get search system status
        
        Returns:
            Status dictionary with API info
        """
        return {
            'available': self.is_available(),
            'backend': 'Bing Search API',
            'has_api_key': bool(self.api_key),
            'endpoint': self.endpoint
        }
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute Bing search command
        
        Commands:
        - search: [query: str] - Search the web for information
        
        Args:
            command: Command name ('search')
            args: Command arguments as defined in information.json
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[Bing] Command: '{command}', args: {args}")
        
        # Check availability first
        if not self.is_available():
            return self._error_result(
                'Bing search unavailable: No API key configured',
                guidance='Configure bing_search_api_key in config.json'
            )
        
        # Validate command (default to search for backward compatibility)
        if not command:
            command = 'search'
        
        try:
            # Route to appropriate handler
            if command == 'search':
                return await self._handle_search_command(args)
            else:
                return self._error_result(
                    f'Unknown command: {command}',
                    guidance='Use: bing.search'
                )
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Bing] Command execution error: {e}")
            import traceback
            traceback.print_exc()
            
            return self._error_result(
                f'Command execution failed: {str(e)}',
                metadata={'error': str(e)},
                guidance='Check logs for details'
            )
    
    async def _handle_search_command(self, args: List[Any]) -> Dict[str, Any]:
        """
        Handle search command: bing.search with [query: str]
        
        Args:
            args: [query]
            
        Returns:
            Result dict with search results
        """
        # Validate arguments
        if not args:
            return self._error_result(
                'No search query provided',
                guidance='Provide a search query string'
            )
        
        # Extract query
        query = str(args[0])
        
        if not query or not query.strip():
            return self._error_result(
                'Empty search query',
                guidance='Provide a non-empty search query'
            )
        
        # Perform Bing search
        if self._logger:
            self._logger.tool(f"[Bing] Searching: '{query}'")
        
        results = await self._perform_bing_search(query)
        
        if results:
            # Count results
            double_newline = '\n\n'
            result_count = len(results.split(double_newline))
            
            if self._logger:
                self._logger.success(
                    f"[Bing] Search completed: {result_count} results"
                )
            
            return self._success_result(
                results,
                metadata={
                    'query': query,
                    'result_count': result_count
                }
            )
        else:
            if self._logger:
                self._logger.warning(f"[Bing] No results found for: '{query}'")
            
            return self._error_result(
                f'No results found for query: {query}',
                metadata={'query': query},
                guidance='Try different search terms or broader query'
            )
    
    async def _perform_bing_search(self, query: str) -> str:
        """
        Perform Bing search and format results
        
        Args:
            query: Search query string
            
        Returns:
            Formatted search results or empty string on failure
        """
        if not self.api_key:
            if self._logger:
                self._logger.error("[Bing] No API key configured")
            return ""
        
        try:
            headers = {'Ocp-Apim-Subscription-Key': self.api_key}
            params = {
                'q': query,
                'count': 5,  # Top 5 results
                'textDecorations': False,
                'textFormat': 'Raw'
            }
            
            if self._logger:
                self._logger.tool(f"[Bing] Calling Bing API...")
            
            response = requests.get(
                self.endpoint,
                headers=headers,
                params=params,
                timeout=25  # 25s timeout (handler has 30s)
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Format results
            if 'webPages' in data and 'value' in data['webPages']:
                # Build results list
                results = []
                for i, item in enumerate(data['webPages']['value'][:5], 1):
                    title = item.get('name', 'No title')
                    snippet = item.get('snippet', 'No description')
                    url = item.get('url', '')
                    
                    # Build result entry
                    result_entry = f"{i}. {title}\n{snippet}\nSource: {url}"
                    results.append(result_entry)
                
                # Join with double newline
                formatted = "\n\n".join(results)
                
                if self._logger:
                    self._logger.tool(f"[Bing] Found {len(results)} results")
                
                return formatted
            
            else:
                if self._logger:
                    self._logger.warning("[Bing] No results in response")
                return ""
        
        except requests.exceptions.Timeout:
            if self._logger:
                self._logger.error("[Bing] Request timed out")
            return ""
        
        except requests.exceptions.RequestException as e:
            if self._logger:
                self._logger.error(f"[Bing] Request failed: {e}")
            return ""
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[Bing] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return ""
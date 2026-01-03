# Filename: BASE/tools/installed/wiki_search/tool.py
"""
Wikipedia Search Tool - Simplified Architecture
Single master class with start() and end() lifecycle
"""
import asyncio
from typing import List, Dict, Any, Optional, Set, Tuple
from BASE.handlers.base_tool import BaseTool
import requests
import re
import random


class WikiSearchTool(BaseTool):
    """
    Wikipedia search with position tracking for varied results
    Ensures repeated searches return different content sections
    """

    __slots__ = ('max_results', 'headers')
    
    API_URL = "https://en.wikipedia.org/w/api.php"
    CHUNK_SIZE = 500
    CHUNK_GOAL = 5
    MIN_CHUNK_DISTANCE = 300
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    ]
    
    # Class-level cache for tracking used positions per article
    _position_cache: Dict[str, Set[int]] = {}
    
    @property
    def name(self) -> str:
        return "wiki_search"
    
    async def initialize(self) -> bool:
        """Initialize Wikipedia search system"""
        # Get max results from config/controls
        try:
            import personality.controls as controls
            self.max_results = getattr(controls, 'MAX_SEARCH_RESULTS', 5)
        except:
            self.max_results = 5
        
        self.headers = {
            'User-Agent': f'WikipediaAgent/2.0 (Python; {random.choice(self.USER_AGENTS)})'
        }
        
        if self._logger:
            self._logger.system(
                f"[WikiSearch] Wikipedia search ready "
                f"(max_results: {self.max_results})"
            )
        
        return True
    
    async def cleanup(self):
        """Cleanup search resources"""
        self._position_cache.clear()
        if self._logger:
            self._logger.system("[WikiSearch] Cleaned up position cache")
    
    def is_available(self) -> bool:
        """Check if Wikipedia search is available"""
        return True
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute Wikipedia search command
        
        Commands:
        - search: Search Wikipedia (default)
        
        Args:
            command: Command name ('search')
            args: [query: str, max_results: Optional[int]]
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[WikiSearch] Command: '{command}', args: {args}")
        
        if not args:
            return self._error_result(
                'No search query provided',
                guidance='Provide a search query: {"tool": "wiki_search.search", "args": ["topic"]}'
            )
        
        query = str(args[0]).strip()
        max_results = int(args[1]) if len(args) > 1 else self.max_results
        
        if not query:
            return self._error_result(
                'Empty search query',
                guidance='Provide a non-empty search query'
            )
        
        # Execute Wikipedia search
        if command in ['search', '']:
            return await self._search_wikipedia(query, max_results)
        else:
            return self._error_result(
                f'Unknown command: {command}',
                guidance='Available commands: search'
            )
    
    async def _search_wikipedia(self, query: str, max_results: int) -> Dict[str, Any]:
        """
        Search Wikipedia with position tracking for varied results
        
        Args:
            query: Search query
            max_results: Maximum number of result chunks
            
        Returns:
            Result dict with Wikipedia content
        """
        try:
            if self._logger:
                self._logger.tool(f"[WikiSearch] Searching: {query}")
            
            # Extract query words for matching
            query_words = {w for w in re.findall(r'\b\w+\b', query.lower()) if len(w) >= 3}
            
            # Find best matching article
            title, page_id = self._find_article_info(query)
            
            if not title or not page_id:
                return self._error_result(
                    f'No Wikipedia article found for: {query}',
                    metadata={'query': query},
                    guidance='Try different search terms or check spelling'
                )
            
            # Create unique key for position tracking
            article_key = f"{page_id}:{title}"
            
            # Fetch full article
            article_text = self._fetch_full_article(page_id)
            
            if not article_text:
                return self._error_result(
                    f'Could not retrieve article: {title}',
                    metadata={'query': query, 'article': title},
                    guidance='Wikipedia API may be unavailable - try again'
                )
            
            # Extract contextual chunks with position tracking
            chunks = self._extract_context_chunks(article_text, query_words, article_key)
            
            if not chunks:
                # Reset position cache and try again
                if article_key in self._position_cache:
                    self._position_cache[article_key].clear()
                    chunks = self._extract_context_chunks(article_text, query_words, article_key)
                
                if not chunks:
                    return self._error_result(
                        f'No relevant content found in article: {title}',
                        metadata={'query': query, 'article': title},
                        guidance='Try more specific search terms'
                    )
            
            # Format results
            url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
            content = self._format_results(title, url, chunks[:max_results])
            
            # Track statistics
            positions_used = len(self._position_cache.get(article_key, []))
            
            if self._logger:
                self._logger.success(
                    f"[WikiSearch] Retrieved {len(chunks)} chunks "
                    f"(position #{positions_used} in article)"
                )
            
            return self._success_result(
                content,
                metadata={
                    'query': query,
                    'article': title,
                    'url': url,
                    'chunks': len(chunks),
                    'position': positions_used
                }
            )
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[WikiSearch] Error: {e}")
            
            return self._error_result(
                f'Search error: {str(e)}',
                metadata={'query': query},
                guidance='Check internet connection and try again'
            )
    
    def _find_article_info(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """Find best matching Wikipedia article"""
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': query,
            'srnamespace': '0',
            'srlimit': '1',
            'format': 'json',
        }
        
        try:
            r = requests.get(self.API_URL, params=params, headers=self.headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            results = data.get('query', {}).get('search', [])
            
            if results:
                top = results[0]
                return top['title'], str(top['pageid'])
        except Exception as e:
            if self._logger:
                self._logger.warning(f"[WikiSearch] Article search error: {e}")
        
        return None, None
    
    def _fetch_full_article(self, page_id: str) -> str:
        """Fetch entire article in a single request"""
        params = {
            'action': 'query',
            'prop': 'extracts',
            'pageids': page_id,
            'explaintext': '1',
            'exlimit': '1',
            'format': 'json',
            'redirects': '1',
        }
        
        try:
            r = requests.get(self.API_URL, params=params, headers=self.headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            
            if 'error' in data:
                if self._logger:
                    self._logger.warning(f"[WikiSearch] API error: {data['error']}")
                return ""
            
            pages = data.get('query', {}).get('pages', {})
            if not pages:
                return ""
            
            for page in pages.values():
                if 'extract' in page:
                    return page['extract']
        
        except Exception as e:
            if self._logger:
                self._logger.warning(f"[WikiSearch] Fetch error: {e}")
        
        return ""
    
    def _extract_context_chunks(
        self, 
        text: str, 
        query_words: Set[str], 
        article_key: str
    ) -> List[str]:
        """
        Extract contextual chunks with position tracking
        Avoids previously used positions for varied results
        """
        if not query_words or not text:
            return []
        
        # Get previously used positions for this article
        used_positions = self._position_cache.get(article_key, set())
        
        # Find all query word matches
        pattern = r'\b(' + '|'.join(re.escape(w) for w in query_words) + r')\b'
        matches = list(re.finditer(pattern, text.lower()))
        
        if not matches:
            return []
        
        # Filter out matches too close to used positions
        valid_matches = []
        for m in matches:
            mid = m.start()
            if all(abs(mid - used_pos) >= self.MIN_CHUNK_DISTANCE for used_pos in used_positions):
                valid_matches.append(m)
        
        # Reset if exhausted all positions
        if not valid_matches and used_positions:
            if self._logger:
                self._logger.tool(f"[WikiSearch] Resetting position cache for article")
            used_positions.clear()
            valid_matches = matches
        
        chunks = []
        new_positions = []
        
        for m in valid_matches:
            if len(chunks) >= self.CHUNK_GOAL:
                break
            
            mid = m.start()
            
            # Check overlap with current batch
            if any(abs(mid - pos) < self.MIN_CHUNK_DISTANCE for pos in new_positions):
                continue
            
            # Calculate chunk boundaries
            start = max(0, mid - self.CHUNK_SIZE // 2)
            end = min(len(text), start + self.CHUNK_SIZE)
            
            # Adjust if at text end
            if end - start < self.CHUNK_SIZE and start > 0:
                start = max(0, end - self.CHUNK_SIZE)
            
            chunk = text[start:end].strip()
            
            if chunk and len(chunk) > 50:
                chunks.append(chunk)
                new_positions.append(mid)
        
        # Update position cache
        if article_key not in self._position_cache:
            self._position_cache[article_key] = set()
        self._position_cache[article_key].update(new_positions)
        
        return chunks
    
    def _format_results(self, title: str, url: str, chunks: List[str]) -> str:
        """Format search results for AI consumption"""
        result = f"**{title}** (Wikipedia)\n"
        result += f"URL: {url}\n\n"
        result += "Content:\n"
        result += "\n\n".join(f"[{i+1}] {chunk}" for i, chunk in enumerate(chunks))
        return result
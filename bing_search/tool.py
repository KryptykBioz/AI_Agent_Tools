# Filename: BASE/tools/installed/bing_search/tool.py
"""
Bing Search Tool - Dual Mode Architecture
Primary: Bing Search API (official, reliable)
Fallback: Web scraping with anti-detection (when API unavailable)

ENHANCEMENTS:
- HTML entity decoding (fixes &nbsp;, &#0183;, &#32;, etc.)
- Domain diversity enforcement (each result from different source)
- Offset-based pagination (different results each call)
- Deduplication tracking (avoids repeating URLs)
"""
import asyncio
import re
import time
import random
import requests
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urlparse
from BASE.handlers.base_tool import BaseTool
import html

class BingSearchTool(BaseTool):
    """
    Bing web search with automatic fallback and result variation
    
    Mode 1: Bing Search API (requires API key)
    Mode 2: Web scraping with anti-detection (API key not configured)
    
    Features:
    - Domain diversity: Each result from a different website
    - Pagination: Each search call returns different results
    - Deduplication: Tracks seen URLs to avoid repeats
    - HTML entity decoding: Clean, readable results
    - Source attribution: Each result shows its domain
    """
    
    # Web scraping constants
    BING_URL = "https://www.bing.com/search"
    CHUNK_SIZE = 1200
    CHUNK_GOAL = 3
    
    # Diverse User-Agent pool for scraping
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    @property
    def name(self) -> str:
        return "bing"
    
    async def initialize(self) -> bool:
        """
        Initialize Bing search system
        
        Returns:
            True (always succeeds - graceful degradation to scraping)
        """
        # Get Bing API key from config
        self.api_key = getattr(self._config, 'bing_search_api_key', None)
        self.endpoint = getattr(
            self._config, 
            'bing_search_endpoint', 
            'https://api.bing.microsoft.com/v7.0/search'
        )
        
        # Initialize scraping session
        self.scrape_session = requests.Session()
        self.scrape_session.mount('https://', requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=1,
            pool_maxsize=1
        ))
        
        # Result variation tracking
        self.query_offsets = {}      # query -> current offset
        self.query_seen_urls = {}    # query -> set of seen URLs
        self.query_seen_domains = {} # query -> set of seen domains (for current batch)
        self.max_offset = 45         # Bing allows up to 50 results
        self.results_per_page = 5
        
        # Determine mode
        if self.api_key:
            mode = "API mode (official)"
        else:
            mode = "Scraping mode (fallback)"
        
        if self._logger:
            self._logger.system(f"[Bing] Search ready - {mode} with domain diversity")
        
        return True
    
    async def cleanup(self):
        """Cleanup search resources"""
        if hasattr(self, 'scrape_session'):
            self.scrape_session.close()
        
        if self._logger:
            self._logger.system("[Bing] Cleanup complete")
    
    def is_available(self) -> bool:
        """
        Check if Bing search is available
        
        Returns:
            True (always available - uses fallback if no API key)
        """
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get search system status
        
        Returns:
            Status dictionary with mode info
        """
        mode = "API" if self.api_key else "Scraping"
        
        return {
            'available': True,
            'mode': mode,
            'has_api_key': bool(self.api_key),
            'endpoint': self.endpoint if self.api_key else self.BING_URL,
            'fallback_enabled': True,
            'domain_diversity': True
        }
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute Bing search command
        
        Commands:
        - search: [query: str] - Search the web for information
        - reset: [query: str | None] - Reset tracking for query (or all queries)
        
        Args:
            command: Command name ('search' or 'reset')
            args: Command arguments
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[Bing] Command: '{command}', args: {args}")
        
        # Default to search
        if not command:
            command = 'search'
        
        try:
            # Route to handler
            if command == 'search':
                return await self._handle_search_command(args)
            elif command == 'reset':
                return await self._handle_reset_command(args)
            else:
                return self._error_result(
                    f'Unknown command: {command}',
                    guidance='Available commands: search, reset'
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
        Handle search command with automatic API/scraping fallback
        
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
        
        query = str(args[0]).strip()
        
        if not query:
            return self._error_result(
                'Empty search query',
                guidance='Provide a non-empty search query'
            )
        
        if self._logger:
            self._logger.tool(f"[Bing] Searching: '{query}'")
        
        # Try API first if available
        if self.api_key:
            results = await self._search_api(query)
            
            # If API succeeds, return results
            if results:
                return self._format_success_result(query, results, source="API")
            
            # API failed - fall back to scraping
            if self._logger:
                self._logger.warning("[Bing] API failed, falling back to scraping")
        
        # Use scraping (either no API key or API failed)
        results = await self._search_scrape(query)
        
        if results:
            return self._format_success_result(query, results, source="scraping")
        else:
            if self._logger:
                self._logger.warning(f"[Bing] No results found for: '{query}'")
            
            return self._error_result(
                f'No results found for query: {query}',
                metadata={'query': query},
                guidance='Try different search terms or broader query'
            )
    
    async def _handle_reset_command(self, args: List[Any]) -> Dict[str, Any]:
        """
        Handle reset command - clears tracking for a query
        
        Args:
            args: [query] or [] to reset all
            
        Returns:
            Success result
        """
        query = str(args[0]).strip() if args else None
        
        if query:
            # Reset specific query
            self.query_offsets.pop(query, None)
            self.query_seen_urls.pop(query, None)
            self.query_seen_domains.pop(query, None)
            
            if self._logger:
                self._logger.system(f"[Bing] Reset tracking for query: '{query}'")
            
            return self._success_result(
                f"Reset tracking for query: {query}",
                metadata={'query': query}
            )
        else:
            # Reset all queries
            self.query_offsets.clear()
            self.query_seen_urls.clear()
            self.query_seen_domains.clear()
            
            if self._logger:
                self._logger.system("[Bing] Reset tracking for all queries")
            
            return self._success_result(
                "Reset tracking for all queries",
                metadata={'reset': 'all'}
            )
    
    def _format_success_result(
        self, 
        query: str, 
        results: str, 
        source: str
    ) -> Dict[str, Any]:
        """Format successful search result"""
        # Count results
        result_count = len(results.split('\n\n'))
        
        if self._logger:
            self._logger.success(
                f"[Bing] Search completed: {result_count} results ({source}, diverse domains)"
            )
        
        return self._success_result(
            results,
            metadata={
                'query': query,
                'result_count': result_count,
                'source': source,
                'domain_diversity': True
            }
        )
    
    def _extract_domain(self, url: str) -> str:
        """
        Extract clean domain from URL
        
        Args:
            url: Full URL
            
        Returns:
            Domain string (e.g., 'example.com')
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Remove 'www.' prefix for consistency
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain
        except:
            return url
    
    # ========================================================================
    # API MODE - Official Bing Search API with Domain Diversity
    # ========================================================================
    
    async def _search_api(self, query: str) -> str:
        """
        Search using official Bing Search API with domain diversity enforcement
        
        Features:
        - Domain diversity: Each result from a different website
        - Pagination: Each call returns next 5 results
        - Deduplication: Tracks seen URLs to avoid repeats
        - Auto-wrap: Resets to page 1 after exhausting results
        
        Args:
            query: Search query
            
        Returns:
            Formatted results or empty string on failure
        """
        try:
            # Get current offset for this query
            current_offset = self.query_offsets.get(query, 0)
            
            # Track seen URLs for deduplication
            if query not in self.query_seen_urls:
                self.query_seen_urls[query] = set()
            seen_urls = self.query_seen_urls[query]
            
            # Initialize domain tracking for this batch (resets each call)
            batch_domains = set()
            
            # Prepare API request - fetch more results for domain filtering
            headers = {'Ocp-Apim-Subscription-Key': self.api_key}
            params = {
                'q': query,
                'count': 20,  # Fetch extra to ensure domain diversity
                'offset': current_offset,
                'textDecorations': False,
                'textFormat': 'Raw'
            }
            
            if self._logger:
                page_num = (current_offset // self.results_per_page) + 1
                self._logger.tool(
                    f"[Bing] API call - page {page_num} (offset {current_offset})"
                )
            
            response = requests.get(
                self.endpoint,
                headers=headers,
                params=params,
                timeout=25
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Process results with domain diversity enforcement
            if 'webPages' in data and 'value' in data['webPages']:
                all_results = data['webPages']['value']
                
                # Filter for diverse domains and deduplicate URLs
                diverse_results = []
                
                for item in all_results:
                    url = item.get('url', '')
                    
                    # Skip if URL already seen
                    if url in seen_urls:
                        continue
                    
                    # Extract domain
                    domain = self._extract_domain(url)
                    
                    # Skip if domain already used in this batch
                    if domain in batch_domains:
                        continue
                    
                    # Accept this result
                    diverse_results.append(item)
                    seen_urls.add(url)
                    batch_domains.add(domain)
                    
                    # Stop when we have enough diverse results
                    if len(diverse_results) >= self.results_per_page:
                        break
                
                # If we couldn't find enough diverse results, fill with duplicates
                if len(diverse_results) < self.results_per_page:
                    if self._logger:
                        self._logger.warning(
                            f"[Bing] Only found {len(diverse_results)} diverse domains, "
                            f"filling with any available results"
                        )
                    
                    for item in all_results:
                        if len(diverse_results) >= self.results_per_page:
                            break
                        
                        url = item.get('url', '')
                        if url not in seen_urls:
                            diverse_results.append(item)
                            seen_urls.add(url)
                
                # Update offset for next call
                next_offset = current_offset + 20
                if next_offset > self.max_offset or len(diverse_results) < self.results_per_page:
                    # Wrapped to beginning or exhausted results - reset tracking
                    next_offset = 0
                    seen_urls.clear()
                    if self._logger:
                        self._logger.system(
                            f"[Bing] Query '{query}' exhausted results, wrapping to page 1"
                        )
                
                self.query_offsets[query] = next_offset
                
                # Format results with domain attribution
                results = []
                for i, item in enumerate(diverse_results, 1):
                    # Get raw values
                    title = item.get('name', 'No title')
                    snippet = item.get('snippet', 'No description')
                    url = item.get('url', '')
                    
                    # Clean HTML entities
                    title = html.unescape(title)
                    snippet = html.unescape(snippet)
                    
                    # Normalize whitespace
                    title = ' '.join(title.split())
                    snippet = ' '.join(snippet.split())
                    
                    # Extract domain for display
                    domain = self._extract_domain(url)
                    
                    # Format with result number and source domain
                    result_num = current_offset + i
                    result_entry = (
                        f"{result_num}. {title}\n"
                        f"{snippet}\n"
                        f"Source: {domain}\n"
                        f"URL: {url}"
                    )
                    results.append(result_entry)
                
                if self._logger and diverse_results:
                    domains = [self._extract_domain(r.get('url', '')) for r in diverse_results]
                    self._logger.system(
                        f"[Bing] Domains in results: {', '.join(domains)}"
                    )
                
                return "\n\n".join(results)
            
            return ""
        
        except Exception as e:
            if self._logger:
                self._logger.warning(f"[Bing] API error: {e}")
            return ""
    
    # ========================================================================
    # SCRAPING MODE - Anti-Detection Web Scraping
    # ========================================================================
    
    async def _search_scrape(self, query: str) -> str:
        """
        Search using web scraping with anti-detection
        
        Args:
            query: Search query
            
        Returns:
            Formatted results or empty string on failure
        """
        if self._logger:
            self._logger.tool("[Bing] Using scraping mode...")
        
        # Extract query words for context matching
        query_words = {
            w for w in re.findall(r'\b\w+\b', query.lower()) 
            if len(w) >= 3
        }
        
        # Try up to 3 times with progressive backoff
        html_content = None
        for attempt in range(3):
            html_content = await self._scrape_attempt(query, attempt)
            if html_content:
                break
            
            if attempt < 2 and self._logger:
                self._logger.tool(f"[Bing] Retry {attempt + 2}/3...")
        
        if not html_content:
            if self._logger:
                self._logger.warning("[Bing] All scraping attempts failed")
            return ""
        
        # Clean and extract content
        cleaned_text = self._clean_html(html_content)
        
        if not cleaned_text:
            return ""
        
        # Validate query words appear
        if query_words:
            cleaned_lower = cleaned_text.lower()
            found = sum(1 for w in query_words if w in cleaned_lower)
            if found == 0:
                if self._logger:
                    self._logger.warning("[Bing] Query words not in results")
                return ""
        
        # Extract contextual chunks
        chunks = self._extract_context_chunks(cleaned_text, query_words)
        
        if not chunks:
            return ""
        
        # Format as numbered results (scraping mode can't extract individual sources easily)
        formatted_chunks = []
        for i, chunk in enumerate(chunks, 1):
            formatted_chunks.append(
                f"{i}. {chunk}\n"
                f"Source: bing.com (scraped)"
            )
        
        return "\n\n".join(formatted_chunks)
    
    async def _scrape_attempt(
        self, 
        query: str, 
        attempt: int
    ) -> Optional[str]:
        """
        Single scraping attempt with anti-detection
        
        Args:
            query: Search query
            attempt: Attempt number
            
        Returns:
            HTML content or None
        """
        params = {
            'q': query,
            'form': 'QBLH',
            'sp': '-1',
            'pq': query[:20],
            'sc': '10-0',
            'qs': 'n',
            'sk': '',
            'cvid': ''.join(random.choices('0123456789ABCDEF', k=32))
        }
        
        headers = self._get_scrape_headers()
        
        # Progressive delay
        if attempt > 0:
            delay = min(2 ** attempt + random.uniform(0, 1), 10)
            await asyncio.sleep(delay)
        
        try:
            # Run synchronous request in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.scrape_session.get(
                    self.BING_URL,
                    params=params,
                    headers=headers,
                    timeout=15,
                    allow_redirects=True
                )
            )
            
            # Handle status codes
            if response.status_code in (202, 400, 429):
                return None
            
            response.raise_for_status()
            html = response.text
            
            # Validate response
            if len(html) < 1000:
                return None
            
            # Check for blocks
            html_lower = html.lower()
            block_indicators = [
                'unusual traffic', 'captcha', 'verify you are human',
                'security check', 'blocked'
            ]
            if any(ind in html_lower for ind in block_indicators):
                return None
            
            # Check for results
            if 'id="b_results"' not in html and 'class="b_algo"' not in html:
                return None
            
            return html
        
        except Exception as e:
            if self._logger and attempt == 0:
                self._logger.tool(f"[Bing] Scrape error: {str(e)[:50]}")
            return None
    
    def _get_scrape_headers(self) -> dict:
        """Generate realistic browser headers"""
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    def _clean_html(self, html_content: str) -> str:
        """
        Remove HTML tags and clean text
        
        Handles:
        - Script/style/head removal
        - HTML tag stripping  
        - HTML entity decoding (&nbsp;, &#32;, &#0183;, &quot;, &#237;, etc.)
        - Whitespace normalization
        - Empty line removal
        
        Args:
            html_content: Raw HTML string
            
        Returns:
            Cleaned, readable text
        """
        # Remove scripts, styles, metadata
        content = re.sub(
            r'<script[^>]*>.*?</script>', '', html_content, 
            flags=re.DOTALL | re.IGNORECASE
        )
        content = re.sub(
            r'<style[^>]*>.*?</style>', '', content, 
            flags=re.DOTALL | re.IGNORECASE
        )
        content = re.sub(
            r'<head[^>]*>.*?</head>', '', content, 
            flags=re.DOTALL | re.IGNORECASE
        )
        
        # Remove HTML tags
        cleaned = re.sub(r'<[^>]+>', ' ', content)
        
        # Decode HTML entities (&nbsp; &#32; &#0183; &quot; &#237; etc.)
        cleaned = html.unescape(cleaned)
        
        # Normalize whitespace
        cleaned = re.sub(r'[ \t]{2,}', ' ', cleaned)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Clean lines
        lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
        
        return '\n'.join(lines)
    
    def _extract_context_chunks(
        self, 
        text: str, 
        query_words: Set[str]
    ) -> List[str]:
        """
        Extract contextual chunks around query word matches
        
        Args:
            text: Cleaned text
            query_words: Set of query words to match
            
        Returns:
            List of relevant text chunks
        """
        if not query_words or not text:
            return []
        
        # Build regex pattern
        pattern = r'\b(' + '|'.join(re.escape(w) for w in query_words) + r')\b'
        matches = list(re.finditer(pattern, text.lower()))
        
        if not matches:
            return []
        
        chunks = []
        used_positions = set()
        
        for match in matches:
            if len(chunks) >= self.CHUNK_GOAL:
                break
            
            mid = match.start()
            
            # Avoid overlapping chunks
            if any(abs(mid - pos) < 300 for pos in used_positions):
                continue
            
            # Extract chunk
            start = max(0, mid - self.CHUNK_SIZE // 2)
            end = min(len(text), start + self.CHUNK_SIZE)
            
            # Adjust if at end
            if end - start < self.CHUNK_SIZE and start > 0:
                start = max(0, end - self.CHUNK_SIZE)
            
            chunk = text[start:end].strip()
            
            if chunk and len(chunk) > 50:
                chunks.append(chunk)
                used_positions.add(mid)
        
        return chunks


# Testing
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Mock minimal config and logger
    class MockConfig:
        bing_search_api_key = None  # Set to test API mode
        bing_search_endpoint = 'https://api.bing.microsoft.com/v7.0/search'
    
    class MockLogger:
        def system(self, msg): print(f"[SYS] {msg}")
        def tool(self, msg): print(f"[TOOL] {msg}")
        def success(self, msg): print(f"[OK] {msg}")
        def warning(self, msg): print(f"[WARN] {msg}")
        def error(self, msg): print(f"[ERR] {msg}")
    
    async def test():
        print("=" * 70)
        print("Bing Search Tool Test (with domain diversity)")
        print("=" * 70)
        
        tool = BingSearchTool(MockConfig(), None, MockLogger())
        
        await tool.initialize()
        
        status = tool.get_status()
        print(f"\nStatus: {status}")
        
        print("\nFeatures:")
        print("  • Domain diversity: Each result from different website")
        print("  • Pagination: Same query returns different results each time")
        print("  • Source attribution: Each result shows its domain")
        print("\nTip: Search the same query multiple times to see pagination!")
        print("Commands: 'reset <query>' to reset pagination for a query")
        
        while True:
            try:
                q = input("\nEnter search query (or press Enter to exit): ").strip()
                if not q:
                    print("\nExiting...")
                    break
                
                # Check for reset command
                if q.startswith('reset '):
                    query = q[6:].strip()
                    result = await tool.execute('reset', [query] if query else [])
                    print(f"\n{result['content']}")
                    continue
                
                print("\n" + "=" * 70)
                
                result = await tool.execute('search', [q])
                
                if result['success']:
                    print("\nResults:")
                    print("-" * 70)
                    print(result['content'])
                    print("-" * 70)
                    print(f"\nMetadata: {result.get('metadata', {})}")
                else:
                    print(f"\nError: {result['content']}")
                
                print("=" * 70)
            
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"\nError: {e}")
        
        await tool.cleanup()
    
    asyncio.run(test())
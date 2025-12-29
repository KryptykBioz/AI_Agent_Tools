# Filename: BASE/tools/installed/duckduckgo_search/tool.py
"""
DuckDuckGo Search Tool - Privacy-Focused Web Search
Uses DuckDuckGo's HTML search for reliable, ad-free results

FEATURES:
- HTML entity decoding (fixes &nbsp;, &#0183;, &#32;, etc.)
- Domain diversity enforcement (each result from different source)
- Offset-based pagination (different results each call)
- Deduplication tracking (avoids repeating URLs)
- Privacy-focused (no tracking, no API key required)
"""
import asyncio
import re
import time
import random
import requests
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urlparse, quote_plus
from BASE.handlers.base_tool import BaseTool
import html


class DuckDuckGoSearchTool(BaseTool):
    """
    DuckDuckGo web search with privacy focus and result variation
    
    Features:
    - No API key required (uses HTML scraping)
    - Domain diversity: Each result from a different website
    - Pagination: Each search call returns different results
    - Deduplication: Tracks seen URLs to avoid repeats
    - HTML entity decoding: Clean, readable results
    - Source attribution: Each result shows its domain
    - Privacy-focused: No tracking or user profiling
    """
    
    # DuckDuckGo search constants
    DDG_URL = "https://html.duckduckgo.com/html/"
    RESULTS_PER_PAGE = 5
    MAX_PAGES = 10  # DuckDuckGo provides ~10 pages
    
    # Diverse User-Agent pool
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
        return "duckduckgo"
    
    async def initialize(self) -> bool:
        """
        Initialize DuckDuckGo search system
        
        Returns:
            True (always succeeds - no API key required)
        """
        # Initialize session
        self.session = requests.Session()
        self.session.mount('https://', requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=1,
            pool_maxsize=1
        ))
        
        # Result variation tracking
        self.query_offsets = {}      # query -> current page offset
        self.query_seen_urls = {}    # query -> set of seen URLs
        self.query_seen_domains = {} # query -> set of seen domains (for current batch)
        
        if self._logger:
            self._logger.system(
                "[DuckDuckGo] Search ready - privacy-focused with domain diversity"
            )
        
        return True
    
    async def cleanup(self):
        """Cleanup search resources"""
        if hasattr(self, 'session'):
            self.session.close()
        
        if self._logger:
            self._logger.system("[DuckDuckGo] Cleanup complete")
    
    def is_available(self) -> bool:
        """
        Check if DuckDuckGo search is available
        
        Returns:
            True (always available - no API key required)
        """
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get search system status
        
        Returns:
            Status dictionary
        """
        return {
            'available': True,
            'mode': 'HTML Scraping',
            'requires_api_key': False,
            'endpoint': self.DDG_URL,
            'privacy_focused': True,
            'domain_diversity': True
        }
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute DuckDuckGo search command
        
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
            self._logger.tool(f"[DuckDuckGo] Command: '{command}', args: {args}")
        
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
                self._logger.error(f"[DuckDuckGo] Command execution error: {e}")
            import traceback
            traceback.print_exc()
            
            return self._error_result(
                f'Command execution failed: {str(e)}',
                metadata={'error': str(e)},
                guidance='Check logs for details'
            )
    
    async def _handle_search_command(self, args: List[Any]) -> Dict[str, Any]:
        """
        Handle search command
        
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
            self._logger.tool(f"[DuckDuckGo] Searching: '{query}'")
        
        # Perform search
        results = await self._search(query)
        
        if results:
            # Count results
            result_count = len(results.split('\n\n'))
            
            if self._logger:
                self._logger.success(
                    f"[DuckDuckGo] Search completed: {result_count} results (diverse domains)"
                )
            
            return self._success_result(
                results,
                metadata={
                    'query': query,
                    'result_count': result_count,
                    'source': 'DuckDuckGo',
                    'domain_diversity': True
                }
            )
        else:
            if self._logger:
                self._logger.warning(f"[DuckDuckGo] No results found for: '{query}'")
            
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
                self._logger.system(f"[DuckDuckGo] Reset tracking for query: '{query}'")
            
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
                self._logger.system("[DuckDuckGo] Reset tracking for all queries")
            
            return self._success_result(
                "Reset tracking for all queries",
                metadata={'reset': 'all'}
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
    # SEARCH IMPLEMENTATION - HTML Scraping with Domain Diversity
    # ========================================================================
    
    async def _search(self, query: str) -> str:
        """
        Search DuckDuckGo with domain diversity enforcement
        
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
        # Get current offset for this query
        current_offset = self.query_offsets.get(query, 0)
        
        # Track seen URLs for deduplication
        if query not in self.query_seen_urls:
            self.query_seen_urls[query] = set()
        seen_urls = self.query_seen_urls[query]
        
        # Initialize domain tracking for this batch (resets each call)
        batch_domains = set()
        
        # Try to get results
        html_content = await self._fetch_search_page(query, current_offset)
        
        if not html_content:
            return ""
        
        # Parse results from HTML
        raw_results = self._parse_results(html_content)
        
        if not raw_results:
            return ""
        
        # Filter for diverse domains and deduplicate URLs
        diverse_results = []
        
        for result in raw_results:
            url = result.get('url', '')
            
            # Skip if URL already seen
            if url in seen_urls:
                continue
            
            # Extract domain
            domain = self._extract_domain(url)
            
            # Skip if domain already used in this batch
            if domain in batch_domains:
                continue
            
            # Accept this result
            diverse_results.append(result)
            seen_urls.add(url)
            batch_domains.add(domain)
            
            # Stop when we have enough diverse results
            if len(diverse_results) >= self.RESULTS_PER_PAGE:
                break
        
        # If we couldn't find enough diverse results, fill with any available
        if len(diverse_results) < self.RESULTS_PER_PAGE:
            if self._logger:
                self._logger.warning(
                    f"[DuckDuckGo] Only found {len(diverse_results)} diverse domains, "
                    f"filling with any available results"
                )
            
            for result in raw_results:
                if len(diverse_results) >= self.RESULTS_PER_PAGE:
                    break
                
                url = result.get('url', '')
                if url not in seen_urls:
                    diverse_results.append(result)
                    seen_urls.add(url)
        
        # Update offset for next call
        next_offset = current_offset + 1
        if next_offset >= self.MAX_PAGES or len(diverse_results) < self.RESULTS_PER_PAGE:
            # Wrapped to beginning or exhausted results - reset tracking
            next_offset = 0
            seen_urls.clear()
            if self._logger:
                self._logger.system(
                    f"[DuckDuckGo] Query '{query}' exhausted results, wrapping to page 1"
                )
        
        self.query_offsets[query] = next_offset
        
        # Format results with domain attribution
        formatted_results = []
        for i, result in enumerate(diverse_results, 1):
            title = result.get('title', 'No title')
            snippet = result.get('snippet', 'No description')
            url = result.get('url', '')
            
            # Extract domain for display
            domain = self._extract_domain(url)
            
            # Format with result number and source domain
            result_num = (current_offset * self.RESULTS_PER_PAGE) + i
            result_entry = (
                f"{result_num}. {title}\n"
                f"{snippet}\n"
                f"Source: {domain}\n"
                f"URL: {url}"
            )
            formatted_results.append(result_entry)
        
        if self._logger and diverse_results:
            domains = [self._extract_domain(r.get('url', '')) for r in diverse_results]
            self._logger.system(
                f"[DuckDuckGo] Domains in results: {', '.join(domains)}"
            )
        
        return "\n\n".join(formatted_results)
    
    async def _fetch_search_page(self, query: str, page_offset: int) -> Optional[str]:
        """
        Fetch search results page from DuckDuckGo
        
        Args:
            query: Search query
            page_offset: Page number (0-indexed)
            
        Returns:
            HTML content or None on failure
        """
        try:
            # Prepare POST data (DuckDuckGo uses POST for HTML search)
            data = {
                'q': query,
                'b': '',  # Empty for first page
                'kl': 'us-en',
                'df': ''
            }
            
            # Add pagination parameter if not first page
            if page_offset > 0:
                # DuckDuckGo pagination works via form token, but we can approximate
                # by adding more results parameter
                data['s'] = str(page_offset * 30)  # Approximate offset
            
            headers = {
                'User-Agent': random.choice(self.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://duckduckgo.com',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            if self._logger:
                page_num = page_offset + 1
                self._logger.tool(f"[DuckDuckGo] Fetching page {page_num}...")
            
            # Small delay to be respectful
            if page_offset > 0:
                await asyncio.sleep(random.uniform(1.0, 2.0))
            
            # Make request
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.post(
                    self.DDG_URL,
                    data=data,
                    headers=headers,
                    timeout=20
                )
            )
            
            response.raise_for_status()
            
            if len(response.text) < 500:
                return None
            
            return response.text
        
        except Exception as e:
            if self._logger:
                self._logger.warning(f"[DuckDuckGo] Fetch error: {e}")
            return None
    
    def _parse_results(self, html_content: str) -> List[Dict[str, str]]:
        """
        Parse search results from DuckDuckGo HTML
        
        Args:
            html_content: Raw HTML from DuckDuckGo
            
        Returns:
            List of result dicts with title, snippet, url
        """
        results = []
        
        try:
            # DuckDuckGo HTML structure uses <div class="result results_links...">
            # Title in <a class="result__a">
            # Snippet in <a class="result__snippet">
            # URL in <a class="result__url">
            
            # Find all result blocks
            result_pattern = r'<div[^>]*class="result[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>'
            result_blocks = re.findall(result_pattern, html_content, re.DOTALL)
            
            for block in result_blocks[:20]:  # Get extra for filtering
                # Extract title
                title_match = re.search(
                    r'<a[^>]*class="result__a"[^>]*>(.*?)</a>',
                    block,
                    re.DOTALL
                )
                title = ''
                if title_match:
                    title = self._clean_html(title_match.group(1))
                
                # Extract snippet
                snippet_match = re.search(
                    r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                    block,
                    re.DOTALL
                )
                snippet = ''
                if snippet_match:
                    snippet = self._clean_html(snippet_match.group(1))
                
                # Extract URL
                url_match = re.search(
                    r'<a[^>]*class="result__url"[^>]*href="([^"]+)"',
                    block
                )
                url = ''
                if url_match:
                    url = url_match.group(1)
                    # DuckDuckGo sometimes uses redirect URLs, extract real URL
                    if 'uddg=' in url:
                        real_url_match = re.search(r'uddg=([^&]+)', url)
                        if real_url_match:
                            from urllib.parse import unquote
                            url = unquote(real_url_match.group(1))
                
                if title and url:
                    results.append({
                        'title': title,
                        'snippet': snippet if snippet else 'No description available',
                        'url': url
                    })
            
            return results
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[DuckDuckGo] Parse error: {e}")
            return []
    
    def _clean_html(self, text: str) -> str:
        """
        Remove HTML tags and clean text
        
        Handles:
        - HTML tag stripping  
        - HTML entity decoding (&nbsp;, &#32;, &#0183;, &quot;, &#237;, etc.)
        - Whitespace normalization
        
        Args:
            text: Raw HTML string
            
        Returns:
            Cleaned, readable text
        """
        # Remove HTML tags
        cleaned = re.sub(r'<[^>]+>', ' ', text)
        
        # Decode HTML entities (&nbsp; &#32; &#0183; &quot; &#237; etc.)
        cleaned = html.unescape(cleaned)
        
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()


# Testing
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Mock minimal config and logger
    class MockConfig:
        pass
    
    class MockLogger:
        def system(self, msg): print(f"[SYS] {msg}")
        def tool(self, msg): print(f"[TOOL] {msg}")
        def success(self, msg): print(f"[OK] {msg}")
        def warning(self, msg): print(f"[WARN] {msg}")
        def error(self, msg): print(f"[ERR] {msg}")
    
    async def test():
        print("=" * 70)
        print("DuckDuckGo Search Tool Test (with domain diversity)")
        print("=" * 70)
        
        tool = DuckDuckGoSearchTool(MockConfig(), None, MockLogger())
        
        await tool.initialize()
        
        status = tool.get_status()
        print(f"\nStatus: {status}")
        
        print("\nFeatures:")
        print("  • Privacy-focused: No tracking or user profiling")
        print("  • No API key required: Uses HTML scraping")
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
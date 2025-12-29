# Filename: BASE/tools/installed/web_fetch/tool.py
"""
Web Fetch Tool - Safe webpage retrieval with domain whitelist
Supports plaintext, markdown, and PDF output formats
"""
import asyncio
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from BASE.handlers.base_tool import BaseTool
import requests
from bs4 import BeautifulSoup
import random


class WebFetchTool(BaseTool):
    """
    Safe web page retrieval with domain whitelist
    Supports multiple output formats: text, markdown, PDF
    """
    
    # Configurable approved domains
    APPROVED_DOMAINS = [
        'wikipedia.org',
        'github.com',
        'docs.python.org',
        'stackoverflow.com',
        'reddit.com',
        'arxiv.org',
        'medium.com',
        'dev.to',
        'hackernews.com'
    ]
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    ]
    
    MAX_SIZE_MB = 10
    TIMEOUT_SECONDS = 30
    
    @property
    def name(self) -> str:
        return "web_fetch"
    
    async def initialize(self) -> bool:
        """Initialize web fetch system"""
        self.max_size_bytes = self.MAX_SIZE_MB * 1024 * 1024
        
        self.headers = {
            'User-Agent': f'WebFetchAgent/1.0 ({random.choice(self.USER_AGENTS)})',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        if self._logger:
            self._logger.system(
                f"[WebFetch] Initialized - {len(self.APPROVED_DOMAINS)} approved domains"
            )
        
        return True
    
    async def cleanup(self):
        """Cleanup resources"""
        if self._logger:
            self._logger.system("[WebFetch] Cleaned up")
    
    def is_available(self) -> bool:
        """Check if web fetch is available"""
        return True
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """
        Execute web fetch command
        
        Commands:
        - fetch: Fetch webpage (default)
        - list_domains: List approved domains
        
        Args:
            command: Command name ('fetch', 'list_domains')
            args: Command arguments
            
        Returns:
            Standardized result dict
        """
        if self._logger:
            self._logger.tool(f"[WebFetch] Command: '{command}', args: {args}")
        
        # List approved domains
        if command == 'list_domains':
            return self._list_approved_domains()
        
        # Fetch webpage (default command)
        if command in ['fetch', '']:
            if not args:
                return self._error_result(
                    'No URL provided',
                    guidance='Provide a URL: {"tool": "web_fetch.fetch", "args": ["https://example.com"]}'
                )
            
            url = str(args[0]).strip()
            output_format = str(args[1]).lower() if len(args) > 1 else 'text'
            
            if not url:
                return self._error_result(
                    'Empty URL',
                    guidance='Provide a valid URL'
                )
            
            # Validate format
            if output_format not in ['text', 'markdown', 'pdf']:
                return self._error_result(
                    f'Invalid format: {output_format}',
                    guidance='Valid formats: text, markdown, pdf'
                )
            
            return await self._fetch_webpage(url, output_format)
        
        return self._error_result(
            f'Unknown command: {command}',
            guidance='Available commands: fetch, list_domains'
        )
    
    def _list_approved_domains(self) -> Dict[str, Any]:
        """List all approved domains"""
        domain_list = "\n".join([f"- {domain}" for domain in sorted(self.APPROVED_DOMAINS)])
        
        content = f"**Approved Domains ({len(self.APPROVED_DOMAINS)})**\n\n{domain_list}\n\n"
        content += "Any page from these domains can be fetched.\n"
        content += "Formats available: text, markdown, pdf"
        
        if self._logger:
            self._logger.success(f"[WebFetch] Listed {len(self.APPROVED_DOMAINS)} approved domains")
        
        return self._success_result(
            content,
            metadata={
                'domain_count': len(self.APPROVED_DOMAINS),
                'domains': self.APPROVED_DOMAINS
            }
        )
    
    async def _fetch_webpage(self, url: str, output_format: str) -> Dict[str, Any]:
        """
        Fetch webpage with specified output format
        
        Args:
            url: URL to fetch
            output_format: 'text', 'markdown', or 'pdf'
            
        Returns:
            Result dict with webpage content
        """
        try:
            # Validate URL format
            if not url.startswith(('http://', 'https://')):
                return self._error_result(
                    'Invalid URL format - must start with http:// or https://',
                    metadata={'url': url},
                    guidance='Provide a complete URL with protocol'
                )
            
            # Check domain whitelist
            if not self._is_domain_allowed(url):
                domain = urlparse(url).netloc
                return self._error_result(
                    f'Domain not approved: {domain}',
                    metadata={'url': url, 'domain': domain},
                    guidance='Use list_domains command to see approved domains'
                )
            
            if self._logger:
                self._logger.tool(f"[WebFetch] Fetching: {url} (format: {output_format})")
            
            # Fetch based on format
            if output_format == 'pdf':
                content = await self._fetch_as_pdf(url)
                format_label = "PDF"
            elif output_format == 'markdown':
                content = await self._fetch_as_markdown(url)
                format_label = "Markdown"
            else:
                content = await self._fetch_as_text(url)
                format_label = "Plain Text"
            
            if not content:
                return self._error_result(
                    f'Failed to retrieve content from {url}',
                    metadata={'url': url, 'format': output_format},
                    guidance='Check URL validity and try again'
                )
            
            # Format result
            result_content = f"**Web Page Retrieved**\n"
            result_content += f"URL: {url}\n"
            result_content += f"Format: {format_label}\n"
            result_content += f"Size: {len(content)} characters\n\n"
            result_content += f"---\n\n{content}"
            
            if self._logger:
                self._logger.success(
                    f"[WebFetch] Retrieved {len(content)} chars from {urlparse(url).netloc}"
                )
            
            return self._success_result(
                result_content,
                metadata={
                    'url': url,
                    'format': output_format,
                    'size': len(content),
                    'domain': urlparse(url).netloc
                }
            )
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[WebFetch] Error: {e}")
            
            return self._error_result(
                f'Fetch error: {str(e)}',
                metadata={'url': url, 'format': output_format},
                guidance='Check internet connection and URL validity'
            )
    
    def _is_domain_allowed(self, url: str) -> bool:
        """Check if URL domain is in approved list"""
        try:
            domain = urlparse(url).netloc.lower()
            
            # Check if domain or any parent domain is approved
            for approved in self.APPROVED_DOMAINS:
                if approved.lower() in domain or domain.endswith(approved.lower()):
                    return True
            
            return False
        except:
            return False
    
    async def _fetch_as_text(self, url: str) -> str:
        """Fetch page as clean plain text with smart extraction"""
        try:
            # Try playwright first for JS-heavy sites (Reddit, modern sites)
            domain = urlparse(url).netloc.lower()
            needs_js = any(x in domain for x in ['reddit.com', 'twitter.com', 'x.com', 'medium.com'])
            
            if needs_js:
                try:
                    return await self._fetch_with_playwright(url, format='text')
                except ImportError:
                    if self._logger:
                        self._logger.warning("[WebFetch] Playwright not available, using fallback")
                except Exception as e:
                    if self._logger:
                        self._logger.warning(f"[WebFetch] Playwright failed: {e}, using fallback")
            
            # Standard fetch for static sites
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.TIMEOUT_SECONDS
            )
            response.raise_for_status()
            
            # Check size
            if len(response.content) > self.max_size_bytes:
                raise ValueError(f"Page too large (>{self.MAX_SIZE_MB}MB)")
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'iframe', 'aside', 'header']):
                tag.decompose()
            
            # Try to find main content area
            main_content = None
            for selector in ['main', 'article', '[role="main"]', '.content', '#content']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # Use main content if found, otherwise whole body
            content_source = main_content if main_content else soup.body
            if not content_source:
                content_source = soup
            
            # Extract text
            text = content_source.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            clean_text = '\n'.join(lines)
            
            # If result is too short, might be JS-rendered
            if len(clean_text) < 500 and needs_js:
                if self._logger:
                    self._logger.warning("[WebFetch] Content appears JS-rendered, consider installing playwright")
            
            return clean_text
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[WebFetch] Text fetch error: {e}")
            return ""
    
    async def _fetch_as_markdown(self, url: str) -> str:
        """Fetch page converted to markdown with smart extraction"""
        try:
            # Try playwright first for JS-heavy sites
            domain = urlparse(url).netloc.lower()
            needs_js = any(x in domain for x in ['reddit.com', 'twitter.com', 'x.com', 'medium.com'])
            
            if needs_js:
                try:
                    return await self._fetch_with_playwright(url, format='markdown')
                except ImportError:
                    if self._logger:
                        self._logger.warning("[WebFetch] Playwright not available for JS-heavy site")
                except Exception as e:
                    if self._logger:
                        self._logger.warning(f"[WebFetch] Playwright failed: {e}")
            
            # Standard fetch
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.TIMEOUT_SECONDS
            )
            response.raise_for_status()
            
            # Check size
            if len(response.content) > self.max_size_bytes:
                raise ValueError(f"Page too large (>{self.MAX_SIZE_MB}MB)")
            
            # Try to use html2text if available
            try:
                import html2text
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = False
                h.body_width = 0  # Don't wrap lines
                h.ignore_emphasis = False
                markdown = h.handle(response.text)
                return markdown
            except ImportError:
                # Fallback to basic text extraction
                if self._logger:
                    self._logger.warning("[WebFetch] html2text not available, using basic text")
                return await self._fetch_as_text(url)
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[WebFetch] Markdown fetch error: {e}")
            return ""
    
    async def _fetch_as_pdf(self, url: str) -> str:
        """Fetch page rendered as PDF with Playwright"""
        try:
            return await self._fetch_with_playwright(url, format='pdf')
        
        except ImportError:
            if self._logger:
                self._logger.warning("[WebFetch] Playwright not available, falling back to text")
            return await self._fetch_as_text(url)
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[WebFetch] PDF fetch error: {e}")
            return ""
    
    async def _fetch_with_playwright(self, url: str, format: str = 'text') -> str:
        """
        Fetch page using Playwright for JS-rendered content
        
        Args:
            url: URL to fetch
            format: 'text', 'markdown', or 'pdf'
            
        Returns:
            Extracted content in requested format
        """
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=random.choice(self.USER_AGENTS)
            )
            page = await context.new_page()
            
            # Set timeout
            page.set_default_timeout(self.TIMEOUT_SECONDS * 1000)
            
            try:
                # Navigate and wait for content
                await page.goto(url, wait_until='networkidle')
                
                # Wait a bit for dynamic content
                await page.wait_for_timeout(2000)
                
                if format == 'pdf':
                    # Generate PDF
                    pdf_bytes = await page.pdf(format='A4')
                    await browser.close()
                    
                    # Return description
                    return f"[PDF Generated: {len(pdf_bytes)} bytes]\n\nNote: PDF generation successful. The page has been rendered to PDF format."
                
                elif format == 'markdown':
                    # Get HTML content
                    html_content = await page.content()
                    
                    # Convert to markdown
                    try:
                        import html2text
                        h = html2text.HTML2Text()
                        h.ignore_links = False
                        h.ignore_images = False
                        h.body_width = 0
                        markdown = h.handle(html_content)
                        
                        await browser.close()
                        return markdown
                    except ImportError:
                        # Fall through to text extraction
                        pass
                
                # Text extraction (default)
                # Try to get main content
                main_selectors = [
                    'main',
                    'article',
                    '[role="main"]',
                    '.post',
                    '.content',
                    '#content',
                    '.main-content'
                ]
                
                text_content = ""
                for selector in main_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            text_content = await element.inner_text()
                            if len(text_content) > 500:  # Good content found
                                break
                    except:
                        continue
                
                # Fallback to body text
                if not text_content or len(text_content) < 200:
                    text_content = await page.evaluate('document.body.innerText')
                
                await browser.close()
                
                # Clean up text
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                clean_text = '\n'.join(lines)
                
                return clean_text
            
            except Exception as e:
                await browser.close()
                raise e
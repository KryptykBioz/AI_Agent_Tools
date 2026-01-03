# Filename: BASE/tools/installed/memory_search/tool.py
"""
Memory Search Tool - FIXED: Complete diagnostics + fallback
===========================================================
FIX: Detailed logging AND keyword fallback when vector search fails
"""
from typing import List, Dict, Any
from BASE.handlers.base_tool import BaseTool
from datetime import datetime


class MemorySearchTool(BaseTool):
    """
    Memory search tool for retrieving past conversations and knowledge
    Integrates with the four-tier memory system
    
    All searches return exactly 1 most relevant result
    Date filtering available for medium and long memory tiers
    """
    
    __slots__ = ('memory_manager', 'memory_search')
    
    @property
    def name(self) -> str:
        return "memory_search"
    
    async def initialize(self) -> bool:
        """Initialize memory search system"""
        # Get memory manager and memory search from config
        self.memory_manager = None
        self.memory_search = None
        
        # Try multiple ways to access memory system
        if hasattr(self._config, 'ai_core'):
            try:
                ai_core = self._config.ai_core
                self.memory_manager = getattr(ai_core, 'memory_manager', None)
                self.memory_search = getattr(ai_core, 'memory_search', None)
                if self._logger and self.memory_manager:
                    self._logger.system("[MemorySearch] Found memory system via config.ai_core")
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"[MemorySearch] Could not access via config.ai_core: {e}")
        
        if not self.memory_manager:
            self.memory_manager = getattr(self._config, 'memory_manager', None)
            if self._logger and self.memory_manager:
                self._logger.system("[MemorySearch] Found memory_manager on config")
        
        if not self.memory_search:
            self.memory_search = getattr(self._config, 'memory_search', None)
            if self._logger and self.memory_search:
                self._logger.system("[MemorySearch] Found memory_search on config")
        
        if not self.memory_manager:
            if self._logger:
                self._logger.error("[MemorySearch] Memory manager not available")
            return False
        
        # Detailed diagnostics
        if self._logger:
            has_search = self.memory_search is not None
            has_medium_memory = hasattr(self.memory_manager, 'medium_memory')
            has_long_memory = hasattr(self.memory_manager, 'long_memory')
            has_short_memory = hasattr(self.memory_manager, 'short_memory')
            
            self._logger.system(
                f"[MemorySearch] Initialization status:\n"
                f"  - memory_manager: ✓ Available\n"
                f"  - memory_search: {'✓ Available' if has_search else '✗ Not found (will use fallback)'}\n"
                f"  - short_memory: {'✓' if has_short_memory else '✗'}\n"
                f"  - medium_memory: {'✓' if has_medium_memory else '✗'}\n"
                f"  - long_memory: {'✓' if has_long_memory else '✗'}"
            )
            
            if self.memory_search:
                has_medium_search = hasattr(self.memory_search, 'search_medium_memory')
                has_long_search = hasattr(self.memory_search, 'search_long_memory')
                has_base_search = hasattr(self.memory_search, 'search_base_knowledge')
                
                self._logger.system(
                    f"[MemorySearch] memory_search methods:\n"
                    f"  - search_medium_memory: {'✓' if has_medium_search else '✗'}\n"
                    f"  - search_long_memory: {'✓' if has_long_search else '✗'}\n"
                    f"  - search_base_knowledge: {'✓' if has_base_search else '✗'}"
                )
            
            try:
                short_count = len(self.memory_manager.short_memory) if has_short_memory else 0
                medium_count = len(self.memory_manager.medium_memory) if has_medium_memory else 0
                long_count = len(self.memory_manager.long_memory) if has_long_memory else 0
                
                self._logger.system(
                    f"[MemorySearch] Memory tier counts:\n"
                    f"  - Short: {short_count} entries\n"
                    f"  - Medium: {medium_count} entries\n"
                    f"  - Long: {long_count} entries"
                )
                
                # CRITICAL DIAGNOSTIC: Check if medium entries have embeddings
                if medium_count > 0:
                    with_embeddings = sum(
                        1 for e in self.memory_manager.medium_memory 
                        if 'embedding' in e and e['embedding']
                    )
                    self._logger.system(
                        f"[MemorySearch] Medium memory embeddings: {with_embeddings}/{medium_count} entries have embeddings"
                    )
                
                if long_count > 0:
                    with_embeddings = sum(
                        1 for e in self.memory_manager.long_memory 
                        if 'embedding' in e and e['embedding']
                    )
                    self._logger.system(
                        f"[MemorySearch] Long memory embeddings: {with_embeddings}/{long_count} entries have embeddings"
                    )
                    
            except Exception as e:
                self._logger.warning(f"[MemorySearch] Could not count entries: {e}")
        
        if self._logger:
            try:
                stats = self.memory_manager.get_stats()
                self._logger.success(
                    f"[MemorySearch] Initialized with memory access:\n"
                    f"  - Short memory: {stats['short_memory_entries']} entries\n"
                    f"  - Medium memory: {stats['medium_memory_entries']} entries\n"
                    f"  - Long memory: {stats['long_memory_summaries']} summaries\n"
                    f"  - Base knowledge: {stats['base_knowledge_chunks']} chunks"
                )
            except Exception as e:
                self._logger.warning(f"[MemorySearch] Could not get stats: {e}")
                self._logger.success("[MemorySearch] Initialized with memory access")
        
        return True
    
    async def cleanup(self):
        """Cleanup memory search resources"""
        if self._logger:
            self._logger.system("[MemorySearch] Cleaned up")
    
    def is_available(self) -> bool:
        """Check if memory search is available"""
        return self.memory_manager is not None
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """Execute memory search command"""
        if not self.is_available():
            return self._error_result(
                'Memory system not available',
                guidance='Memory manager not initialized'
            )
        
        if self._logger:
            self._logger.tool(f"[MemorySearch] Command: '{command}', args: {args}")
        
        if command in ['search', '']:
            return await self._search_all_tiers(args)
        elif command == 'search_short':
            return await self._search_short_memory(args)
        elif command == 'search_medium':
            return await self._search_medium_memory(args)
        elif command == 'search_long':
            return await self._search_long_memory(args)
        elif command == 'search_base':
            return await self._search_base_knowledge(args)
        else:
            return self._error_result(
                f'Unknown command: {command}',
                guidance='Available commands: search, search_short, search_medium, '
                        'search_long, search_base'
            )
    
    # ========================================================================
    # SEARCH IMPLEMENTATIONS
    # ========================================================================
    
    async def _search_all_tiers(self, args: List[Any]) -> Dict[str, Any]:
        """Search across all relevant memory tiers"""
        if not args or not args[0]:
            return self._error_result(
                'No search query provided',
                guidance='Provide a specific search term (e.g., "minecraft", "VTubers")'
            )
        
        query = str(args[0]).strip()
        date_filter = str(args[1]).strip() if len(args) > 1 and args[1] else None
        
        if date_filter and not self._validate_date(date_filter):
            return self._error_result(
                f'Invalid date format: {date_filter}',
                guidance='Use YYYY-MM-DD format (e.g., "2025-12-26")'
            )
        
        if self._logger:
            self._logger.system(f"[MemorySearch] Starting all-tier search for: '{query}'")
            if date_filter:
                self._logger.system(f"[MemorySearch] Date filter: {date_filter}")
        
        try:
            results = []
            
            # TIER 1: Short-term memory
            if self._logger:
                self._logger.system("[MemorySearch] Searching SHORT memory...")
            
            short_results = self._search_short_memory_internal(query, k=1)
            if self._logger:
                self._logger.system(f"[MemorySearch] Short memory: {len(short_results)} results")
            
            if short_results:
                formatted = self._format_short_search_results(short_results)
                results.append(("Short-term Memory (Recent)", formatted))
            
            # TIER 2: Medium-term memory
            if self._logger:
                self._logger.system("[MemorySearch] Searching MEDIUM memory...")
            
            try:
                medium_results = self._search_medium_internal(query, k=1)
                if self._logger:
                    self._logger.system(f"[MemorySearch] Medium memory raw results: {len(medium_results)}")
                
                if date_filter and medium_results:
                    before_filter = len(medium_results)
                    medium_results = self._filter_by_date(medium_results, date_filter)
                    if self._logger:
                        self._logger.system(
                            f"[MemorySearch] Medium after date filter: {len(medium_results)} "
                            f"(filtered out {before_filter - len(medium_results)})"
                        )
                
                if medium_results:
                    formatted = self._format_medium_results(medium_results)
                    results.append(("Medium-term Memory (Earlier Today)", formatted))
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[MemorySearch] Medium search failed: {e}")
                    import traceback
                    traceback.print_exc()
            
            # TIER 3: Long-term memory
            if self._logger:
                self._logger.system("[MemorySearch] Searching LONG memory...")
            
            try:
                long_results = self._search_long_internal(query, k=1)
                if self._logger:
                    self._logger.system(f"[MemorySearch] Long memory raw results: {len(long_results)}")
                
                if date_filter and long_results:
                    before_filter = len(long_results)
                    long_results = self._filter_by_date(long_results, date_filter)
                    if self._logger:
                        self._logger.system(
                            f"[MemorySearch] Long after date filter: {len(long_results)} "
                            f"(filtered out {before_filter - len(long_results)})"
                        )
                
                if long_results:
                    formatted = self._format_long_results(long_results)
                    results.append(("Long-term Memory (Past Days)", formatted))
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[MemorySearch] Long search failed: {e}")
                    import traceback
                    traceback.print_exc()
            
            # TIER 4: Base knowledge
            if self._logger:
                self._logger.system("[MemorySearch] Searching BASE knowledge...")
            
            try:
                base_results = self._search_base_internal(query, k=1)
                if self._logger:
                    self._logger.system(f"[MemorySearch] Base knowledge: {len(base_results)} results")
                
                if base_results:
                    formatted = self._format_base_results(base_results)
                    results.append(("Base Knowledge", formatted))
            except Exception as e:
                if self._logger:
                    self._logger.error(f"[MemorySearch] Base search failed: {e}")
                    import traceback
                    traceback.print_exc()
            
            if not results:
                if self._logger:
                    self._logger.warning(f"[MemorySearch] No results found in any tier for: '{query}'")
                
                return self._error_result(
                    f'No relevant memories found for: {query}',
                    metadata={'query': query, 'date_filter': date_filter},
                    guidance='Try different specific search terms'
                )
            
            content = self._combine_results(results)
            
            if self._logger:
                self._logger.success(
                    f"[MemorySearch] Found {len(results)} tier(s) with matches for '{query}'"
                )
            
            return self._success_result(
                content,
                metadata={
                    'query': query,
                    'date_filter': date_filter,
                    'tiers_searched': len(results)
                }
            )
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[MemorySearch] Search error: {e}")
                import traceback
                traceback.print_exc()
            
            return self._error_result(
                f'Memory search error: {str(e)}',
                metadata={'query': query}
            )
    
    async def _search_short_memory(self, args: List[Any]) -> Dict[str, Any]:
        """Search short-term memory"""
        if not args or not args[0]:
            return self._error_result(
                'No search query provided',
                guidance='Provide a specific search term'
            )
        
        query = str(args[0]).strip()
        
        try:
            results = self._search_short_memory_internal(query, k=1)
            
            if not results:
                return self._error_result(
                    f'No short-term memories found for: {query}',
                    metadata={'query': query}
                )
            
            content = self._format_short_search_results(results)
            
            return self._success_result(
                content,
                metadata={
                    'query': query,
                    'tier': 'short',
                    'results': len(results)
                }
            )
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[MemorySearch] Short search error: {e}")
            return self._error_result(f'Short memory search error: {str(e)}')
    
    def _search_short_memory_internal(self, query: str, k: int = 1) -> List[Dict[str, Any]]:
        """Internal method: Search short-term memory using keyword matching"""
        if not self.memory_manager.short_memory:
            if self._logger:
                self._logger.system("[MemorySearch] Short memory is empty")
            return []
        
        if self._logger:
            self._logger.system(f"[MemorySearch] Searching {len(self.memory_manager.short_memory)} short memory entries")
        
        query_lower = query.lower()
        query_keywords = set(query_lower.split())
        
        results = []
        
        for entry in self.memory_manager.short_memory:
            content = entry.get('content', '').lower()
            
            score = 0.0
            
            if query_lower in content:
                score += 1.0
            
            content_words = set(content.split())
            keyword_overlap = len(query_keywords & content_words)
            if keyword_overlap > 0:
                score += 0.5 * (keyword_overlap / len(query_keywords))
            
            if score > 0:
                results.append({
                    'role': entry.get('role'),
                    'content': entry.get('content'),
                    'timestamp': entry.get('timestamp'),
                    'date': entry.get('date'),
                    'relevance': score
                })
        
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:k]
    
    async def _search_medium_memory(self, args: List[Any]) -> Dict[str, Any]:
        """Search medium-term memory"""
        if not args or not args[0]:
            return self._error_result(
                'No search query provided',
                guidance='Provide a specific search term'
            )
        
        query = str(args[0]).strip()
        date_filter = str(args[1]).strip() if len(args) > 1 and args[1] else None
        
        if date_filter and not self._validate_date(date_filter):
            return self._error_result(
                f'Invalid date format: {date_filter}',
                guidance='Use YYYY-MM-DD format'
            )
        
        try:
            results = self._search_medium_internal(query, k=1)
            
            if date_filter and results:
                results = self._filter_by_date(results, date_filter)
            
            if not results:
                filter_msg = f" on {date_filter}" if date_filter else ""
                return self._error_result(
                    f'No medium-term memories found for: {query}{filter_msg}',
                    metadata={'query': query, 'date_filter': date_filter}
                )
            
            content = self._format_medium_results(results)
            
            return self._success_result(
                content,
                metadata={
                    'query': query,
                    'date_filter': date_filter,
                    'tier': 'medium',
                    'results': len(results)
                }
            )
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[MemorySearch] Medium search error: {e}")
                import traceback
                traceback.print_exc()
            return self._error_result(f'Medium memory search error: {str(e)}')
    
    def _search_medium_internal(self, query: str, k: int = 1) -> List[Dict]:
        """Internal: Search medium memory with AUTOMATIC fallback"""
        # Try vector search first
        if self.memory_search and hasattr(self.memory_search, 'search_medium_memory'):
            try:
                if self._logger:
                    self._logger.system("[MemorySearch] Trying vector search...")
                
                results = self.memory_search.search_medium_memory(query, k=k)
                
                if self._logger:
                    self._logger.system(f"[MemorySearch] Vector search returned {len(results)} results")
                
                # If vector search succeeds, return results
                if results:
                    return results
                
                if self._logger:
                    self._logger.system("[MemorySearch] Vector search returned 0 results, falling back to keyword search")
                    
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"[MemorySearch] Vector search failed: {e}, falling back to keyword search")
        else:
            if self._logger:
                self._logger.system("[MemorySearch] Vector search not available, using keyword search")
        
        # AUTOMATIC FALLBACK: Keyword search
        return self._keyword_search_medium(query, k)
    
    def _keyword_search_medium(self, query: str, k: int = 1) -> List[Dict]:
        """Fallback: Keyword-based search for medium memory"""
        if not hasattr(self.memory_manager, 'medium_memory'):
            if self._logger:
                self._logger.system("[MemorySearch] No medium_memory attribute")
            return []
        
        medium_mem = self.memory_manager.medium_memory
        
        if not medium_mem:
            if self._logger:
                self._logger.system("[MemorySearch] medium_memory is empty")
            return []
        
        if self._logger:
            self._logger.system(f"[MemorySearch] Keyword searching {len(medium_mem)} medium memory entries")
        
        query_lower = query.lower()
        query_keywords = set(query_lower.split())
        
        results = []
        matches_found = 0
        
        for i, entry in enumerate(medium_mem):
            content = entry.get('content', '').lower()
            
            score = 0.0
            
            # Exact substring match
            if query_lower in content:
                score += 1.0
                matches_found += 1
                if self._logger and matches_found <= 3:
                    self._logger.system(f"[MemorySearch] Found exact match in entry {i}: '{entry.get('content', '')[:100]}...'")
            
            # Keyword overlap
            content_words = set(content.split())
            keyword_overlap = len(query_keywords & content_words)
            if keyword_overlap > 0:
                score += 0.5 * (keyword_overlap / len(query_keywords))
            
            if score > 0:
                results.append({
                    'role': entry.get('role'),
                    'content': entry.get('content'),
                    'timestamp': entry.get('timestamp'),
                    'date': entry.get('date'),
                    'similarity': score
                })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        if self._logger:
            self._logger.system(f"[MemorySearch] Keyword search found {len(results)} matching entries (returning top {k})")
        
        return results[:k]
    
    async def _search_long_memory(self, args: List[Any]) -> Dict[str, Any]:
        """Search long-term memory"""
        if not args or not args[0]:
            return self._error_result(
                'No search query provided',
                guidance='Provide a specific search term'
            )
        
        query = str(args[0]).strip()
        date_filter = str(args[1]).strip() if len(args) > 1 and args[1] else None
        
        if date_filter and not self._validate_date(date_filter):
            return self._error_result(
                f'Invalid date format: {date_filter}',
                guidance='Use YYYY-MM-DD format'
            )
        
        try:
            results = self._search_long_internal(query, k=1)
            
            if date_filter and results:
                results = self._filter_by_date(results, date_filter)
            
            if not results:
                filter_msg = f" on {date_filter}" if date_filter else ""
                return self._error_result(
                    f'No long-term memories found for: {query}{filter_msg}',
                    metadata={'query': query, 'date_filter': date_filter}
                )
            
            content = self._format_long_results(results)
            
            return self._success_result(
                content,
                metadata={
                    'query': query,
                    'date_filter': date_filter,
                    'tier': 'long',
                    'results': len(results)
                }
            )
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[MemorySearch] Long search error: {e}")
                import traceback
                traceback.print_exc()
            return self._error_result(f'Long memory search error: {str(e)}')
    
    def _search_long_internal(self, query: str, k: int = 1) -> List[Dict]:
        """Internal: Search long memory with AUTOMATIC fallback"""
        # Try vector search first
        if self.memory_search and hasattr(self.memory_search, 'search_long_memory'):
            try:
                if self._logger:
                    self._logger.system("[MemorySearch] Trying vector search...")
                
                results = self.memory_search.search_long_memory(query, k=k)
                
                if self._logger:
                    self._logger.system(f"[MemorySearch] Vector search returned {len(results)} results")
                
                if results:
                    return results
                
                if self._logger:
                    self._logger.system("[MemorySearch] Vector search returned 0 results, falling back to keyword search")
                    
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"[MemorySearch] Vector search failed: {e}, falling back to keyword search")
        else:
            if self._logger:
                self._logger.system("[MemorySearch] Vector search not available, using keyword search")
        
        # AUTOMATIC FALLBACK: Keyword search
        return self._keyword_search_long(query, k)
    
    def _keyword_search_long(self, query: str, k: int = 1) -> List[Dict]:
        """Fallback: Keyword-based search for long memory"""
        if not hasattr(self.memory_manager, 'long_memory') or not self.memory_manager.long_memory:
            if self._logger:
                self._logger.system("[MemorySearch] long_memory is empty or not available")
            return []
        
        if self._logger:
            self._logger.system(f"[MemorySearch] Keyword searching {len(self.memory_manager.long_memory)} long memory entries")
        
        query_lower = query.lower()
        query_keywords = set(query_lower.split())
        
        results = []
        
        for entry in self.memory_manager.long_memory:
            summary = entry.get('summary', '').lower()
            
            score = 0.0
            
            if query_lower in summary:
                score += 1.0
            
            summary_words = set(summary.split())
            keyword_overlap = len(query_keywords & summary_words)
            if keyword_overlap > 0:
                score += 0.5 * (keyword_overlap / len(query_keywords))
            
            if score > 0:
                results.append({
                    'summary': entry.get('summary'),
                    'date': entry.get('date'),
                    'similarity': score
                })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        if self._logger:
            self._logger.system(f"[MemorySearch] Keyword search found {len(results)} matching entries")
        
        return results[:k]
    
    async def _search_base_knowledge(self, args: List[Any]) -> Dict[str, Any]:
        """Search base knowledge"""
        if not args or not args[0]:
            return self._error_result(
                'No search query provided',
                guidance='Provide a specific search term'
            )
        
        query = str(args[0]).strip()
        
        try:
            results = self._search_base_internal(query, k=1)
            
            if not results:
                return self._error_result(
                    f'No base knowledge found for: {query}',
                    metadata={'query': query}
                )
            
            content = self._format_base_results(results)
            
            return self._success_result(
                content,
                metadata={
                    'query': query,
                    'tier': 'base',
                    'results': len(results)
                }
            )
        
        except Exception as e:
            if self._logger:
                self._logger.error(f"[MemorySearch] Base search error: {e}")
                import traceback
                traceback.print_exc()
            return self._error_result(f'Base knowledge search error: {str(e)}')
    
    def _search_base_internal(self, query: str, k: int = 1) -> List[Dict]:
        """Internal: Search base knowledge"""
        if self.memory_search and hasattr(self.memory_search, 'search_base_knowledge'):
            try:
                results = self.memory_search.search_base_knowledge(query, k=k, min_similarity=0.4)
                if self._logger:
                    self._logger.system(f"[MemorySearch] Base search: {len(results)} results")
                return results
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"[MemorySearch] Base search failed: {e}")
        
        return []
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _validate_date(self, date_str: str) -> bool:
        """Validate date format YYYY-MM-DD"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def _filter_by_date(self, results: List[Dict], date_filter: str) -> List[Dict]:
        """Filter results by date"""
        filtered = []
        for result in results:
            result_date = result.get('date', '')
            if result_date and result_date == date_filter:
                filtered.append(result)
        return filtered
    
    # ========================================================================
    # FORMATTING HELPERS
    # ========================================================================
    
    def _format_short_search_results(self, results: List[Dict]) -> str:
        """Format short-term memory search results"""
        lines = []
        
        for result in results:
            role = (self.memory_manager.username if result['role'] == 'user' 
                    else self.memory_manager.agentname)
            timestamp = result.get('timestamp', 'Unknown')
            content = result['content']
            relevance = result['relevance']
            date = result.get('date', '')
            
            date_str = f" ({date})" if date else ""
            lines.append(f"[{timestamp}{date_str}] {role}: {content}")
            lines.append(f"  (relevance: {relevance:.2f})\n")
        
        return "\n".join(lines)
    
    def _format_medium_results(self, results: List[Dict]) -> str:
        """Format medium-term memory results"""
        lines = []
        
        for result in results:
            role = (self.memory_manager.username if result['role'] == 'user' 
                    else self.memory_manager.agentname)
            timestamp = result.get('timestamp', 'Unknown')
            content = result['content']
            similarity = result['similarity']
            date = result.get('date', '')
            
            date_str = f" ({date})" if date else ""
            lines.append(f"[{timestamp}{date_str}] {role}: {content}")
            lines.append(f"  (relevance: {similarity:.2f})\n")
        
        return "\n".join(lines)
    
    def _format_long_results(self, results: List[Dict]) -> str:
        """Format long-term memory results"""
        lines = []
        
        for result in results:
            date = result.get('date', 'Unknown date')
            summary = result['summary']
            similarity = result['similarity']
            
            lines.append(f"**{date}**")
            lines.append(f"{summary}")
            lines.append(f"(relevance: {similarity:.2f})\n")
        
        return "\n".join(lines)
    
    def _format_base_results(self, results: List[Dict]) -> str:
        """Format base knowledge results"""
        lines = []
        
        for result in results:
            text = result['text']
            metadata = result.get('metadata', {})
            similarity = result['similarity']
            
            chunk_type = metadata.get('type', 'document')
            if chunk_type in ['conversation_example', 'category_summary', 'system_prompt']:
                type_label = 'Personality Knowledge'
            else:
                type_label = 'Reference Document'
            
            source = metadata.get('source_file', 'Unknown source')
            
            lines.append(f"**{type_label}** (from {source})")
            lines.append(f"{text}")
            lines.append(f"(relevance: {similarity:.2f})\n")
        
        return "\n".join(lines)
    
    def _combine_results(self, results: List[tuple]) -> str:
        """Combine results from multiple tiers"""
        sections = []
        
        for tier_name, content in results:
            sections.append(f"## {tier_name}\n\n{content}")
        
        return "\n\n".join(sections)
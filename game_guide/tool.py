# Filename: BASE/tools/installed/game_guide/tool.py
"""
Game Guide Tool - Search embedded game guides for gameplay information
======================================================================
Searches vector embeddings of markdown game guides with keyword fallback

FIXED: Preserves newlines and formatting in search results
"""
from typing import List, Dict, Any, Optional
from BASE.handlers.base_tool import BaseTool
from pathlib import Path
import json
import numpy as np
import requests
import re


class GameGuideTool(BaseTool):
    """
    Game guide search tool for retrieving gameplay tips and strategies
    Searches embedded markdown game guides
    
    All searches return exactly 5 most relevant results
    Supports filtering by game name
    """
    
    __slots__ = (
        'project_root', 'embeddings_dir', 'game_guides', 'ollama_url', 
        'embed_model', 'games_index'
    )
    
    @property
    def name(self) -> str:
        return "game_guide"
    
    async def initialize(self) -> bool:
        """Initialize game guide system"""
        # Get project root
        if hasattr(self._config, 'project_root'):
            self.project_root = self._config.project_root
        else:
            # Fallback: calculate from file location
            self.project_root = Path(__file__).parent.parent.parent.parent.parent
        
        # Set paths
        self.embeddings_dir = (
            self.project_root / "personality" / "base_memory" / 
            "game_guides" / "embeddings"
        )
        
        # Ollama configuration
        self.ollama_url = getattr(self._config, 'ollama_endpoint', 'http://localhost:11434')
        self.embed_model = getattr(self._config, 'embed_model', 'nomic-embed-text')
        
        # Storage for loaded guides
        self.game_guides = []
        self.games_index = {}  # game_name -> list of chunks
        
        # Load all game guides
        success = self._load_game_guides()
        
        if not success:
            if self._logger:
                self._logger.warning(
                    "[GameGuide] No game guides found. Add markdown files to:\n"
                    f"  {self.project_root / 'personality' / 'base_memory' / 'game_guides'}\n"
                    "Then run: python BASE/memory/embed_document.py --game-guides"
                )
            return False
        
        return True
    
    def _load_game_guides(self) -> bool:
        """Load all embedded game guides"""
        if not self.embeddings_dir.exists():
            if self._logger:
                self._logger.warning(
                    f"[GameGuide] Embeddings directory not found: {self.embeddings_dir}"
                )
            return False
        
        json_files = list(self.embeddings_dir.glob("*.json"))
        
        if not json_files:
            if self._logger:
                self._logger.warning(
                    f"[GameGuide] No embedded guides found in {self.embeddings_dir}"
                )
            return False
        
        loaded_count = 0
        total_chunks = 0
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    guide_data = json.load(f)
                
                # Validate it's a game guide
                if guide_data.get('mode') != 'game_guides':
                    continue
                
                chunks = guide_data.get('chunks', [])
                
                # Skip if no valid chunks
                valid_chunks = [
                    c for c in chunks 
                    if c.get('embedding') and isinstance(c['embedding'], list)
                ]
                
                if not valid_chunks:
                    if self._logger:
                        self._logger.warning(
                            f"[GameGuide] No valid chunks in {json_file.name}"
                        )
                    continue
                
                # Get game name from metadata
                game_name = guide_data.get('metadata', {}).get('game_name', json_file.stem)
                game_name_normalized = game_name.lower().strip()
                
                # Store chunks
                for chunk in valid_chunks:
                    self.game_guides.append(chunk)
                    
                    # Add to game index
                    if game_name_normalized not in self.games_index:
                        self.games_index[game_name_normalized] = []
                    self.games_index[game_name_normalized].append(chunk)
                
                loaded_count += 1
                total_chunks += len(valid_chunks)
                
                if self._logger:
                    self._logger.system(
                        f"[GameGuide] Loaded {game_name}: {len(valid_chunks)} chunks"
                    )
                
            except Exception as e:
                if self._logger:
                    self._logger.warning(
                        f"[GameGuide] Failed to load {json_file.name}: {e}"
                    )
        
        if loaded_count == 0:
            return False
        
        if self._logger:
            self._logger.success(
                f"[GameGuide] Loaded {loaded_count} game guide(s) "
                f"with {total_chunks} total chunks"
            )
            self._logger.system(
                f"[GameGuide] Available games: {', '.join(sorted(self.games_index.keys()))}"
            )
        
        return True
    
    async def cleanup(self):
        """Cleanup game guide resources"""
        self.game_guides.clear()
        self.games_index.clear()
        
        if self._logger:
            self._logger.system("[GameGuide] Cleaned up")
    
    def is_available(self) -> bool:
        """Check if game guides are available"""
        return len(self.game_guides) > 0
    
    async def execute(self, command: str, args: List[Any]) -> Dict[str, Any]:
        """Execute game guide command"""
        if not self.is_available():
            return self._error_result(
                'No game guides loaded',
                guidance='Add markdown files to personality/base_memory/game_guides/ '
                        'and run: python BASE/memory/embed_document.py --game-guides'
            )
        
        if self._logger:
            self._logger.tool(f"[GameGuide] Command: '{command}', args: {args}")
        
        if command in ['search', '']:
            return await self._search_all_guides(args)
        elif command == 'search_game':
            return await self._search_specific_game(args)
        elif command == 'list_games':
            return await self._list_games(args)
        elif command == 'get_sections':
            return await self._get_sections(args)
        else:
            return self._error_result(
                f'Unknown command: {command}',
                guidance='Available commands: search, search_game, list_games, get_sections'
            )
    
    # ========================================================================
    # SEARCH IMPLEMENTATIONS
    # ========================================================================
    
    async def _search_all_guides(self, args: List[Any]) -> Dict[str, Any]:
        """Search across all game guides"""
        if not args or not args[0]:
            return self._error_result(
                'No search query provided',
                guidance='Provide a specific search term (e.g., "crafting", "boss fight")'
            )
        
        query = str(args[0]).strip()
        game_filter = str(args[1]).strip().lower() if len(args) > 1 and args[1] else None
        
        if self._logger:
            if game_filter:
                self._logger.system(
                    f"[GameGuide] Searching all guides for '{query}' (filter: {game_filter})"
                )
            else:
                self._logger.system(f"[GameGuide] Searching all guides for '{query}'")
        
        # Apply game filter if provided
        if game_filter:
            chunks_to_search = []
            for chunk in self.game_guides:
                chunk_game = chunk.get('metadata', {}).get('game_name', '').lower()
                if game_filter in chunk_game:
                    chunks_to_search.append(chunk)
            
            if not chunks_to_search:
                return self._error_result(
                    f'No game guides found matching "{game_filter}"',
                    guidance=f'Available games: {", ".join(sorted(self.games_index.keys()))}'
                )
        else:
            chunks_to_search = self.game_guides
        
        # Perform search
        results = await self._semantic_search(query, chunks_to_search, k=5)
        
        if not results:
            return self._error_result(
                f'No results found for "{query}"',
                guidance='Try different search terms or check available games with list_games'
            )
        
        # Format results
        formatted = self._format_search_results(results)
        
        return self._success_result(
            formatted,
            metadata={
                'query': query,
                'results_count': len(results),
                'game_filter': game_filter
            }
        )
    
    async def _search_specific_game(self, args: List[Any]) -> Dict[str, Any]:
        """Search within a specific game's guide"""
        if len(args) < 2:
            return self._error_result(
                'Missing arguments',
                guidance='Provide: game_name, search_query'
            )
        
        game_name = str(args[0]).strip().lower()
        query = str(args[1]).strip()
        
        if not game_name or not query:
            return self._error_result(
                'Empty game name or query',
                guidance='Both game_name and query must be provided'
            )
        
        if self._logger:
            self._logger.system(
                f"[GameGuide] Searching {game_name} for '{query}'"
            )
        
        # Get chunks for this game
        if game_name not in self.games_index:
            return self._error_result(
                f'Game "{game_name}" not found',
                guidance=f'Available games: {", ".join(sorted(self.games_index.keys()))}'
            )
        
        chunks_to_search = self.games_index[game_name]
        
        # Perform search
        results = await self._semantic_search(query, chunks_to_search, k=5)
        
        if not results:
            return self._error_result(
                f'No results found in {game_name} for "{query}"',
                guidance='Try different search terms or use get_sections to see available topics'
            )
        
        # Format results
        formatted = self._format_search_results(results, game_name=game_name)
        
        return self._success_result(
            formatted,
            metadata={
                'game': game_name,
                'query': query,
                'results_count': len(results)
            }
        )
    
    async def _list_games(self, args: List[Any]) -> Dict[str, Any]:
        """List all available game guides"""
        games = sorted(self.games_index.keys())
        
        lines = ["## Available Game Guides\n"]
        
        for game in games:
            chunk_count = len(self.games_index[game])
            lines.append(f"**{game.title()}** ({chunk_count} sections)")
        
        lines.append(f"\nTotal: {len(games)} game(s)")
        
        content = "\n".join(lines)
        
        return self._success_result(
            content,
            metadata={'games': games, 'total': len(games)}
        )
    
    async def _get_sections(self, args: List[Any]) -> Dict[str, Any]:
        """Get section headings from a game guide"""
        if not args or not args[0]:
            return self._error_result(
                'No game name provided',
                guidance='Provide a game name (use list_games to see available games)'
            )
        
        game_name = str(args[0]).strip().lower()
        
        if game_name not in self.games_index:
            return self._error_result(
                f'Game "{game_name}" not found',
                guidance=f'Available games: {", ".join(sorted(self.games_index.keys()))}'
            )
        
        # Extract unique section headings from chunks
        sections = set()
        chunks = self.games_index[game_name]
        
        for chunk in chunks:
            text = chunk.get('text', '')
            # Look for markdown headers
            for line in text.split('\n'):
                if line.startswith('##'):
                    section = line.lstrip('#').strip()
                    if section:
                        sections.add(section)
        
        sections_list = sorted(sections)
        
        lines = [f"## {game_name.title()} - Sections\n"]
        
        if sections_list:
            for section in sections_list:
                lines.append(f"- {section}")
        else:
            lines.append("No section headings found")
        
        content = "\n".join(lines)
        
        return self._success_result(
            content,
            metadata={
                'game': game_name,
                'sections': sections_list,
                'total': len(sections_list)
            }
        )
    
    # ========================================================================
    # CORE SEARCH ENGINE
    # ========================================================================
    
    async def _semantic_search(
        self, 
        query: str, 
        chunks: List[Dict], 
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using embeddings with keyword fallback
        Always returns top k results
        """
        try:
            # Get query embedding
            query_embedding = await self._get_embedding(query)
            
            if query_embedding:
                if self._logger:
                    self._logger.system("[GameGuide] Using vector similarity search")
                
                results = []
                
                for chunk in chunks:
                    embedding = chunk.get('embedding')
                    if not embedding:
                        continue
                    
                    similarity = self._cosine_similarity(query_embedding, embedding)
                    
                    if similarity > 0.3:  # Minimum threshold
                        results.append({
                            'text': chunk.get('text', ''),
                            'metadata': chunk.get('metadata', {}),
                            'similarity': similarity
                        })
                
                # Sort by similarity
                results.sort(key=lambda x: x['similarity'], reverse=True)
                
                if results:
                    return results[:k]
                
                if self._logger:
                    self._logger.system(
                        "[GameGuide] Vector search returned 0 results, "
                        "falling back to keyword search"
                    )
        
        except Exception as e:
            if self._logger:
                self._logger.warning(
                    f"[GameGuide] Vector search failed: {e}, using keyword fallback"
                )
        
        # Fallback: Keyword search
        return self._keyword_search(query, chunks, k)
    
    def _keyword_search(
        self, 
        query: str, 
        chunks: List[Dict], 
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Keyword-based search fallback"""
        if self._logger:
            self._logger.system("[GameGuide] Using keyword search")
        
        query_lower = query.lower()
        query_keywords = set(query_lower.split())
        
        results = []
        
        for chunk in chunks:
            text = chunk.get('text', '').lower()
            
            score = 0.0
            
            # Exact substring match
            if query_lower in text:
                score += 1.0
            
            # Keyword overlap
            text_words = set(text.split())
            keyword_overlap = len(query_keywords & text_words)
            if keyword_overlap > 0:
                score += 0.5 * (keyword_overlap / len(query_keywords))
            
            if score > 0:
                results.append({
                    'text': chunk.get('text', ''),
                    'metadata': chunk.get('metadata', {}),
                    'similarity': score
                })
        
        # Sort by score
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:k]
    
    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding vector from Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.embed_model, "prompt": text},
                timeout=30
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            if self._logger:
                self._logger.warning(f"[GameGuide] Embedding error: {e}")
            return None
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between vectors"""
        try:
            a_arr = np.array(a)
            b_arr = np.array(b)
            
            norm_a = np.linalg.norm(a_arr)
            norm_b = np.linalg.norm(b_arr)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))
        
        except Exception as e:
            if self._logger:
                self._logger.debug(f"[GameGuide] Similarity error: {e}")
            return 0.0
    
    # ========================================================================
    # FORMATTING - FIXED TO PRESERVE NEWLINES
    # ========================================================================
    
    def _format_search_results(
        self, 
        results: List[Dict[str, Any]], 
        game_name: Optional[str] = None
    ) -> str:
        """
        Format search results for display with PRESERVED formatting
        
        FIXED: No longer strips newlines or collapses whitespace
        """
        lines = []
        
        # Header
        if game_name:
            lines.append(f"## {game_name.title()} - Search Results\n")
        else:
            lines.append("## Game Guide Search Results\n")
        
        # Results
        for i, result in enumerate(results, 1):
            text = result['text']
            metadata = result.get('metadata', {})
            similarity = result['similarity']
            
            result_game = metadata.get('game_name', 'Unknown')
            source_file = metadata.get('source_file', '')
            
            lines.append(f"**[Result {i}]** {result_game.title()}")
            if source_file:
                lines.append(f"Source: {source_file}")
            
            # FIXED: Use minimal cleaning that preserves formatting
            formatted_text = self._preserve_formatting(text)
            
            # Smart truncation at paragraph boundary
            if len(formatted_text) > 800:
                formatted_text = self._smart_truncate(formatted_text, 800)
            
            lines.append(f"\n{formatted_text}")
            lines.append(f"\n(relevance: {similarity:.2f})\n")
        
        return "\n".join(lines)
    
    def _preserve_formatting(self, text: str) -> str:
        """
        Minimal cleaning that PRESERVES newlines and formatting
        
        FIXED: Only removes excessive blank lines, keeps structure intact
        """
        # Only clean up excessive consecutive blank lines (3+ newlines -> 2 newlines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove any trailing/leading whitespace from the entire text
        text = text.strip()
        
        return text
    
    def _smart_truncate(self, text: str, max_length: int) -> str:
        """
        Truncate text at natural boundary near max_length
        
        FIXED: Tries to break at paragraph boundaries to preserve structure
        """
        if len(text) <= max_length:
            return text
        
        truncated = text[:max_length]
        
        # Priority 1: Break at paragraph (double newline)
        para_break = truncated.rfind('\n\n')
        if para_break > max_length * 0.6:
            return text[:para_break].strip() + "\n\n[...]"
        
        # Priority 2: Break at single newline
        line_break = truncated.rfind('\n')
        if line_break > max_length * 0.7:
            return text[:line_break].strip() + "\n[...]"
        
        # Priority 3: Break at sentence
        sentence_ends = [truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?')]
        last_sentence = max(sentence_ends)
        if last_sentence > max_length * 0.7:
            return text[:last_sentence + 1].strip() + " [...]"
        
        # Priority 4: Break at word boundary
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return text[:last_space].strip() + " [...]"
        
        # Last resort: hard truncate
        return truncated.strip() + " [...]"
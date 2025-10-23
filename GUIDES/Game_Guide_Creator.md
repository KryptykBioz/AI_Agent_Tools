# Game Guide RAG System - Setup & Usage Guide

## Overview

Your AI assistant now has an intelligent four-tier memory system optimized for game guides:

- **Tier 1**: Working Memory (latest conversation, always in context)
- **Tier 2**: Current Day (today's interactions, searchable)
- **Tier 3**: Past Days (summarized history, searchable)
- **Tier 4**: Base Knowledge (game guides, searchable with metadata)

## Setup Instructions

### 1. Prepare Your Game Guide

Save your League of Legends guide (or any game guide) as a markdown file:
```
Esther_AI/personality/memory_base/base_files/league_of_legends_guide.md
```

### 2. Embed the Guide

Run the embedding script:
```bash
cd Esther_AI/BASE/memory_methods
python embed_game_guide.py
```

The script will:
- Find all `.md`, `.txt`, `.rst` files in `base_files/`
- Parse them into semantic sections (preserving hierarchy)
- Split large sections intelligently (2000 char max, 1500 ideal)
- Extract metadata (content types, difficulty, key terms)
- Generate embeddings with Ollama
- Save to `base_memory/` directory

### 3. Verify Loading

Start your AI and check the logs:
```
[Tier 4] Loaded 147 chunks from league_of_legends_guide_embeddings.json
[Tier 4] Total: 147 base knowledge chunks from 1 files
```

## Using the System

### In Conversation

The AI automatically searches base knowledge when relevant:

**User**: "How do I play jungle effectively?"

The system will:
1. Embed the query
2. Search base knowledge (cosine similarity)
3. Return top 5 relevant chunks with metadata
4. Include in AI's context with section paths and relevance scores

### Memory Commands

#### Basic Commands
```bash
/memory                    # Show statistics for all tiers
/base_summary             # Detailed base knowledge breakdown
/show_working             # See latest conversation context
```

#### Search Commands
```bash
# Search all tiers
/search_memory how to gank

# Search only base knowledge
/search_base jungle pathing

# Advanced guide search with filters
/search_guide teamfight --type=strategy
/search_guide items --section=itemization
/search_guide champions --type=character_info
```

#### Debug Commands
```bash
/memory_debug             # Show system paths and stats
/test_search             # Test embedding and search
/reload_base             # Reload guide files
```

## How It Works

### Intelligent Chunking

The embedder splits your guide intelligently:

1. **By Headers**: Respects markdown structure (##, ###, ####)
2. **By Size**: Max 2000 chars, ideal 1500 chars
3. **By Semantics**: Splits at paragraphs, lists, sentences
4. **With Context**: Each chunk knows its hierarchy

Example chunk structure:
```json
{
  "title": "Jungle Pathing & Gank Timing",
  "hierarchy": ["JUNGLE CHAMPIONS", "Jungle Pathing & Gank Timing"],
  "section_path": "JUNGLE CHAMPIONS > Jungle Pathing & Gank Timing",
  "content": "Original text content...",
  "searchable_text": "Section: JUNGLE CHAMPIONS > Jungle Pathing...",
  "metadata": {
    "content_types": ["strategy", "tutorial"],
    "key_terms": ["gank", "jungle path", "timing"],
    "has_list": true
  },
  "embedding": [0.123, 0.456, ...],
  "similarity": 0.87
}
```

### Search & Retrieval

When a user asks a question:

1. **Query Embedding**: Question → embedding vector
2. **Similarity Search**: Compare with all chunk embeddings (cosine similarity)
3. **Filtering**: Apply minimum threshold (0.3 by default)
4. **Ranking**: Sort by relevance score
5. **Context Building**: Include top K results (5 by default) with:
   - Section hierarchy
   - Content type tags
   - Relevance scores
   - Key terms

### Metadata-Enhanced Search

The system extracts and uses:

**Content Types**:
- `strategy` - Tips, best practices, how-to guides
- `troubleshooting` - Common mistakes, solutions
- `checklist` - Action items, pre-game checks
- `reference` - Tables, stats, values
- `tutorial` - Step-by-step instructions
- `character_info` - Champion/hero details
- `mechanics` - Game systems, controls
- `itemization` - Equipment, builds
- `terminology` - Definitions, glossary

**Structural Elements**:
- Tables (for stats)
- Lists (for checklists)
- Code blocks (for commands)
- Bold terms (key concepts)

**Difficulty Levels**:
- Beginner, Intermediate, Advanced, Expert

## Adding More Guides

### 1. Create New Guide
```markdown
# Valorant Complete Guide

## Agent Roles

### Duelists
**Jett** - High mobility duelist
- Abilities: Dash, updraft, blade storm
- Playstyle: Entry fragger, aggressive
...

### Controllers
**Omen** - Smoke controller
...
```

### 2. Save to Directory
```
Esther_AI/personality/memory_base/base_files/valorant_guide.md
```

### 3. Run Embedder
```bash
python embed_game_guide.py
```

Output:
```
Found 2 files to process
Processing file 1/2: league_of_legends_guide.md
  (Skipped - already exists)
Processing file 2/2: valorant_guide.md
  Created 89 chunks
  ✓ Successfully processed
```

### 4. Reload in AI
```bash
/reload_base
```

## Advanced Features

### Filtered Search

Search with specific criteria:
```bash
# Only strategy content
/search_guide jungle --type=strategy

# Specific section
/search_guide support --section="Support Champions"

# Multiple filters
/search_guide laning --type=tutorial --section="Lane Mechanics"
```

### Context Formatting

Results include rich formatting:
```
=== BASE KNOWLEDGE ===
[league_of_legends_guide.md] [Jungle Champions > Early Game Gankers] (strategy, tutorial)
Master Yi and Amumu are strong early game junglers who can gank effectively...
(relevance: 0.89)
```

### Auto-Summarization

The system automatically summarizes conversations every 50 interactions:
- Tier 2 (current day) → compressed into Tier 3 (past days)
- Frees up context space
- Maintains searchable history

## Performance Tips

### 1. Optimal Chunk Sizes
- **2000 chars max**: Prevents token overload
- **1500 chars ideal**: Balances context and specificity
- **500 chars min**: Avoids tiny fragments

### 2. Search Tuning

Adjust in code (`memory_manager.py`):
```python
# Minimum similarity threshold (0.0-1.0)
min_similarity: float = 0.3  # Lower = more results

# Number of results
k: int = 5  # Higher = more context
```

### 3. Embedding Model

Using `nomic-embed-text`:
- 768 dimensions
- Fast and efficient
- Good for semantic search

Alternative models:
```bash
# More powerful but slower
ollama pull mxbai-embed-large

# Update in config
embed_model = "mxbai-embed-large"
```

## Troubleshooting

### No Results Found

1. Check base knowledge loaded:
   ```bash
   /base_summary
   ```

2. Test search:
   ```bash
   /test_search
   ```

3. Check files:
   ```bash
   /memory_debug
   ```

### Low Relevance Scores

- Guide might not contain relevant info
- Try rephrasing query
- Check guide covers the topic

### Slow Searches

- Reduce `k` parameter (fewer results)
- Check Ollama is running locally
- Consider smaller embedding model

## Example Workflows

### Player Asking for Help

**User**: "I keep dying as ADC, what am I doing wrong?"

**System**:
1. Searches base knowledge for "dying ADC positioning"
2. Finds relevant sections:
   - ADC positioning (0.89 similarity)
   - Common mistakes (0.85)
   - Trading stance (0.78)
3. Provides context to AI
4. AI responds with specific advice from guide

### Learning New Champion

**User**: "How do I play Lee Sin jungle?"

**System**:
1. Searches: "Lee Sin jungle"
2. Finds:
   - Lee Sin champion details (0.95)
   - Jungle pathing (0.88)
   - Early game gankers (0.82)
3. AI explains with guide context

### Strategic Planning

**User**: "What should my team prioritize mid game?"

**System**:
1. Searches: "team mid game objectives"
2. Finds:
   - Mid game strategies (0.91)
   - Objective priority (0.87)
   - Team coordination (0.79)
3. AI provides structured advice

## File Structure

```
Esther_AI/
├── personality/
│   └── memory_base/
│       ├── base_files/              # Input: Your game guides
│       │   ├── league_of_legends_guide.md
│       │   └── valorant_guide.md
│       └── base_memory/             # Output: Embeddings
│           ├── league_of_legends_guide_embeddings.json
│           └── valorant_guide_embeddings.json
├── BASE/
│   └── memory_methods/
│       ├── embed_game_guide.py      # Embedding script
│       ├── memory_manager.py        # Updated manager
│       └── memory_commands.py       # Updated commands
└── memory/
    ├── short_memory.json            # Current day (Tier 2)
    └── long_memory.json             # Past days (Tier 3)
```

## Best Practices

### 1. Guide Writing

- **Use clear headers**: System relies on markdown structure
- **Keep sections focused**: Each section = one topic
- **Include metadata**: Bold important terms, use lists
- **Add examples**: Real scenarios help matching

### 2. Chunking Strategy

- **Let auto-chunking work**: Don't force arbitrary sizes
- **Respect hierarchy**: Sub-sections under main topics
- **Include context**: Each chunk is self-contained

### 3. Maintenance

- **Update regularly**: Re-embed when guides change
- **Monitor stats**: Check which sections are retrieved
- **Test searches**: Verify coverage of common questions

## Future Enhancements

Potential improvements:

1. **Multi-modal**: Add image analysis for game screenshots
2. **Dynamic updates**: Hot-reload guides without restart
3. **Usage analytics**: Track which sections are most helpful
4. **Cross-references**: Link related sections automatically
5. **Version control**: Track guide changes over time

---

Your AI assistant is now ready to be an expert gaming guide! 🎮
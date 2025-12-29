# DuckDuckGo Search Tool

Privacy-focused web search using DuckDuckGo with no tracking, no user profiling, and no API key required.

## Features

- **Privacy-Focused**: No tracking or user profiling
- **No API Key Required**: Uses HTML scraping (always available)
- **Domain Diversity**: Each result from a different website
- **Pagination**: Same query returns different results each time
- **Source Attribution**: Each result shows its domain
- **HTML Entity Decoding**: Clean, readable results
- **Deduplication**: Avoids showing duplicate URLs

## Setup

No configuration required! The tool works out of the box.

### Enable in Controls

Set `USE_DUCKDUCKGO_SEARCH = True` in `personality/controls.py` or via the GUI.

## Usage

The agent can use DuckDuckGo search automatically when:
- Asked about current events or news
- Needing recent information
- Questions about topics that change frequently
- Privacy is a concern

### Commands

**Search:**
```json
{"tool": "duckduckgo.search", "args": ["Python tutorials"]}
```

**Reset Pagination (start over):**
```json
{"tool": "duckduckgo.reset", "args": ["Python tutorials"]}
```

### Examples

**User:** "What's the latest news about AI?"
**Agent:** Uses `{"tool": "duckduckgo.search", "args": ["latest AI news"]}`

**User:** "Search for Python tutorials" (multiple times)
**Agent:** 
- 1st call: Results 1-5 from 5 different domains
- 2nd call: Results 6-10 from 5 different domains
- 3rd call: Results 11-15 from 5 different domains

## Result Format

Each result includes:
```
1. Result Title
Description of the result
Source: example.com
URL: https://example.com/full/path
```

## Domain Diversity

The tool ensures each result comes from a **different domain**:
- ✅ example.com
- ✅ wikipedia.org
- ✅ github.com
- ✅ stackoverflow.com
- ✅ reddit.com

**Not allowed in same batch:**
- ❌ example.com
- ❌ example.com (duplicate domain)

This provides diverse perspectives and prevents domain monopolization.

## Pagination Behavior

**First search:**
```
User: Search for "Python tutorials"
Results: 1-5 (from 5 different domains)
```

**Second search (same query):**
```
User: Search for "Python tutorials"
Results: 6-10 (from 5 different domains, no duplicates)
```

**Third search:**
```
User: Search for "Python tutorials"
Results: 11-15 (from 5 different domains, no duplicates)
```

After ~10 pages (50 results), automatically wraps back to page 1.

## Architecture

```
duckduckgo_search/
├── tool.py              # Main search implementation
├── information.json     # Tool metadata
└── README.md           # This file
```

## Privacy

DuckDuckGo search provides:
- ✅ No tracking cookies
- ✅ No user profiling
- ✅ No search history storage
- ✅ No personalized results
- ✅ No filter bubble

## Advantages over Bing

| Feature | DuckDuckGo | Bing |
|---------|------------|------|
| Privacy | ✅ No tracking | ⚠️ Tracks users |
| API Key | ✅ Not required | ⚠️ Required for API |
| Always Available | ✅ Yes | ⚠️ Only with key |
| Domain Diversity | ✅ Yes | ✅ Yes |
| Pagination | ✅ Yes | ✅ Yes |
| HTML Entity Decoding | ✅ Yes | ✅ Yes |

## Troubleshooting

### "No results found"
- Check internet connection
- Try different search terms
- Try broader query

### "Parse error"
- DuckDuckGo may have changed HTML structure
- Tool may need update
- Try again in a few minutes

### Results seem stale
- Use `reset` command to start from page 1
- Results are live from DuckDuckGo

## Technical Details

- **Method**: HTML scraping (POST requests)
- **Rate Limiting**: 1-2 second delay between pages
- **Results per page**: 5 (configurable)
- **Max pages**: ~10 (DuckDuckGo limit)
- **Timeout**: 25 seconds
- **Retries**: Up to 2

## Comparison with Bing Tool

Both tools share the same features:
- Domain diversity enforcement
- Pagination with offset tracking
- HTML entity decoding
- Result deduplication

**Choose DuckDuckGo when:**
- Privacy is a priority
- No API key available
- Want ad-free results

**Choose Bing when:**
- Have API key for official access
- Need guaranteed reliability
- Corporate environment

## Development

To test the tool:

```bash
python tool.py
```

This launches an interactive test harness where you can try searches and see pagination in action.
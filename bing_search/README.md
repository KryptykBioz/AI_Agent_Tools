# Search Tool

Web search tool using Bing Search API for finding current information.

## Setup

1. **Get Bing Search API Key**
   - Go to [Azure Portal](https://portal.azure.com/)
   - Create a Bing Search resource
   - Copy the API key

2. **Configure in `config.json`**
   ```json
   {
     "bing_search_api_key": "your_api_key_here",
     "bing_search_endpoint": "https://api.bing.microsoft.com/v7.0/search"
   }
   ```

3. **Enable in Controls**
   - Set `USE_SEARCH = True` in `personality/controls.py`

## Usage

The agent can use search automatically when:
- Asked about current events or news
- Needing recent information
- Questions about topics that change frequently

### Examples

**User:** "What's the latest news about AI?"
**Agent:** Uses `{"tool": "search", "args": ["latest AI news"]}`

**User:** "Who won the Super Bowl?"
**Agent:** Uses `{"tool": "search", "args": ["Super Bowl winner"]}`

## Features

- **Automatic Query Optimization**: Short, concise queries (1-6 words)
- **Top 5 Results**: Returns most relevant results
- **Source Attribution**: Each result includes title, snippet, and URL
- **Timeout Protection**: 30s timeout with retry logic
- **Rate Limiting**: 3s cooldown between searches

## Architecture

```
search/
├── decider.py          # Decides when to execute search
├── executor.py         # Initializes and executes
├── handler.py          # Manages async execution
├── interface.py        # Bing API integration
├── information.json    # Tool metadata
└── README.md          # This file
```

## Troubleshooting

### "No API key configured"
- Check `config.json` has `bing_search_api_key`
- Verify API key is valid in Azure Portal

### "Request timed out"
- Check internet connection
- Verify Bing API endpoint is accessible
- Try reducing search query complexity

### "No results found"
- Try different search terms
- Check if query is too specific
- Verify API quota hasn't been exceeded
# China Trending MCP Server

MCP Server aggregating trending topics from Chinese social media platforms — Weibo hot search and Zhihu hot list. Designed for AI agents to access real-time Chinese trending data.

## Features

| Tool | Description | Source |
|------|-------------|--------|
| `get_weibo_hot` | Get Weibo hot search Top 50 with rank, title, heat score, and summary | weibo.com |
| `get_zhihu_hot` | Get Zhihu hot list Top 50 with rank and question title | zhihu.com |

## Installation

```bash
pip install git+https://github.com/521w/china-trending-mcp.git
```

Or from source:

```bash
git clone https://github.com/521w/china-trending-mcp.git
cd china-trending-mcp
pip install -e .
```

## Usage

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "china-trending": {
      "command": "python3",
      "args": ["-m", "china_trending_mcp.server"]
    }
  }
}
```

## Why This Server

- **Real data**: Calls official Weibo and Zhihu APIs, not scraped content
- **Zero setup**: No API keys required — works out of the box
- **AI-native output**: Formatted as clean Chinese text, optimized for LLM reading
- **Reliable**: Full error handling with timeouts and graceful degradation

## Use Cases

- Content creators finding trending topics for WeChat/Official Accounts
- AI agents needing real-time Chinese social sentiment
- Social media monitoring and trend analysis

## API Details

### Weibo Hot Search

- **Endpoint**: `https://weibo.com/ajax/side/hotSearch`
- **Required headers**: Mobile User-Agent + Referer
- **Returns**: `data.realtime` array with `word`, `num`, `rank`, `note`

### Zhihu Hot List

- **Endpoint**: `https://www.zhihu.com/api/v4/search/top_search`
- **Required headers**: Mobile User-Agent
- **Returns**: `top_search.words` array with `query`

## Requirements

- Python >= 3.10
- mcp >= 1.0.0
- requests >= 2.28.0

## License

MIT
# China Trending MCP Server

A lightweight MCP server that gives AI agents real-time Chinese trend signals from Weibo Hot Search and Zhihu Hot List.

It is designed for agents that need to monitor public topics, discover content ideas, or summarize what Chinese social platforms are discussing right now.

## What It Does

- Fetches Weibo Hot Search topics
- Fetches Zhihu Hot List topics
- Returns clean, LLM-readable Chinese text
- Works without API keys
- Exposes data through standard MCP tools

## Tools

| Tool | Description | Source |
| --- | --- | --- |
| `get_weibo_hot` | Get Weibo hot search Top 50 with rank, title, heat score, and summary | Weibo |
| `get_zhihu_hot` | Get Zhihu hot list Top 50 with rank and question title | Zhihu |

## Good For

- AI content planning
- Daily trend briefings
- Social topic monitoring
- WeChat Official Account topic discovery
- Chinese market and sentiment observation
- Agent workflows that need live public signals

## Installation

```bash
pip install git+https://github.com/521w/china-trending-mcp.git
```

Or install from source:

```bash
git clone https://github.com/521w/china-trending-mcp.git
cd china-trending-mcp
pip install -e .
```

## MCP Configuration

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

## Example Agent Tasks

- "Summarize today's top Chinese internet topics."
- "Find 5 article ideas from today's Weibo and Zhihu trends."
- "Compare entertainment, finance, and technology topics in today's hot lists."
- "Generate a daily China trend briefing for content creators."

## Why This Server

- **No API key**: usable out of the box
- **Agent-native**: returns concise text that LLMs can directly reason over
- **Small surface area**: focused on high-signal trend sources
- **Easy to productize**: useful as a daily briefing, content research, or monitoring component

## Requirements

- Python >= 3.10
- `mcp >= 1.0.0`
- `requests >= 2.28.0`

## Notes

This project depends on public platform endpoints. If Weibo or Zhihu changes their response format or access rules, the server may need updates.

## License

MIT

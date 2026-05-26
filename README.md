# 🔥 中国热搜聚合 MCP 服务器

聚合微博热搜榜和知乎热榜的 MCP 工具服务器，可接入 Claude Desktop、Cursor 等支持 MCP 协议的 AI 客户端。

## ✨ 功能

| 工具 | 说明 | 数据源 |
|------|------|--------|
| `get_weibo_hot` | 获取微博热搜榜 Top50，含排名、标题、热度、摘要 | weibo.com |
| `get_zhihu_hot` | 获取知乎热榜 Top50，含排名、问题标题 | zhihu.com |

## 📦 安装

### 环境要求

- Python >= 3.10
- pip

### 步骤

```bash
cd ~/china-trending-mcp
pip install -e .
```

## 🚀 使用

### 直接运行

```bash
# 方式一：模块运行
python3 -m china_trending_mcp.server

# 方式二：命令行入口
china-trending-mcp
```

### 接入 Claude Desktop

在 Claude Desktop 配置文件中添加：

```json
{
  "mcpServers": {
    "china-trending": {
      "command": "python3",
      "args": ["-m", "china_trending_mcp.server"],
      "cwd": "/data/data/com.termux/files/home/china-trending-mcp"
    }
  }
}
```

### 接入 Cursor

在 Cursor 的 MCP 设置中添加：

```json
{
  "mcpServers": {
    "china-trending": {
      "command": "python3",
      "args": ["-m", "china_trending_mcp.server"],
      "cwd": "/data/data/com.termux/files/home/china-trending-mcp"
    }
  }
}
```

## 🛠️ 技术栈

- **MCP SDK**: 标准 MCP Python SDK，使用 stdio 传输协议
- **HTTP 请求**: requests 库，带完整的错误处理和超时保护
- **数据格式**: 纯中文文本输出，适合终端和 AI 阅读

## 📁 项目结构

```
china-trending-mcp/
├── pyproject.toml              # 项目配置和依赖
├── README.md                   # 项目说明
├── .gitignore                  # Git 忽略规则
└── china_trending_mcp/
    ├── __init__.py             # 包初始化
    └── server.py               # MCP 服务器主文件
```

## 🌐 API 说明

### 微博热搜

- **接口**: `https://weibo.com/ajax/side/hotSearch`
- **Headers**: 需模拟移动端 User-Agent 和 Referer
- **返回**: `data.realtime` 数组，每项包含 `word`(标题)、`num`(热度)、`rank`(排名)、`note`(摘要)

### 知乎热榜

- **接口**: `https://www.zhihu.com/api/v4/search/top_search`
- **Headers**: 需模拟移动端 User-Agent
- **返回**: `top_search.words` 数组，每项包含 `query`(标题)

## 📝 License

MIT
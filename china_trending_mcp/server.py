"""
中国热搜聚合 MCP 服务器

提供微博热搜榜和知乎热榜查询工具。
使用 MCP stdio 模式运行，可供 Claude Desktop、Cursor 等 MCP 客户端使用。

启动方式：
    python3 -m china_trending_mcp.server
    或
    china-trending-mcp
"""

import asyncio
import json
from typing import Any

import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ---------- 全局配置 ----------

# 请求超时时间（秒）
REQUEST_TIMEOUT = 15

# 微博热搜 API
WEIBO_API_URL = "https://weibo.com/ajax/side/hotSearch"
WEIBO_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/16.0 Mobile/15E148 Safari/604.1"
    ),
    "Referer": "https://weibo.com/",
    "Accept": "application/json, text/plain, */*",
}

# 知乎热榜 API
ZHIHU_API_URL = "https://www.zhihu.com/api/v4/search/top_search"
ZHIHU_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/16.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept": "application/json, text/plain, */*",
}

# ---------- 网络请求 ----------


def _safe_request(url: str, headers: dict) -> tuple[bool, Any]:
    """
    安全地发起 HTTP GET 请求，返回 (成功标志, 数据或错误信息)。

    不会因为网络问题而崩溃，始终返回可处理的结果。
    """
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return True, resp.json()
    except requests.exceptions.Timeout:
        return False, "请求超时，请稍后重试"
    except requests.exceptions.ConnectionError:
        return False, "网络连接失败，请检查网络"
    except requests.exceptions.HTTPError as e:
        return False, f"HTTP 错误：{e.response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"请求异常：{str(e)}"
    except json.JSONDecodeError:
        return False, "API 返回数据格式异常"


# ---------- 格式化输出 ----------


def _format_weibo(items: list[dict]) -> str:
    """格式化微博热搜数据为可读的中文文本。"""
    if not items:
        return "微博热搜榜暂无数据"

    lines = ["🔥 微博热搜榜 Top50\n"]
    for item in items[:50]:
        rank = item.get("rank", "?")
        word = item.get("word", "").strip()
        num = item.get("num", 0)
        note = item.get("note", "").strip()

        # 构造每行：序号. 标题  热度
        line = f"{rank:>2}. {word}"
        if num:
            # 热度值格式化（万为单位更直观）
            if num >= 10000:
                line += f"  🔥{num / 10000:.1f}万"
            else:
                line += f"  🔥{num}"
        if note:
            line += f"\n    📌 {note}"
        lines.append(line)

    lines.append(f"\n共 {len(items)} 条热搜")
    return "\n".join(lines)


def _format_zhihu(items: list[dict]) -> str:
    """格式化知乎热榜数据为可读的中文文本。"""
    if not items:
        return "知乎热榜暂无数据"

    lines = ["🧀 知乎热榜 Top50\n"]
    for idx, item in enumerate(items[:50], start=1):
        query = item.get("query", "").strip()
        if query:
            lines.append(f"{idx:>2}. {query}")

    lines.append(f"\n共 {len(items)} 条热榜")
    return "\n".join(lines)


# ---------- MCP 工具定义 ----------


async def get_weibo_hot() -> str:
    """
    获取微博热搜榜 Top50。

    数据来源：https://weibo.com/ajax/side/hotSearch
    返回格式化的中文热搜列表，包含排名、标题、热度和摘要。
    """
    ok, data = _safe_request(WEIBO_API_URL, WEIBO_HEADERS)
    if not ok:
        return f"❌ 微博热搜获取失败：{data}"

    # 微博 API 结构：data.realtime 是热搜数组
    realtime = data.get("data", {}).get("realtime", [])
    if not realtime:
        return "⚠️ 微博热搜榜暂时无数据，请稍后再试"

    return _format_weibo(realtime)


async def get_zhihu_hot() -> str:
    """
    获取知乎热榜 Top50。

    数据来源：https://www.zhihu.com/api/v4/search/top_search
    返回格式化的中文热榜列表，包含排名和标题。
    """
    ok, data = _safe_request(ZHIHU_API_URL, ZHIHU_HEADERS)
    if not ok:
        return f"❌ 知乎热榜获取失败：{data}"

    # 知乎 API 结构：top_search.words 是热榜数组
    top_search = data.get("top_search", {})
    words = top_search.get("words", [])
    if not words:
        return "⚠️ 知乎热榜暂时无数据，请稍后再试"

    return _format_zhihu(words)


# ---------- MCP 服务器 ----------


def _make_server() -> Server:
    """创建并配置 MCP 服务器实例。"""
    server = Server("china-trending-mcp")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """列出所有可用工具。"""
        return [
            Tool(
                name="get_weibo_hot",
                description="获取微博热搜榜 Top50。返回实时热搜列表，包含排名、标题、热度和话题摘要。",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            Tool(
                name="get_zhihu_hot",
                description="获取知乎热榜 Top50。返回知乎当前热门话题列表，包含排名和问题标题。",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """调用指定的工具并返回结果。"""
        if name == "get_weibo_hot":
            result = await get_weibo_hot()
        elif name == "get_zhihu_hot":
            result = await get_zhihu_hot()
        else:
            result = f"❌ 未知工具：{name}"

        return [TextContent(type="text", text=result)]

    return server


async def _run_async() -> None:
    """异步启动 MCP stdio 服务器。"""
    server = _make_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    """入口函数，启动 MCP stdio 服务器。"""
    try:
        asyncio.run(_run_async())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
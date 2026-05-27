"""
中国热搜聚合 MCP 服务器
=======================
提供微博热搜榜和知乎热榜查询工具。

工具列表：
- get_weibo_hot: 获取微博热搜 Top50
- get_zhihu_hot: 获取知乎热榜 Top50
"""

import asyncio
import json
import logging
import sys
from typing import Any
from functools import lru_cache

import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ── 日志配置 ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("china-trending-mcp")

# ── 版本 ──────────────────────────────────────────────
VERSION = "0.2.0"

# ── 常量 ──────────────────────────────────────────────

REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
RETRY_DELAY = 1.0

# 微博热搜 API
WEIBO_API_URL = "https://weibo.com/ajax/side/hotSearch"
WEIBO_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.0 Mobile/15E148 Safari/604.1"
    ),
    "Referer": "https://weibo.com/",
    "Accept": "application/json, text/plain, */*",
}

# 知乎热榜 API
ZHIHU_API_URL = "https://www.zhihu.com/api/v4/search/top_search"
ZHIHU_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept": "application/json, text/plain, */*",
}

# ── HTTP 客户端 ─────────────────────────────────────────


class HTTPClient:
    """带连接池和重试的 HTTP 客户端"""
    
    def __init__(self):
        self._session: requests.Session | None = None
    
    @property
    def session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=10,
                pool_maxsize=10,
                max_retries=0,
            )
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)
        return self._session
    
    def get(self, url: str, headers: dict, timeout: int = REQUEST_TIMEOUT) -> requests.Response:
        """带重试的 GET 请求"""
        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = self.session.get(url, headers=headers, timeout=timeout)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                last_error = e
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {url} - {e}")
                if attempt < MAX_RETRIES - 1:
                    import time
                    time.sleep(RETRY_DELAY * (attempt + 1))
        
        raise last_error or requests.RequestException("未知错误")


http_client = HTTPClient()

# ── 网络请求 ──────────────────────────────────────────


def _safe_request(url: str, headers: dict) -> tuple[bool, Any]:
    """安全地发起 HTTP GET 请求，返回 (成功标志, 数据或错误信息)。"""
    try:
        resp = http_client.get(url, headers)
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


# ── 格式化输出 ──────────────────────────────────────────


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


# ── MCP 工具定义 ────────────────────────────────────────


async def get_weibo_hot() -> str:
    """
    获取微博热搜榜 Top50。

    数据来源：https://weibo.com/ajax/side/hotSearch
    返回格式化的中文热搜列表，包含排名、标题、热度和摘要。
    """
    logger.info("获取微博热搜...")
    ok, data = _safe_request(WEIBO_API_URL, WEIBO_HEADERS)
    if not ok:
        logger.warning(f"微博热搜获取失败: {data}")
        return f"❌ 微博热搜获取失败：{data}"

    # 微博 API 结构：data.realtime 是热搜数组
    realtime = data.get("data", {}).get("realtime", [])
    if not realtime:
        logger.warning("微博热搜榜无数据")
        return "⚠️ 微博热搜榜暂时无数据，请稍后再试"

    logger.info(f"微博热搜获取成功: {len(realtime)} 条")
    return _format_weibo(realtime)


async def get_zhihu_hot() -> str:
    """
    获取知乎热榜 Top50。

    数据来源：https://www.zhihu.com/api/v4/search/top_search
    返回格式化的中文热榜列表，包含排名和标题。
    """
    logger.info("获取知乎热榜...")
    ok, data = _safe_request(ZHIHU_API_URL, ZHIHU_HEADERS)
    if not ok:
        logger.warning(f"知乎热榜获取失败: {data}")
        return f"❌ 知乎热榜获取失败：{data}"

    # 知乎 API 结构：top_search.words 是热榜数组
    top_search = data.get("top_search", {})
    words = top_search.get("words", [])
    if not words:
        logger.warning("知乎热榜无数据")
        return "⚠️ 知乎热榜暂时无数据，请稍后再试"

    logger.info(f"知乎热榜获取成功: {len(words)} 条")
    return _format_zhihu(words)


# ── MCP 服务器 ──────────────────────────────────────────


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
        try:
            if name == "get_weibo_hot":
                result = await get_weibo_hot()
            elif name == "get_zhihu_hot":
                result = await get_zhihu_hot()
            else:
                result = f"❌ 未知工具：{name}"

            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.exception(f"工具执行失败: {name}")
            return [TextContent(type="text", text=f"❌ 执行失败: {e}")]

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
    logger.info(f"China Trending MCP Server v{VERSION} 启动")
    try:
        asyncio.run(_run_async())
    except KeyboardInterrupt:
        logger.info("服务器已停止")
        pass


if __name__ == "__main__":
    main()
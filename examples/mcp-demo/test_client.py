# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.2,<2"]
# ///
"""不依赖任何 AI，直接以“MCP 客户端”的身份测试 server.py。

运行：  uv run test_client.py
这就是 AI 助手在背后做的事：启动服务 → 握手 → 问有哪些工具 → 调用工具。
"""
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = str(Path(__file__).with_name("server.py"))


async def call(session: ClientSession, name: str, args: dict) -> str:
    result = await session.call_tool(name, args)
    text = result.content[0].text if result.content else ""
    return ("❌ 被拒绝/出错: " if result.isError else "✅ ") + text[:160].replace("\n", " ")


async def main() -> int:
    params = StdioServerParameters(command="uv", args=["run", SERVER])
    failures = 0
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()                                     # 1. 握手
            tools = [t.name for t in (await s.list_tools()).tools]   # 2. 问有哪些工具
            print("工具:", tools)
            print("资源:", [str(r.uri) for r in (await s.list_resources()).resources])
            print("提示词:", [p.name for p in (await s.list_prompts()).prompts])
            print()

            # 3. 应该成功的调用
            for name, args in [("list_tables", {}),
                               ("describe_table", {"table": "orders"}),
                               ("monthly_sales", {"month": "2026-03"}),
                               ("run_query", {"sql": "SELECT city, COUNT(*) FROM customers GROUP BY city"})]:
                out = await call(s, name, args)
                print(f"{name:15s}{out}")
                failures += out.startswith("❌")

            # 4. 应该被拒绝的调用（安全测试：这些必须失败，否则就是漏洞）
            print("\n--- 安全测试：下面每一条都必须被拒绝 ---")
            for label, name, args in [
                ("删表", "run_query", {"sql": "DROP TABLE orders"}),
                ("改数据", "run_query", {"sql": "UPDATE orders SET amount=0"}),
                ("挂载外部库", "run_query", {"sql": "ATTACH DATABASE '/tmp/x.db' AS x"}),
                ("月份格式错误", "monthly_sales", {"month": "2026-3; DROP TABLE orders"}),
                ("不存在的表", "describe_table", {"table": "no_such_table"}),
            ]:
                out = await call(s, name, args)
                ok = out.startswith("❌")
                print(f"{'通过' if ok else '漏洞!'}  {label:8s}{out}")
                failures += (not ok)
    print("\n结果：", "全部通过 ✅" if failures == 0 else f"{failures} 项不符合预期 ❌")
    return failures


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

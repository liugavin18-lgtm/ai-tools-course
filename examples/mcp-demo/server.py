# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.2,<2"]
# ///
"""示例 MCP 服务：只读的销售数据库查询。

运行方式（会自动装依赖）：  uv run server.py
包含 MCP 的三类能力：Tool（工具）、Resource（资源）、Prompt（提示词模板）。
"""
import re
import sqlite3
import time
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DB = Path(__file__).with_name("sales_demo.db")
MAX_ROWS = 200      # 单次最多返回行数，防止一次拉爆上下文
TIMEOUT_S = 10      # 单次查询最长时间

mcp = FastMCP("demo-db")

# ---- 只读防线：数据库层面拒绝一切“写”类操作 ----
_ALLOWED = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ,
            sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE}


def _authorize(action, arg1, arg2, dbname, source):
    if action in _ALLOWED:
        return sqlite3.SQLITE_OK
    # 查字段用的 PRAGMA table_info 本身只读，单独放行；其他 PRAGMA 一律拒绝
    if action == sqlite3.SQLITE_PRAGMA and arg1 == "table_info":
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def connect() -> sqlite3.Connection:
    if not DB.exists():
        raise ValueError("找不到 sales_demo.db，请先运行 make_demo_db.py 生成示例库")
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)      # 第一道：只读打开
    con.set_authorizer(_authorize)                              # 第二道：只放行读操作
    deadline = time.time() + TIMEOUT_S                          # 第三道：超时中断
    con.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 100_000)
    return con


# ---- Tool：AI 可以主动调用的“动作” ----
@mcp.tool()
def list_tables() -> list[str]:
    """列出数据库里所有的表名。不确定有哪些数据时，先调用这个。"""
    with connect() as con:
        return [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]


@mcp.tool()
def describe_table(table: str) -> list[dict]:
    """查看某张表的字段名和类型。写 SQL 之前先调用，避免猜错字段名。"""
    with connect() as con:
        if table not in [r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")]:
            raise ValueError(f"表 {table!r} 不存在，请先用 list_tables 查看")
        return [{"name": c[1], "type": c[2]}
                for c in con.execute(f'PRAGMA table_info("{table}")')]


@mcp.tool()
def run_query(sql: str, limit: int = 50) -> dict:
    """执行只读 SQL（只支持 SELECT）。最多返回 200 行。
    需要精确统计时优先用 SQL 的 GROUP BY / SUM，不要把明细全拉回来自己算。"""
    limit = max(1, min(limit, MAX_ROWS))
    with connect() as con:
        try:
            cur = con.execute(sql)
            rows = cur.fetchmany(limit + 1)
        except sqlite3.DatabaseError as e:
            raise ValueError(f"查询被拒绝或出错：{e}（本服务只读，仅支持 SELECT）")
        return {"columns": [d[0] for d in cur.description or []],
                "rows": [list(r) for r in rows[:limit]],
                "truncated": len(rows) > limit}


@mcp.tool()
def monthly_sales(month: str) -> dict:
    """按“意图”设计的高层工具：查询某个月的销售汇总。month 格式 YYYY-MM，例如 2026-03。
    比让 AI 自己拼 SQL 更稳：参数固定、结果口径统一。"""
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month):
        raise ValueError("month 格式应为 YYYY-MM，例如 2026-03")
    with connect() as con:
        orders, qty, amount = con.execute(
            "SELECT COUNT(*), COALESCE(SUM(qty),0), COALESCE(SUM(amount),0) "
            "FROM orders WHERE substr(order_date,1,7)=?", (month,)).fetchone()   # 参数化，防注入
        top = con.execute(
            "SELECT p.name, SUM(o.amount) s FROM orders o JOIN products p ON p.id=o.product_id "
            "WHERE substr(o.order_date,1,7)=? GROUP BY p.name ORDER BY s DESC LIMIT 3",
            (month,)).fetchall()
    return {"month": month, "orders": orders, "qty": qty, "amount": amount,
            "top_products": [{"name": n, "amount": a} for n, a in top]}


# ---- Resource：AI 可以“阅读”的资料（不执行动作） ----
@mcp.resource("schema://tables")
def schema() -> str:
    """整个数据库的建表语句，作为参考资料。"""
    with connect() as con:
        return "\n\n".join(r[0] for r in con.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"))


# ---- Prompt：预设好的提问模板，用户可一键选用 ----
@mcp.prompt()
def analyze_sales(question: str) -> str:
    """销售分析模板：规定分析步骤，让每次分析都按同一套方法来。"""
    return (f"请分析销售数据并回答：{question}\n"
            "步骤：1) 先用 list_tables / describe_table 了解结构；"
            "2) 用 run_query 或 monthly_sales 取数；"
            "3) 给出结论，并标明数据口径和时间范围；4) 数字必须来自查询结果，不得编造。")


if __name__ == "__main__":
    mcp.run()

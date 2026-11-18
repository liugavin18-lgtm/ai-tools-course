# 自己做一个

## 案例：只读数据库查询服务
需求：让 AI 能查公司本地的 SQLite 数据库，但**绝对不能改数据**。

这是最适合入门的 MCP：简单、有用、安全。

## 设计思路
先想清楚三件事：

1. **开放哪些动作**：列出有哪些库、看表结构、执行查询。
2. **怎么保证只读**：不靠“叮嘱 AI 别乱改”，而是**程序上就做不到写入**。
3. **怎么防止拖垮电脑**：限制返回行数、设置超时。

## 核心代码（精简版）

```python
import sqlite3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo-db")
DB_PATH = "sales_demo.db"   # 示例库，数据均为虚构

# 只允许“读”类操作
ALLOWED = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ,
           sqlite3.SQLITE_FUNCTION}

def connect():
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)  # 只读模式打开
    con.set_authorizer(
        lambda action, *_: sqlite3.SQLITE_OK if action in ALLOWED
        else sqlite3.SQLITE_DENY                                 # 其他一律拒绝
    )
    return con

@mcp.tool()
def query(sql: str, limit: int = 100) -> list:
    """对示例库执行只读 SQL，最多返回 limit 行。"""
    con = connect()
    try:
        return con.execute(sql).fetchmany(min(limit, 500))
    finally:
        con.close()

if __name__ == "__main__":
    mcp.run()
```

## 关键点讲解

!!! success "双重保险"
    - `mode=ro`：数据库文件以只读方式打开。
    - `set_authorizer`：即使有人构造了 `CREATE`、`DROP`、`ATTACH` 之类的语句，也会被拒绝。

!!! tip "函数上方的说明文字很重要"
    `"""对示例库执行只读 SQL..."""` 这句话会被 AI 读到，AI 靠它判断“什么时候该用这个工具”。写得越清楚，AI 越会用。

## 测试：一定要验证“写不进去”
装好后，让 AI 试一条 `CREATE TABLE x(a)`。正确结果是**被拒绝**。能拒绝，才算真正只读。

## 扩展思路
- 加一个“查看表结构”的工具
- 加一个“查看定时任务是否运行成功”的工具
- 需要“写”的功能时，**单独做成另一个服务**，并加上人工审批，不要和只读服务混在一起

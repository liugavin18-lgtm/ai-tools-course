"""生成示例数据库 sales_demo.db。所有数据均为随机生成的虚构数据。"""
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB = Path(__file__).with_name("sales_demo.db")
random.seed(42)  # 固定随机种子，每个学员生成的数据一致

CITIES = ["上海", "北京", "深圳", "杭州", "成都", "武汉"]
PRODUCTS = [("入门课程", 199), ("进阶课程", 599), ("企业内训", 4800),
            ("一对一辅导", 1200), ("资料包", 99)]


def main() -> None:
    DB.unlink(missing_ok=True)
    con = sqlite3.connect(DB)
    con.executescript("""
        CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT, city TEXT);
        CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT, price REAL);
        CREATE TABLE orders(
            id INTEGER PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(id),
            product_id  INTEGER REFERENCES products(id),
            qty INTEGER, amount REAL, order_date TEXT
        );
        CREATE INDEX idx_orders_date ON orders(order_date);
    """)
    con.executemany("INSERT INTO customers VALUES(?,?,?)",
                    [(i, f"客户{i:03d}", random.choice(CITIES)) for i in range(1, 51)])
    con.executemany("INSERT INTO products VALUES(?,?,?)",
                    [(i + 1, n, p) for i, (n, p) in enumerate(PRODUCTS)])
    start = date(2026, 1, 1)
    rows = []
    for oid in range(1, 401):
        pid = random.randint(1, len(PRODUCTS))
        qty = random.randint(1, 3)
        d = start + timedelta(days=random.randint(0, 300))
        rows.append((oid, random.randint(1, 50), pid, qty,
                     PRODUCTS[pid - 1][1] * qty,
                     d.isoformat()))
    con.executemany("INSERT INTO orders VALUES(?,?,?,?,?,?)", rows)
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    print(f"已生成 {DB.name}：50 位客户、{len(PRODUCTS)} 个产品、{n} 笔订单（均为虚构）")


if __name__ == "__main__":
    main()

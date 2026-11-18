"""生成课程里的图表与动画（SVG，自带背景，亮色/深色主题下都清晰）。

运行：python3 tools/make_diagrams.py        输出到 docs/assets/img/
动画使用 SVG 原生 SMIL，无需任何 JS 或外部库，浏览器直接播放。
图表数据来自示例库 examples/mcp-demo/sales_demo.db（虚构数据）。
"""
import html
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "assets" / "img"
OUT.mkdir(parents=True, exist_ok=True)

FONT = 'font-family="PingFang SC, Hiragino Sans GB, Noto Sans CJK SC, Microsoft YaHei, sans-serif"'
C = dict(bg="#f6f8fb", line="#c5cfdd", text="#1f2937", mute="#6b7280", pri="#3f51b5", pril="#e8eaf6",
         ok="#2e7d32", okl="#e8f5e9", bad="#c62828", badl="#fdecea", amb="#a35f00", ambl="#fff4dc",
         white="#ffffff")


def esc(s):
    return html.escape(s, quote=False)


def marker(name, color):
    return (f'<marker id="a-{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" '
            f'markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker>')


MARKERS = "".join(marker(n, C[n]) for n in ("pri", "ok", "bad", "mute", "amb"))


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" {FONT}>'
            f'<title>{esc(title)}</title><defs>{MARKERS}</defs>'
            f'<rect width="{w}" height="{h}" rx="14" fill="{C["bg"]}"/>{body}</svg>')


def box(x, y, w, h, fill, stroke, rx=10, sw=1.5):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>')


def text(x, y, s, size=15, anchor="middle", fill=None, weight="normal"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
            f'fill="{fill or C["text"]}" font-weight="{weight}">{esc(s)}</text>')


def lines(x, y, rows, size=15, gap=22, **kw):
    return "".join(text(x, y + i * gap, r, size, **kw) for i, r in enumerate(rows))


def line(x1, y1, x2, y2, color, w=2, dash=None, arrow=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#a-{arrow})"' if arrow else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}"{d}{m}/>'


def anim_opacity(start, end=0.95, dur=20, fade=0.015):
    """从 start 起淡入，保持到 end，再淡出（所有元素同周期，整体同步循环）。"""
    return (f'<animate attributeName="opacity" values="0;0;1;1;0" '
            f'keyTimes="0;{start:.4f};{start + fade:.4f};{end:.4f};1" dur="{dur}s" repeatCount="indefinite"/>')


def cylinder(cx, cy, w, h, label):
    rx, ry = w / 2, 12
    return (f'<path d="M{cx - rx},{cy - h / 2} v{h} a{rx},{ry} 0 0 0 {w},0 v{-h} a{rx},{ry} 0 0 0 {-w},0 z" '
            f'fill="{C["pril"]}" stroke="{C["pri"]}" stroke-width="1.5"/>'
            f'<ellipse cx="{cx}" cy="{cy - h / 2}" rx="{rx}" ry="{ry}" fill="{C["white"]}" stroke="{C["pri"]}" stroke-width="1.5"/>'
            + text(cx, cy + 8, label, 14, weight="bold", fill=C["pri"]))


# ------------------------------------------------------------------ 1. M×N 问题
def mn_problem():
    b = []
    b.append(text(210, 36, "没有 MCP：每个 AI × 每个工具，各接一套", 16, weight="bold"))
    b.append(text(650, 36, "有了 MCP：大家都按同一个标准接", 16, weight="bold", fill=C["pri"]))
    ais, tools = ["Claude", "Kimi", "其他 AI"], ["数据库", "日历", "出图"]
    ys = [90, 170, 250]
    for i, ya in enumerate(ys):          # 左：9 条线
        for yt in ys:
            b.append(line(135, ya + 20, 285, yt + 20, C["bad"], 1.4))
    for i, y in enumerate(ys):
        b.append(box(40, y, 95, 40, C["white"], C["line"]) + text(87, y + 26, ais[i], 14))
        b.append(box(285, y, 95, 40, C["white"], C["line"]) + text(332, y + 26, tools[i], 14))
    b.append(text(210, 330, "3 × 3 = 9 套对接，工具越多越累", 14, fill=C["bad"], weight="bold"))
    for i, y in enumerate(ys):           # 右：6 条线 + 枢纽
        b.append(line(485, y + 20, 570, 190, C["pri"], 1.6))
        b.append(line(650, 190, 735, y + 20, C["pri"], 1.6))
    b.append(box(570, 110, 80, 160, C["pri"], C["pri"], rx=12) + text(610, 196, "MCP", 20, fill=C["white"], weight="bold"))
    for i, y in enumerate(ys):
        b.append(box(395, y, 90, 40, C["white"], C["line"]) + text(440, y + 26, ais[i], 14))
        b.append(box(735, y, 95, 40, C["white"], C["line"]) + text(782, y + 26, tools[i], 14))
    b.append(text(640, 330, "3 + 3 = 6 个接口，新增工具只需做 1 个", 14, fill=C["ok"], weight="bold"))
    b.append(line(425, 60, 425, 310, C["line"], 1, dash="4 4"))
    return svg(860, 350, "".join(b), "没有 MCP 与有 MCP 的对接数量对比")


# ------------------------------------------------------------------ 2. 三个角色
def roles():
    b = []
    b.append(box(20, 30, 340, 270, C["white"], C["pri"], rx=16, sw=2))
    b.append(text(190, 58, "AI 应用（Host）", 16, weight="bold", fill=C["pri"]))
    b.append(text(190, 78, "例：Claude Code、Kimi", 12, fill=C["mute"]))
    b.append(box(50, 100, 280, 56, C["pril"], C["pri"]) + text(190, 124, "AI 模型", 15, weight="bold")
             + text(190, 144, "听懂你的话，决定该用哪个工具", 12, fill=C["mute"]))
    b.append(line(190, 158, 190, 200, C["pri"], 2, arrow="pri"))
    b.append(box(50, 202, 280, 56, C["pril"], C["pri"]) + text(190, 226, "MCP 客户端", 15, weight="bold")
             + text(190, 246, "负责“说 MCP”，每连一个服务就有一个", 12, fill=C["mute"]))
    b.append(box(540, 30, 300, 120, C["white"], C["ok"], rx=14, sw=2))
    b.append(text(690, 58, "MCP 服务（本地）", 15, weight="bold", fill=C["ok"]))
    b.append(text(690, 80, "你写的 Python 程序", 12, fill=C["mute"]))
    b.append(text(690, 106, "Tool · Resource · Prompt", 13))
    b.append(text(690, 130, "→ 本机的数据库、文件", 12, fill=C["mute"]))
    b.append(box(540, 190, 300, 110, C["white"], C["amb"], rx=14, sw=2))
    b.append(text(690, 218, "MCP 服务（远程）", 15, weight="bold", fill=C["amb"]))
    b.append(text(690, 240, "别人提供的云端服务", 12, fill=C["mute"]))
    b.append(text(690, 266, "出图、在线文档……", 13))
    b.append(text(690, 286, "常需要登录授权", 12, fill=C["mute"]))
    b.append(line(332, 226, 538, 100, C["ok"], 2.5, arrow="ok"))
    b.append(text(478, 210, "stdio（本地进程）", 13, fill=C["ok"], weight="bold"))
    b.append(line(332, 240, 538, 245, C["amb"], 2.5, arrow="amb"))
    b.append(text(440, 272, "HTTP（联网）", 13, fill=C["amb"], weight="bold"))
    return svg(860, 330, "".join(b), "MCP 的三个角色：宿主、客户端、服务端")


# ------------------------------------------------------------------ 3. 三类能力
def primitives():
    b = []
    cards = [("Tool 工具", C["pri"], ["谁触发：AI 模型自己决定", "做什么：执行动作、查询数据", "类比：一个可以按的按钮"]),
             ("Resource 资源", C["ok"], ["谁触发：应用或用户选择加载", "做什么：提供可阅读的资料", "类比：一份可以翻阅的资料"]),
             ("Prompt 提示词模板", C["amb"], ["谁触发：用户主动选用", "做什么：预设提问方式和步骤", "类比：一张填空的表单"])]
    for i, (name, col, rows) in enumerate(cards):
        x = 20 + i * 280
        b.append(box(x, 20, 260, 150, C["white"], col, rx=12, sw=2))
        b.append(f'<path d="M{x},32 a12,12 0 0 1 12,-12 h236 a12,12 0 0 1 12,12 v28 h-260 z" fill="{col}"/>')
        b.append(text(x + 130, 48, name, 16, fill=C["white"], weight="bold"))
        for j, r in enumerate(rows):
            b.append(text(x + 16, 92 + j * 28, r, 13.5, anchor="start"))
    b.append(text(430, 202, "日常 90% 的场景，只用 Tool 就够了", 15, weight="bold", fill=C["pri"]))
    return svg(860, 226, "".join(b), "MCP 服务端的三类能力")


# ------------------------------------------------------------------ 4. 调用流程（动画）
def call_flow():
    W, H = 860, 590
    xs = {"u": 120, "a": 430, "s": 740}
    b = []
    for k, label in (("u", "你"), ("a", "AI 应用（模型 + 客户端）"), ("s", "MCP 服务（你写的程序）")):
        b.append(box(xs[k] - 100, 14, 200, 40, C["pril"], C["pri"]) + text(xs[k], 40, label, 14, weight="bold"))
        b.append(line(xs[k], 56, xs[k], H - 16, C["line"], 1.5, dash="5 5"))
    rows = [  # (kind, from, to, label, color, dashed)
        ("msg", "a", "s", "① 启动服务进程", C["pri"], False),
        ("msg", "a", "s", "② initialize（握手）", C["pri"], False),
        ("msg", "a", "s", "③ tools/list：你有哪些工具？", C["pri"], False),
        ("msg", "s", "a", "③ 返回工具清单（名字、说明、参数）", C["ok"], True),
        ("msg", "u", "a", "你提问：3 月销售额是多少？", C["text"], False),
        ("note", "a", None, "④ 模型判断：该用 monthly_sales", C["amb"], False),
        ("msg", "a", "s", "⑤ tools/call monthly_sales(2026-03)", C["pri"], False),
        ("msg", "s", "a", "⑥ 返回 {订单 39，金额 130955}", C["ok"], True),
        ("msg", "a", "u", "⑦ 回答：3 月共 39 单，约 13.1 万元", C["text"], False),
    ]
    for i, (kind, f, t, label, col, dashed) in enumerate(rows):
        y = 100 + i * 52
        start = 0.04 + i * 0.092
        g = ['<g>', anim_opacity(start)]
        if kind == "msg":
            x1, x2 = xs[f], xs[t]
            d = 8 if x2 > x1 else -8
            g.append(line(x1 + d, y, x2 - d, y, col, 2.2, dash="6 4" if dashed else None,
                          arrow="ok" if col == C["ok"] else ("pri" if col == C["pri"] else "mute")))
            g.append(text((x1 + x2) / 2, y - 9, label, 13.5, fill=col if col != C["text"] else C["text"], weight="bold"))
        else:
            g.append(box(xs[f] + 12, y - 20, 280, 40, C["ambl"], C["amb"]) + text(xs[f] + 152, y + 5, label, 13.5, fill=C["amb"], weight="bold"))
        g.append('</g>')
        b.append("".join(g))
    return svg(W, H, "".join(b), "一次 MCP 工具调用的完整过程（动画）")


# ------------------------------------------------------------------ 5. 只读三道防线（动画）
def readonly_layers():
    W, H = 860, 410
    b = []
    walls = [(280, "① 只读打开", "mode=ro"), (420, "② 授权白名单", "set_authorizer"), (560, "③ 行数与超时", "limit + timeout")]
    for x, t, sub in walls:
        b.append(box(x, 78, 16, 250, C["pril"], C["pri"], rx=4))
        b.append(text(x + 8, 62, t, 14, weight="bold", fill=C["pri"]))
        b.append(text(x + 8, 350, sub, 12, fill=C["mute"]))
    b.append(cylinder(770, 200, 110, 150, "数据库"))
    lanes = [  # (y, label, fill, stroke, tx, start, end, hold_end, result, result_x, result_col)
        (120, "SELECT …  正常查询", C["okl"], C["ok"], 500, 0.02, 0.22, 0.32, "✓ 正常返回结果", 590, C["ok"]),
        (200, "DROP TABLE orders", C["badl"], C["bad"], 214, 0.34, 0.50, 0.62, "✗ 被拒绝：not authorized", 440, C["bad"]),
        (280, "SELECT * 全表（超大）", C["ambl"], C["amb"], 354, 0.64, 0.80, 0.94, "! 只返回前 200 行 / 超时中断", 580, C["amb"]),
    ]
    for y, label, fill, stroke, tx, s, e, hold, res, rx_, rc in lanes:
        packet = box(24, y - 18, 174, 36, fill, stroke, rx=18) + text(111, y + 5, label, 13, weight="bold", fill=stroke)
        b.append(
            f'<g>{anim_opacity(s, hold, fade=0.012)}'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;0 0;{tx} 0;{tx} 0" '
            f'keyTimes="0;{s:.4f};{e:.4f};1" dur="20s" repeatCount="indefinite"/>{packet}</g>')
        ry = y + 46 if tx >= 500 else y + 5      # 包会走到最右侧时，结果文字放到包的下方，避免重叠
        b.append(f'<g>{anim_opacity(e, hold, fade=0.012)}' + text(rx_, ry, res, 13.5, anchor="start", weight="bold", fill=rc) + '</g>')
    b.append(text(430, 390, "三道防线各管一类问题：任何一层失效，另一层仍能拦住", 14, weight="bold"))
    return svg(W, H, "".join(b), "只读服务的三道防线（动画）")


# ------------------------------------------------------------------ 6. 审批闸门
def approval_gate():
    b = []
    b.append(text(24, 30, "AI 一侧", 13, anchor="start", fill=C["mute"], weight="bold"))
    b.append(text(24, 192, "人 一侧", 13, anchor="start", fill=C["mute"], weight="bold"))
    b.append(line(24, 174, 836, 174, C["line"], 1, dash="4 4"))
    ai = [(24, "① 查余额", C["white"], C["pri"]), (192, "② 提交申请单", C["white"], C["pri"]),
          (360, "③ 停下，等待", C["ambl"], C["amb"]), (528, "⑤ 调用工具", C["white"], C["pri"]),
          (696, "⑥ 核对并记账", C["white"], C["pri"])]
    subs = {"② 提交申请单": "工具·次数·预计花费", "③ 停下，等待": "拿到申请号 REQ-001", "⑤ 调用工具": "批准之后才执行",
            "⑥ 核对并记账": "对比实际花费"}
    for x, t, f, s in ai:
        b.append(box(x, 50, 140, 84, f, s, rx=10, sw=2) + text(x + 70, 86, t, 14.5, weight="bold"))
        if t in subs:
            b.append(text(x + 70, 110, subs[t], 12, fill=C["mute"]))
    for x in (164, 332, 668):
        b.append(line(x, 92, x + 26, 92, C["pri"], 2.2, arrow="pri"))
    b.append(box(300, 206, 260, 76, C["okl"], C["ok"], rx=10, sw=2))
    b.append(text(430, 236, "④ 你审核", 15, weight="bold", fill=C["ok"]))
    b.append(text(430, 262, "回复「批准 REQ-001」", 13.5))
    b.append(line(430, 134, 430, 204, C["amb"], 2.2, arrow="amb"))
    b.append(text(440, 172, "等你的决定", 12, anchor="start", fill=C["amb"]))
    b.append(f'<path d="M560,244 H598 V136" fill="none" stroke="{C["ok"]}" stroke-width="2.2" marker-end="url(#a-ok)"/>')
    b.append(text(610, 214, "批准", 12.5, anchor="start", fill=C["ok"], weight="bold"))
    b.append(text(430, 318, "批准权在人，AI 不能给自己批准；被拦截后不重试、不绕路", 14, weight="bold"))
    return svg(860, 340, "".join(b), "危险操作的人工审批闸门流程")


# ------------------------------------------------------------------ 7. 排错决策树
def debug_tree():
    b = []
    qs = [(["① 在终端手动运行启动命令，", "有报错吗？"], ["修依赖、路径、SDK 版本"], "有报错"),
          (["② 用 test_client 或 Inspector", "测试，通过吗？"], ["修工具代码和输入校验"], "不通过"),
          (["③ 新开会话后，", "AI 能看到这个工具吗？"], ["查绝对路径、/mcp 状态、延迟加载"], "看不到"),
          (["④ AI 会用对吗？"], ["改工具名、描述、参数示例"], "用错")]
    for i, (q, ans, tag) in enumerate(qs):
        y = 24 + i * 128
        b.append(box(30, y, 360, 76, C["pril"], C["pri"], rx=12, sw=2))
        b.append(lines(210, y + (32 if len(q) == 2 else 44), q, 15, 24, weight="bold"))
        b.append(line(390, y + 38, 470, y + 38, C["bad"], 2.2, arrow="bad"))
        b.append(text(430, y + 28, tag, 12.5, fill=C["bad"], weight="bold"))
        b.append(box(472, y + 8, 360, 60, C["badl"], C["bad"], rx=10))
        b.append(lines(652, y + 44, ans, 14))
        b.append(line(210, y + 76, 210, y + 126, C["ok"], 2.2, arrow="ok"))
        b.append(text(222, y + 106, "是 / 没问题", 12.5, anchor="start", fill=C["ok"], weight="bold"))
    b.append(box(30, 536, 360, 44, C["okl"], C["ok"], rx=12, sw=2) + text(210, 564, "完成  ✓", 16, weight="bold", fill=C["ok"]))
    return svg(860, 600, "".join(b), "MCP 排错决策树")


# ------------------------------------------------------------------ 8. 示例数据图表
def demo_chart():
    db = ROOT / "examples" / "mcp-demo" / "sales_demo.db"
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    months = con.execute("SELECT substr(order_date,1,7), SUM(amount) FROM orders GROUP BY 1 ORDER BY 1").fetchall()
    prods = con.execute("SELECT p.name, SUM(o.amount) s FROM orders o JOIN products p ON p.id=o.product_id "
                        "GROUP BY p.name ORDER BY s DESC").fetchall()
    con.close()
    fmt = lambda v: f"{v / 10000:.1f}万"
    b = [text(250, 34, "各月销售额", 16, weight="bold"), text(660, 34, "各产品销售额", 16, weight="bold")]
    mx = max(v for _, v in months)
    bw, base, top = 38, 300, 70
    for i, (m, v) in enumerate(months):
        h = (v / mx) * (base - top)
        x = 40 + i * 47
        b.append(box(x, base - h, bw, h, C["pri"], C["pri"], rx=4, sw=0))
        b.append(text(x + bw / 2, base - h - 6, fmt(v), 11.5))
        b.append(text(x + bw / 2, base + 18, m[5:] + "月", 12, fill=C["mute"]))
    b.append(line(34, base, 520, base, C["line"], 1.5))
    pm = max(v for _, v in prods)
    for i, (n, v) in enumerate(prods):
        y = 70 + i * 48
        w = (v / pm) * 210
        b.append(text(560, y + 20, n, 13, anchor="end"))
        b.append(box(570, y, w, 28, C["ok"], C["ok"], rx=4, sw=0))
        b.append(text(570 + w + 8, y + 20, fmt(v), 12, anchor="start"))
    b.append(text(430, 364, "示例库的虚构数据，由 monthly_sales / run_query 这类工具查询得到", 12.5, fill=C["mute"]))
    return svg(860, 384, "".join(b), "示例销售库：各月与各产品销售额")


if __name__ == "__main__":
    items = {"mn-problem": mn_problem, "roles": roles, "primitives": primitives, "call-flow": call_flow,
             "readonly-layers": readonly_layers, "approval-gate": approval_gate, "debug-tree": debug_tree,
             "demo-chart": demo_chart}
    for name, fn in items.items():
        p = OUT / f"{name}.svg"
        p.write_text(fn(), encoding="utf-8")
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size / 1024:.1f}KB")

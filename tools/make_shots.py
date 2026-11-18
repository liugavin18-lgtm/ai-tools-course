# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.2,<2"]
# ///
"""生成课程里的“真实运行截图”。

内容不是手写的：脚本会真正启动 examples/mcp-demo/server.py，
把运行结果渲染成 HTML，再用本机 Chrome 无头模式截成 PNG。
运行：  uv run tools/make_shots.py      （需要先 python3 examples/mcp-demo/make_demo_db.py）
"""
import asyncio
import html
import json
import os
import subprocess
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "examples" / "mcp-demo"
OUT = ROOT / "docs" / "assets" / "img"
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
FONT = "'PingFang SC','Hiragino Sans GB','Noto Sans CJK SC','Microsoft YaHei',sans-serif"
MONO = "Menlo,'SF Mono',Consolas,'PingFang SC',monospace"


def shoot(page_html: str, name: str, width: int, height: int) -> None:
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "page.html"
        f.write_text(page_html, encoding="utf-8")
        target = OUT / name
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=2", f"--screenshot={target}",
                        f"--window-size={width},{height}", f"file://{f}"],
                       check=True, capture_output=True)
    print(f"{target.relative_to(ROOT)}  {target.stat().st_size / 1024:.0f}KB")


def colorize(line: str) -> str:
    e = html.escape(line)
    for key, cls in (("✅", "ok"), ("通过", "ok"), ("全部通过", "ok"), ("❌", "bad"), ("漏洞!", "bad")):
        e = e.replace(key, f'<span class="{cls}">{key}</span>')
    if line.startswith("---"):
        return f'<span class="dim">{e}</span>'
    return e


def terminal_page(cmd: str, output: str) -> tuple[str, int]:
    rows = [colorize(l) for l in output.splitlines()]
    page = f"""<html><meta charset="utf-8"><body style="margin:0;background:#f6f8fb">
<div style="margin:18px;border-radius:12px;overflow:hidden;box-shadow:0 4px 18px rgba(0,0,0,.25);background:#1e1e2e">
<div style="background:#2b2b3d;padding:10px 14px;display:flex;align-items:center;gap:8px;font:13px {FONT};color:#a6adc8">
<i style="width:12px;height:12px;border-radius:6px;background:#ff5f57"></i><i style="width:12px;height:12px;border-radius:6px;background:#febc2e"></i><i style="width:12px;height:12px;border-radius:6px;background:#28c840"></i>
<span style="margin-left:10px">终端 — examples/mcp-demo</span></div>
<pre style="margin:0;padding:16px 18px;font:13.5px/1.6 {MONO};color:#cdd6f4;white-space:pre-wrap;word-break:break-all"><span style="color:#89b4fa">$ {html.escape(cmd)}</span>
{chr(10).join(rows)}</pre></div>
<style>.ok{{color:#a6e3a1}}.bad{{color:#f38ba8}}.dim{{color:#7f849c}}</style></body></html>"""
    return page, 90 + 24 * (len(rows) + 2)


def card_page(title: str, subtitle: str, body_json: str) -> tuple[str, int]:
    n = body_json.count("\n") + 1
    page = f"""<html><meta charset="utf-8"><body style="margin:0;background:#f6f8fb;font-family:{FONT}">
<div style="margin:18px;border:2px solid #3f51b5;border-radius:14px;background:#fff;overflow:hidden">
<div style="background:#3f51b5;color:#fff;padding:12px 18px;font-size:17px;font-weight:bold">{html.escape(title)}</div>
<div style="padding:10px 18px;color:#6b7280;font-size:13.5px;border-bottom:1px solid #e5e9f0">{html.escape(subtitle)}</div>
<pre style="margin:0;padding:14px 18px;font:13.5px/1.55 {MONO};color:#1f2937;white-space:pre-wrap">{html.escape(body_json)}</pre></div></body></html>"""
    return page, 150 + 22 * n


async def tool_spec() -> str:
    params = StdioServerParameters(command="uv", args=["run", str(DEMO / "server.py")])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tool = next(t for t in (await s.list_tools()).tools if t.name == "monthly_sales")
            return json.dumps({"name": tool.name, "description": tool.description,
                               "inputSchema": tool.inputSchema}, ensure_ascii=False, indent=2)


def main() -> None:
    if not (DEMO / "sales_demo.db").exists():
        raise SystemExit("请先运行 python3 examples/mcp-demo/make_demo_db.py")
    OUT.mkdir(parents=True, exist_ok=True)

    run = subprocess.run(["uv", "run", "test_client.py"], cwd=DEMO, capture_output=True, text=True)
    out = "\n".join(l for l in run.stdout.splitlines() if l.strip() != "" or True)
    page, h = terminal_page("uv run test_client.py", out)
    shoot(page, "shot-test-client.png", 1100, h)

    spec = asyncio.run(tool_spec())
    page, h = card_page("AI 看到的“工具说明书”：monthly_sales",
                        "这是服务端通过 tools/list 发给 AI 的全部信息——AI 看不到你的代码，只看到这些",
                        spec)
    shoot(page, "shot-tool-spec.png", 900, h)


if __name__ == "__main__":
    main()

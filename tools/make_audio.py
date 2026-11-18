"""把 narration/*.txt 口语稿合成为语音（macOS 自带中文语音 + ffmpeg 压缩）。

运行：python3 tools/make_audio.py            全部重新生成
      python3 tools/make_audio.py mcp-03     只生成指定章节
输出：docs/assets/audio/<名>.m4a （单声道 AAC，约 40kbps，体积小，浏览器可直接播放）
想换音色：改下面的 VOICE（用 `say -v '?' | grep zh_CN` 查看可用音色）。
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "narration"
OUT = ROOT / "docs" / "assets" / "audio"
VOICE = "Tingting"   # 普通话女声
RATE = 165           # 语速（字/分钟附近，教学内容略慢一些更易听清）


def duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    total = 0.0
    for txt in sorted(SRC.glob("*.txt")):
        if only and txt.stem not in only:
            continue
        target = OUT / f"{txt.stem}.m4a"
        with tempfile.TemporaryDirectory() as d:
            aiff = Path(d) / "a.aiff"
            subprocess.run(["say", "-v", VOICE, "-r", str(RATE), "-f", str(txt), "-o", str(aiff)], check=True)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(aiff), "-ac", "1", "-ar", "24000",
                            "-c:a", "aac", "-b:a", "40k", "-movflags", "+faststart", str(target)], check=True)
        sec = duration(target)
        total += sec
        print(f"{target.name}  {sec / 60:4.1f} 分钟  {target.stat().st_size / 1024 / 1024:.1f}MB  ({len(txt.read_text(encoding='utf-8'))} 字)")
    print(f"合计 {total / 60:.1f} 分钟")


if __name__ == "__main__":
    main()

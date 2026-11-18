"""把 narration/*.txt 口语稿合成为语音，输出到 docs/assets/audio/<名>.m4a。

引擎（自动选择）：
  f5   本地 F5-TTS（MLX）克隆音色 —— 本机装有 ~/tts/bin/tts.py 时默认使用，免费、离线、数据不出本机
  say  macOS 自带中文语音 —— 没有 F5 时的兜底

运行：python3 tools/make_audio.py              全部重新生成
      python3 tools/make_audio.py mcp-03       只生成指定章节
      TTS_ENGINE=say python3 tools/make_audio.py   强制用系统语音
可调：TTS_HOME（F5 工具目录，默认 ~/tts）、TTS_VOICE（参考音 wav，默认 TTS_HOME/voices/female_xiaoxiao.wav）
"""
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "narration"
OUT = ROOT / "docs" / "assets" / "audio"
TTS_HOME = Path(os.environ.get("TTS_HOME", "~/tts")).expanduser()
TTS_PY = TTS_HOME / "bin" / "tts.py"
VOICE_WAV = Path(os.environ.get("TTS_VOICE", TTS_HOME / "voices" / "female_xiaoxiao.wav")).expanduser()
ENGINE = os.environ.get("TTS_ENGINE") or ("f5" if TTS_PY.exists() and VOICE_WAV.exists() else "say")
SAY_VOICE, SAY_RATE = "Tingting", 165


def prepare(text: str) -> str:
    """让文字更适合朗读：标识符里的下划线改成空格（monthly_sales → monthly sales）。"""
    return re.sub(r"(?<=[A-Za-z0-9])_(?=[A-Za-z0-9])", " ", text)


def duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())


def synth_f5(text_file: Path, wav: Path) -> None:
    env = {k: v for k, v in os.environ.items() if k.lower() not in ("http_proxy", "https_proxy", "all_proxy")}
    env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1")   # 离线运行，不联网
    subprocess.run(["python3", str(TTS_PY), "--engine", "f5mlx", "--text-file", str(text_file),
                    "--voice", str(VOICE_WAV), "--out", str(wav)],
                   check=True, capture_output=True, text=True, env=env)


def synth_say(text_file: Path, wav: Path) -> None:
    subprocess.run(["say", "-v", SAY_VOICE, "-r", str(SAY_RATE), "-f", str(text_file), "-o", str(wav)], check=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    print(f"引擎：{ENGINE}" + (f"（音色 {VOICE_WAV.name}）" if ENGINE == "f5" else f"（{SAY_VOICE}）"), flush=True)
    total = 0.0
    for txt in sorted(SRC.glob("*.txt")):
        if only and txt.stem not in only:
            continue
        t0 = time.time()
        target = OUT / f"{txt.stem}.m4a"
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "in.txt"
            src.write_text(prepare(txt.read_text(encoding="utf-8")), encoding="utf-8")
            wav = Path(d) / "a.wav"
            (synth_f5 if ENGINE == "f5" else synth_say)(src, wav)
            # 响度归一化到 -16 LUFS（各章音量一致），单声道 AAC，体积小
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                            "-af", "loudnorm=I=-16:TP=-1.5", "-ac", "1", "-ar", "24000",
                            "-c:a", "aac", "-b:a", "48k", "-movflags", "+faststart", str(target)], check=True)
        sec = duration(target)
        total += sec
        print(f"{target.name}  {sec / 60:4.1f} 分钟  {target.stat().st_size / 1024 / 1024:.1f}MB  "
              f"合成用时 {time.time() - t0:.0f} 秒", flush=True)
    print(f"合计 {total / 60:.1f} 分钟", flush=True)


if __name__ == "__main__":
    main()

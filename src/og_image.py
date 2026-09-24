"""Render assets/img/og-image.png (1200x630 link-preview image) with headless Chrome.

Usage:  python src/og_image.py
Re-run only if the name or title shown in the image changes.
"""
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "img", "og-image.png")
CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "chromium",
]

HTML = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Crimson+Pro:wght@500&display=swap" rel="stylesheet">
<style>
  html, body { margin: 0; width: 1200px; height: 630px; overflow: hidden; background: #fff; }
  body { position: relative; font-family: "Atkinson Hyperlegible", sans-serif; color: #1c1c1c; }
  svg.iso { position: absolute; inset: 0; width: 1200px; height: 630px; -webkit-mask-image: linear-gradient(to right, transparent 0%, transparent 45%, #000 90%); mask-image: linear-gradient(to right, transparent 0%, transparent 45%, #000 90%); }
  svg.iso path { fill: none; stroke: #d9d9d9; stroke-width: 1.4; }
  svg.iso path.warm { stroke: #e3b58a; }
  .card { position: absolute; left: 96px; top: 150px; right: 96px; }
  h1 { font-family: "Crimson Pro", serif; font-weight: 500; font-size: 104px; margin: 0; letter-spacing: -1.5px; }
  h1 span { color: #b45309; }
  p { font-size: 32px; color: #4a4a4a; margin: 22px 0 0; line-height: 1.35; }
  .bar { width: 72px; height: 3px; background: #b45309; margin-top: 44px; }
  .url { position: absolute; left: 96px; bottom: 64px; font-size: 24px; color: #1e3a5f; font-weight: 700; letter-spacing: .5px; }
</style></head><body>
<svg class="iso" viewBox="0 0 1200 630" preserveAspectRatio="none">PATHS</svg>
<div class="card">
  <h1>Guewen Heslan<span>.</span></h1>
  <p>Economist — trade, environmental policy &amp; maritime transport<br>LEMNA, Nantes Université · Université Paris Cité</p>
  <div class="bar"></div>
</div>
<div class="url">gheslan.github.io</div>
</body></html>"""


def main():
    paths = []
    for i in range(9):
        y = 40 + i * 72
        a = 12 + (i % 3) * 6
        d = f"M0 {y} Q150 {y - a} 300 {y} " + " ".join(f"T{x} {y}" for x in range(600, 1501, 300))
        paths.append(f'<path{" class=\"warm\"" if i == 7 else ""} d="{d}"/>')
    html = HTML.replace("PATHS", "".join(paths))
    chrome = next((c for c in CHROME if os.path.exists(c)), None) or CHROME[-2]
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "og.html")
        with open(src, "w", encoding="utf-8") as f:
            f.write(html)
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        "--virtual-time-budget=4000", "--window-size=1200,630", f"--screenshot={OUT}", "file:///" + src.replace("\\", "/")],
                       check=True, capture_output=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()

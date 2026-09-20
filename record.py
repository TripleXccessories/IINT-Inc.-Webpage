#!/usr/bin/env python3
"""Frame-exact capture of one IINT sequence variant.

Xvfb -> Chrome in app/kiosk mode (no browser UI) on ?armed (black frame) ->
x11grab starts rolling -> CDP releases the page -> capture -> mux the cue.
The page is armed, so the animation cannot begin before the grabber is up and
nothing has to be trimmed by guesswork.

usage: record.py "<query>" <outfile>
"""

import os
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

QUERY = sys.argv[1]
OUT = sys.argv[2]
W, H = 1920, 1080
FPS = 30
LEAD = 1.2       # black frames captured before the release
SHORT = "short" in QUERY
DUR = (7.0 if SHORT else 20.0) + LEAD  # sequence plus a beat of tail
DISP = ":77"
PORT = 9222
CUE = (
    "/home/user/iint-logo-preview/packages/web/public/iint-cue-short.mp3"
    if SHORT
    else "/home/user/iint-logo-preview/packages/web/public/iint-cue.mp3"
)
RAW = f"/tmp/iint_raw_{os.getpid()}.mp4"
PROFILE = f"/tmp/iint_chrome_{os.getpid()}"

subprocess.run(["pkill", "-f", f"Xvfb {DISP}"], check=False)
subprocess.run(["pkill", "-f", f"remote-debugging-port={PORT}"], check=False)
time.sleep(1)

xvfb = subprocess.Popen(
    ["Xvfb", DISP, "-screen", "0", f"{W}x{H}x24", "-nolisten", "tcp"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
time.sleep(2)
env = {**os.environ, "DISPLAY": DISP}

url = f"http://localhost:4200/?armed&mute&{QUERY}"
chrome = subprocess.Popen(
    [
        "google-chrome",
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={PROFILE}",
        f"--app={url}",
        "--start-fullscreen",
        "--kiosk",
        f"--window-size={W},{H}",
        "--window-position=0,0",
        "--force-device-scale-factor=1",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-infobars",
        "--disable-features=Translate",
        "--no-sandbox",
    ],
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
time.sleep(4)

grab = None
try:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{PORT}")
        page = browser.contexts[0].pages[0]
        page.wait_for_function("typeof window.__iintStart === 'function'", timeout=30000)
        time.sleep(1.5)  # compositor settles on a clean black frame

        grab = subprocess.Popen(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "x11grab", "-framerate", str(FPS),
                "-video_size", f"{W}x{H}", "-draw_mouse", "0", "-i", DISP,
                "-t", str(DUR),
                "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                "-pix_fmt", "yuv420p", RAW,
            ],
            env=env,
        )
        time.sleep(LEAD)
        page.evaluate("window.__iintStart()")
        grab.wait(timeout=DUR + 90)
finally:
    if grab is not None and grab.poll() is None:
        grab.terminate()
    chrome.terminate()
    xvfb.terminate()
    time.sleep(1)
    subprocess.run(["rm", "-rf", PROFILE], check=False)

# drop the black lead-in, lay the cue underneath
subprocess.run(
    [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", str(LEAD), "-i", RAW, "-i", CUE,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", OUT,
    ],
    check=True,
)
os.remove(RAW)
print(f"wrote {OUT}")

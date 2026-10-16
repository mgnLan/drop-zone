# CDP screenshot runner for Drop Zone uitest tour
import asyncio, base64, json, subprocess, time, urllib.request, os, sys

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 9333
URL = "http://localhost:8901/index.html?uitest=1"
OUT = r"C:\Users\Антон\AppData\Local\Temp\dz_shots"
W, H = 1280, 800

os.makedirs(OUT, exist_ok=True)

async def main():
    proc = subprocess.Popen([
        CHROME, "--headless=new", f"--remote-debugging-port={PORT}",
        "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
        f"--window-size={W},{H}", "--no-first-run", "--user-data-dir=C:/tmp/dz_chrome",
        "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        # wait for devtools
        version = None
        for _ in range(50):
            try:
                version = json.load(urllib.request.urlopen(f"http://localhost:{PORT}/json/version", timeout=2))
                break
            except Exception:
                time.sleep(0.5)
        if not version:
            print("NO DEVTOOLS"); return
        targets = json.load(urllib.request.urlopen(f"http://localhost:{PORT}/json/list", timeout=5))
        page = next(t for t in targets if t["type"] == "page")
        import websockets
        async with websockets.connect(page["webSocketDebuggerUrl"], max_size=100*1024*1024) as ws:
            mid = 0
            async def cmd(method, params=None):
                nonlocal mid
                mid += 1
                await ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
                while True:
                    msg = json.loads(await ws.recv())
                    if msg.get("id") == mid:
                        return msg.get("result", {})
            await cmd("Page.enable")
            await cmd("Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False})
            await cmd("Page.navigate", {"url": URL})
            # capture frames across the uitest tour (~2.5 min total)
            t0 = time.time()
            shots = [(8, "loading"), (25, "lobby"), (45, "screen2"), (65, "screen3"),
                     (85, "screen4"), (105, "screen5"), (125, "screen6"), (145, "battle")]
            for target_t, name in shots:
                dt = target_t - (time.time() - t0)
                if dt > 0:
                    await asyncio.sleep(dt)
                res = await cmd("Page.captureScreenshot", {"format": "png"})
                p = os.path.join(OUT, f"{name}.png")
                with open(p, "wb") as f:
                    f.write(base64.b64decode(res["data"]))
                print("saved", p, flush=True)
    finally:
        proc.terminate()

asyncio.run(main())

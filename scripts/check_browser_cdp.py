"""Check the running synthetic browser through Chrome DevTools Protocol.

Install the optional benchmark dependencies, generate the fixture with
benchmark_browser.py --write-fixture, then run Streamlit using those CSVs.
"""

import argparse
import base64
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from urllib.request import urlopen

import websocket


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8521")
    parser.add_argument("--chrome", default=shutil.which("google-chrome") or r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    parser.add_argument("--output", type=Path, default=Path("docs/evidence/a9-browser-performance"))
    parser.add_argument("--repeats", type=int, default=7)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="a9-chrome-", ignore_cleanup_errors=True) as profile:
        process = subprocess.Popen([
            args.chrome, "--headless=new", "--no-first-run", "--disable-extensions",
            "--enable-unsafe-swiftshader", "--use-angle=swiftshader",
            "--remote-debugging-port=9349", "--remote-allow-origins=*",
            f"--user-data-dir={profile}", args.url,
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(100):
                try:
                    with urlopen("http://127.0.0.1:9349/json", timeout=1) as response:
                        tab = next(t for t in json.load(response) if t["type"] == "page")
                    break
                except (OSError, StopIteration):
                    time.sleep(.1)
            connection = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=20)
            sequence = 0

            def call(method, params=None):
                nonlocal sequence
                sequence += 1
                connection.send(json.dumps({"id": sequence, "method": method, "params": params or {}}))
                while True:
                    response = json.loads(connection.recv())
                    if response.get("id") == sequence:
                        if "error" in response:
                            raise RuntimeError(response)
                        return response["result"]

            def js(expression):
                result = call("Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True})
                if "exceptionDetails" in result:
                    raise RuntimeError(result["exceptionDetails"])
                return result["result"].get("value")

            def wait_for(expression):
                for _ in range(200):
                    if js(expression):
                        return
                    time.sleep(.05)
                raise RuntimeError(f"Timed out: {expression}")

            def settle():
                # Observe the resulting graph, then wait for two paint frames.
                wait_for("document.querySelector('[data-testid=stApp]')?.getAttribute('data-test-script-state') === 'notRunning'")
                js("new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")

            call("Emulation.setDeviceMetricsOverride", {"width": 1440, "height": 1000, "deviceScaleFactor": 1, "mobile": False})
            wait_for("document.querySelector('.js-plotly-plot')?._fullData?.length > 0")
            settle()
            assert js("document.querySelector('.js-plotly-plot')._fullData.reduce((n,t)=>n+t.x.length,0)") == 8000
            version = call("Browser.getVersion")
            timings = []
            for index in range(args.repeats):
                seed = f"SYN-{index:05d}"
                start = time.perf_counter()
                js("""(() => {
                    const g = document.querySelector('.js-plotly-plot');
                    const n = g.data.findIndex(t => t.customdata?.some(c => c[0] === SEED));
                    const t = g.data[n], i = t.customdata.findIndex(c => c[0] === SEED);
                    g.emit('plotly_selected', {points:[{curveNumber:n,pointNumber:i,pointIndex:i,
                        x:g._fullData[n].x[i],y:g._fullData[n].y[i],customdata:t.customdata[i],
                        data:t,fullData:g._fullData[n]}]});
                })()""".replace("SEED", json.dumps(seed)))
                wait_for(f"document.body.innerText.includes('Track ID: {seed}')")
                wait_for(f"document.querySelector('.js-plotly-plot').data.some(t => t.selectedpoints?.some(i => t.customdata[i][0] === '{seed}'))")
                settle()
                timings.append(time.perf_counter() - start)

            # Actual browser pointer click on a point, followed by Plotly pan/zoom.
            # Bring the chart into view before calculating pointer coordinates.
            js("document.querySelector('.js-plotly-plot').scrollIntoView({block:'center'})")
            settle()
            target = js("""(() => {
                const g=document.querySelector('.js-plotly-plot');
                const r=g.getBoundingClientRect(), l=g._fullLayout;
                const points=g._fullData.flatMap(t=>Array.from(t.x, (x,i)=>({
                    x:r.x+l.xaxis._offset+l.xaxis.l2p(x),
                    y:r.y+l.yaxis._offset+l.yaxis.l2p(t.y[i]),id:t.customdata[i][0]})));
                // A sparse point avoids ambiguous clicks in the dense centre.
                return points.find(p=>p.x>r.x+40 && p.x<r.right-160 && p.y>Math.max(90,r.y+40)
                    && p.y<Math.min(innerHeight-40,r.bottom-40)
                    && points.every(q=>p===q || Math.hypot(p.x-q.x,p.y-q.y)>18));
            })()""")
            assert target, "No isolated visible point found"
            call("Input.dispatchMouseEvent", {"type":"mouseMoved", "x":target["x"], "y":target["y"]})
            time.sleep(.1)
            call("Input.dispatchMouseEvent", {"type":"mousePressed", "x":target["x"], "y":target["y"], "button":"left", "clickCount":1})
            call("Input.dispatchMouseEvent", {"type":"mouseReleased", "x":target["x"], "y":target["y"], "button":"left", "clickCount":1})
            wait_for(f"document.body.innerText.includes('Track ID: {target['id']}')")
            previous_range = js("document.querySelector('.js-plotly-plot')._fullLayout.xaxis.range[0]")
            call("Input.dispatchMouseEvent", {"type":"mouseWheel", "x":target["x"], "y":target["y"], "deltaX":0,"deltaY":-200})
            wait_for(f"document.querySelector('.js-plotly-plot')._fullLayout.xaxis.range[0] !== {previous_range}")
            js("document.querySelector('.modebar-btn[data-title=\"Reset axes\"]').click()")
            wait_for("document.querySelector('.js-plotly-plot')._fullLayout.xaxis.autorange")

            # Keyboard access: tab into the projection radio and use an arrow key.
            js("[...document.querySelectorAll('input[type=radio]')].find(e=>e.checked && e.closest('label').innerText.includes('UMAP')).focus()")
            call("Input.dispatchKeyEvent", {"type":"keyDown", "key":"ArrowLeft", "code":"ArrowLeft", "windowsVirtualKeyCode":37})
            call("Input.dispatchKeyEvent", {"type":"keyUp", "key":"ArrowLeft", "code":"ArrowLeft", "windowsVirtualKeyCode":37})
            wait_for("document.querySelector('.js-plotly-plot').layout.uirevision.includes('PCA')")
            assert js(f"document.body.innerText.includes('Track ID: {target['id']}')")
            filter_timings = []
            reset_timings = []
            count_points = "document.querySelector('.js-plotly-plot')?._fullData.reduce((n,t)=>n+t.x.length,0)"
            for _ in range(args.repeats):
                wait_for("!!document.querySelector('[data-testid=stMultiSelect] [data-baseweb=tag][aria-label^=\"Genre 7,\"]')")
                start = time.perf_counter()
                js("document.querySelector('[data-testid=stMultiSelect] [data-baseweb=tag][aria-label^=\"Genre 7,\"] [role=presentation]').click()")
                wait_for(count_points + " === 7000")
                settle()
                filter_timings.append(time.perf_counter() - start)
                start = time.perf_counter()
                js("[...document.querySelectorAll('button')].find(e=>e.innerText==='Reset filters').click()")
                wait_for(count_points + " === 8000")
                settle()
                reset_timings.append(time.perf_counter() - start)
            layouts = []
            for width in (1440, 768, 375):
                call("Emulation.setDeviceMetricsOverride", {"width":width,"height":1000,"deviceScaleFactor":1,"mobile":False})
                time.sleep(.5)
                js("window.scrollTo(0,0); document.querySelector('[data-testid=stMain]').scrollTo(0,0)")
                state = js("({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,points:document.querySelector('.js-plotly-plot')._fullData.reduce((n,t)=>n+t.x.length,0)})")
                assert state["width"] >= state["scrollWidth"]
                assert state["points"] == 8000
                layouts.append(state)
                screenshot = call("Page.captureScreenshot", {"format":"png","captureBeyondViewport":False})
                (args.output / f"a9-{width}.png").write_bytes(base64.b64decode(screenshot["data"]))
                js("document.querySelector('.js-plotly-plot').scrollIntoView({block:'start'})")
                settle()
                screenshot = call("Page.captureScreenshot", {"format":"png","captureBeyondViewport":False})
                (args.output / f"a9-map-{width}.png").write_bytes(base64.b64decode(screenshot["data"]))
            result = {"browser": version, "rendering": "headless Chrome, SwiftShader software WebGL",
                      "selection_seconds": timings, "selection_method": "Plotly selection event from actual trace data to rendered details and selected marker plus two animation frames",
                      "filter_seconds":filter_timings, "filter_reset_seconds":reset_timings,
                      "filter_method":"Genre 7 remove control (8,000 to 7,000 points); Reset filters restores 8,000; graph update plus two animation frames",
                      "physical_point_click": target["id"], "keyboard_projection_switch": "PASS",
                      "zoom_reset": "PASS", "layouts":layouts}
            (args.output / "browser.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(result, indent=2))
            connection.close()
            assert all(value < 2 for value in timings + filter_timings + reset_timings), "Browser interaction exceeded two seconds"
        finally:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    main()

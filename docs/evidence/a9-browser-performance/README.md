# A9: 8,000-track browser performance

Aaron Sharma, Objective 1, PI5. Recorded November 22, 2026.

## Result

PASS on the documented development machine and deterministic synthetic fixture.
All seven measured cached filter, reset, and selection runs completed within two
seconds, both in Streamlit AppTest and in local headless Chrome. These are
synthetic collection measurements, not FMA retrieval-quality or audio benchmarks.

| Server action | Before median (ms) | After median (ms) | After maximum (ms) |
|---|---:|---:|---:|
| Filter to two genres | 141 | 101 | 124 |
| Reset filters | 237 | 152 | 190 |
| Select another seed | 486 | 319 | 370 |
| Switch PCA/UMAP | 285 | 187 | 239 |
| Switch representation | 277 | 191 | 200 |
| Compare representations | 337 | 214 | 287 |

Cold first load was 526 ms before and 460 ms after (one observation each).
Cached filter and selection medians improved by approximately 28% and 34%.
Both versions already satisfied the server threshold. Warm CSV read counts
were zero before and after; A9 improves lookup and chart construction rather
than claiming a new caching speedup where caching already existed.

Browser medians were 372 ms for removing one genre, 394 ms for reset, and
600 ms for selection. Maxima were 421, 429, and 664 ms respectively.
[before.json](before.json), [after.json](after.json), and
[browser.json](browser.json) retain every observation and environment details.

## Scope and source

The local `integration/a9-baseline` branch at `cfc6549` combines the existing
A3, A5, and A8 histories (A8 includes A4, A6, and A7), starting from current
`origin/main` at `358910b`. Dependency conflict resolutions were recorded on
that baseline before A9 changes. It passes 76 tests. No remote merge occurred.

`feature/a9-browser-performance` contains only A9 changes after this baseline.
Review A9 with `git diff integration/a9-baseline...feature/a9-browser-performance`.
A9 cannot target an isolated diff against current remote `main` until those
dependency PRs are integrated. Rebase/reconcile and rerun verification against
the final integrated main before publication. No PR has been opened for A9.

The baseline merge keeps stable selection and playback while adding A3's
filters and A5's saved projections. Legacy single-map artifacts without a
projection column remain browsable as `Unspecified`; unsupported named
projections retain A5's warning. The benchmark does not fit projections or
compute neighbours. The synthetic neighbour IDs are fixed cyclic fixtures.

## Measured changes

An instrumented three-repeat baseline run recorded 28 map constructions:
75.7 ms mean map construction, including 48.3 ms in Plotly Express. Twenty-six
neighbour lookups averaged 17.4 ms. Track lookup averaged 0.93 ms across 152
calls and was left unchanged. These call-level observations include warmup
and instrumented overhead; the table above uses uninstrumented reruns.

- Construct category-grouped `Scattergl` traces directly, preserving hover IDs,
  deterministic colours, selection cues, legend, and saved-map viewport state.
- Prepare a case-insensitive seed/representation index once inside the cached
  neighbour loader, preserving saved rank, seed exclusion, and deduplication.
- Centralize coordinate/neighbour caches, bound each to eight file versions,
  and key on resolved path, mtime, ctime, and size. Stat on every access means a
  deleted artifact cannot return stale cached content. Callers receive copies.
- Ignore delayed selection events for tracks outside the active map.

Artifact producers must change file timestamps or size when publishing new
content. Changes preserving all recorded metadata are not detectable. Audio
validation and playback retain their existing safety checks; this synthetic
performance fixture has no audio, so real audio I/O remains unmeasured.

## Reproduce

Run from the A9 checkout with Python 3.12 and project dependencies installed:

```powershell
python -m pip install -e ".[dev,benchmark]"
python -m pytest
python scripts/benchmark_browser.py --repeats 7 --output artifacts/a9-after.json --write-fixture artifacts/a9-fixture
```

The deterministic seed is 497. Each of the Conventional/OpenL3 × PCA/UMAP
maps has 8,000 stable track IDs: 32,000 coordinate rows and 80,000 saved-neighbour
rows overall. Eight genres and twelve clusters exercise filtering and colour
groups. AppTest includes server execution, chart serialization, selection's
additional rerun, detail rendering, and neighbour loading. It excludes network
and browser paint. Filter/reset and selection exceedances fail the command.

To reproduce the before measurement, create a separate worktree at `cfc6549`,
copy `scripts/benchmark_browser.py` from the A9 branch into its `scripts/`
directory, and run the same benchmark command from that checkout. The script
derives its app/source roots from its own location. Do not run the A9 script
against a different checkout merely by changing the current directory.

Start the browser fixture server in a separate PowerShell terminal:

```powershell
$env:TIMBRELIO_COORDINATES_PATH = (Resolve-Path artifacts/a9-fixture/coordinates.csv).Path
$env:TIMBRELIO_NEIGHBOURS_PATH = (Resolve-Path artifacts/a9-fixture/neighbours.csv).Path
$env:TIMBRELIO_OPENL3_NEIGHBOURS_PATH = $env:TIMBRELIO_NEIGHBOURS_PATH
$env:PYTHONPATH = (Resolve-Path src).Path
python -m streamlit run app.py --server.port 8521 --server.headless true --browser.gatherUsageStats false
```

Then run:

```powershell
python scripts/check_browser_cdp.py --repeats 7 --output artifacts/a9-browser
```

Use `--chrome` for a different Chrome executable and `--url` for a different
local server. The CDP port is 9349. The script launches a temporary headless
profile and closes its process. Chrome used SwiftShader software WebGL on this
Windows machine; this does not characterize every GPU or remote deployment.
Browser timings include polling and two animation frames after the resulting
map and details update and Streamlit finishes its rerun. Repeated selection
timings emit Plotly's selection event with real trace metadata; a separate
physical pointer click confirms ordinary point selection. Filtering activates
the genre's visible remove control and reset button.

## Verification

| Criterion | Status | Evidence |
|---|---|---|
| Cached filtering/selection under two seconds in repeated runs | PASS | Seven server and seven browser observations per action |
| Before/after medians and environment | PASS | Raw JSON; Python 3.12.4, Windows 11, 20 logical CPUs, pinned project versions |
| 8,000 points navigable and selectable | PASS | Browser point count, physical click, wheel zoom, reset; scale test |
| Filtering and identity remain correct | PASS | Exact ID-set assertion at scale; projection/representation switch and comparison |
| Cache invalidation and isolation | PASS | Size change with preserved mtime, same-size timestamp change, deletion, caller mutation |
| Correctness separate from timing assertions | PASS | 80 pytest tests; standalone timing commands |
| Responsive browser checks | PASS | 375/768/1440 px, no page overflow, 8,000 plotted points at each width |
| Keyboard projection switching | PASS | Native ArrowLeft changes UMAP to PCA while retaining the seed |
| Full real FMA/audio timing and final merged-main integration | UNVERIFIED | Requires actual artifacts and dependency integration |

The server test run reports an unrelated installed `pytest_asyncio` deprecation
warning. It does not fail tests. Screenshots show controls and the selected map
at each width:

| Width | Controls | Map and selected-track context |
|---|---|---|
| 375 | [controls](a9-375.png) | [map](a9-map-375.png) |
| 768 | [controls](a9-768.png) | [map](a9-map-768.png) |
| 1440 | [controls](a9-1440.png) | [map](a9-map-1440.png) |

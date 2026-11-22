Title: perf(ui): keep 8,000-track browsing responsive (A9)

Aaron Objective 1, PI5: keep filtering and selection responsive across all
8,000 tracks. Reduce repeated map-construction and neighbour-lookup work while
preserving saved-artifact identity, hover, selection, and playback behavior.

Construct WebGL category traces directly, prepare a case-insensitive saved
neighbour index in the artifact cache, and bound/version coordinate and
neighbour caches using file metadata. Ignore stale selections outside the
active map. Add reproducible synthetic 8,000-track benchmarks and correctness
coverage for scale and cache invalidation.

Seven-run server medians: filtering 141 → 101 ms; selection 486 → 319 ms.
Seven-run local Chrome maxima: filtering 421 ms, reset 429 ms, selection
664 ms. All cached filter/selection observations were under two seconds.
Warm interactions performed no CSV reads. The baseline already met the target.

Validation: `python -m pytest` (80 passed), `git diff --check`,
`python scripts/benchmark_browser.py --repeats 7 --output artifacts/a9-after.json`,
and `python scripts/check_browser_cdp.py --repeats 7` against the fixture server.
Physical point selection, wheel zoom/reset, keyboard projection switching,
and responsive layouts at 375, 768, and 1440 px passed.

See [measurement evidence](README.md) for raw observations, environment,
commands, screenshots, and limitations. Synthetic data contains no audio;
full FMA/audio performance is unmeasured. No feature/projection/retrieval
computation or visual redesign is included.

Dependencies: [A3](https://github.com/aaronforreal/Timbrelio/pull/3),
[A4](https://github.com/aaronforreal/Timbrelio/pull/4),
[A5](https://github.com/aaronforreal/Timbrelio/pull/5),
[A6](https://github.com/aaronforreal/Timbrelio/pull/6),
[A7](https://github.com/aaronforreal/Timbrelio/pull/7), and
[A8](https://github.com/aaronforreal/Timbrelio/pull/9).
Prepared on local `integration/a9-baseline` (`cfc6549`); reconcile with merged
dependencies and rerun verification before opening against `main`.

Publication status: local draft only, awaiting user approval to raise a PR.

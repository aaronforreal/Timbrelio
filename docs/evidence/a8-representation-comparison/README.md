# A8: compare conventional and learned neighbour results

README mapping: Aaron, Objective 2, PI5 (advanced).

Branch: `feature/a8-representation-comparison`.
Stacked PR base: `feature/a7-comparison-playback` at `9884c08`.
No dependency branches were merged. A3/A5 integration remains deferred.

## Checks

- `python -m pytest`: **59 passed**, including all A7 regression tests.
- `git diff --check`: passed.
- AppTest exercises same-seed dual lists, changing seeds, saved rank preservation,
  deduplication and seed exclusion, deterministic overlap, partial lists, combined
  and separate artifacts, missing/corrupt/empty inputs on either side, off-map IDs,
  colour reruns, locating without replacing the seed, returning to single mode,
  and distinct audio URLs for the seed and shared neighbours.
- Real Streamlit browser review with headless Chrome/CDP: Plotly selection,
  comparison mode, ten ranked rows, six shared-row labels (three shared IDs),
  and locating a neighbour while retaining the seed.
- At 1440, 768, and 375 pixels, measured document width equals viewport width.
  Desktop/tablet lists are side by side; mobile lists stack. Screenshots below.
- Keyboard Tab from the selected comparison radio reaches the first enabled
  Locate on map button; its computed outline is visible. Existing unavailable
  audio controls remain disabled and keep rank context.

Machine: Windows, Python 3.12; Streamlit 1.42.2, Plotly 6.9.0,
pandas 2.2.3, NumPy 1.26.4, pytest 8.3.0 (project pins).
The installed pytest-asyncio plugin emits its existing fixture-loop-scope
deprecation warning; no tests fail.

## PR review follow-up

- `python -m pytest`: **64 passed** after the review fixes.
- `git diff --check`: passed.
- AppTest covers two nonempty partial lists with and without a shared ID,
  asymmetric completeness, a synthetic Conventional list beside custom OpenL3
  results, and an invalid OpenL3 rank in a combined CSV.
- Shared labels remain confirmed matches. Unmatched rows claim uniqueness only
  against a complete opposite list; partial opposite lists show overlap unknown.
- Shared counts explicitly identify synthetic inputs, including mixed sources.
- Combined CSV validation remains atomic: an invalid row makes both sides using
  that file unavailable. The UI and README explain this; separate CSVs retain
  independent failure handling.

## Screenshots

These show the real app with bundled synthetic coordinates and saved neighbour
fixtures. No FMA audio is committed or represented as tested project results.

- [Desktop, 1440 px](a8-1440.png)
- [Tablet, 768 px](a8-768.png)
- [Mobile, 375 px](a8-375.png)
- [Measured browser checks](browser-checks.json)

## Limits

Synthetic fixtures establish comparison behavior, not retrieval quality.
Generated local WAV fixtures verify player identity in AppTest; audible browser
playback with real FMA clips remains an integration check. A3 filters and A5
projection switching are intentionally not part of this stacked A7 baseline.
Full integrated validation and A9's 8,000-track measurements remain future work.

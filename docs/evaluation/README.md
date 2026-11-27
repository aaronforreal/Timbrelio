# Meet’s evaluation workflow

Timbrelio compares how two audio feature representations retrieve similar tracks, preserve neighbours on a map, and support browsing. Run each representation on the same tracks with verified top-level genres. Archive the feature inputs and record the app commit, audio manifest, machine and dependency versions alongside the results.

## Run the experiments

Install with `python -m pip install -e ".[analysis,dev]"`. Nick’s branch `Nicks_work` at `50302b3` supplies the eight feature arrays in `Track.save()`. Its checked-in JSON has one track. Convert a complete export with:

```sh
python -m timbrelio.nick_features tracks.json conventional.csv
python -m timbrelio.study conventional.csv results/conventional-s42 --representation Conventional
python -m timbrelio.study openl3.csv results/openl3-s42 --representation OpenL3
```

The adapter preserves string IDs and exports 46 features. Join a verified FMA top-level `genre` column by ID before evaluation. Nick’s genre lists can contain multiple tags. OpenL3 needs a separate CSV with the same IDs and numeric embedding columns. Compare the ID sets and genre labels before comparing representation scores. Use separate output directories for each dataset, representation and seed. At least 31 tracks are required for the fixed grid.

Each run records baseline PCA, UMAP, k-means and HDBSCAN measurements. Four one-factor changes test UMAP neighbours (15 to 30), minimum distance (0.1 to 0.5), HDBSCAN minimum cluster size (15 to 30), and minimum samples (5 to 10). Other settings stay fixed. Use the projection and cluster metric CSVs to compare each variant with baseline. Prefer greater neighbour overlap and trustworthiness for maps. For clustering, evaluate silhouette alongside noise coverage and ARI. Record the observed trade-off, chosen settings and reason in the paper. Repeat with `--seed 43` to check whether the conclusion holds. First-run UMAP compilation can inflate runtime.

The five neighbours come from cosine distance on standardized original features. Precision@5 is the fraction with the seed’s top-level genre. Report the mean and eligible seed count in `study.json`. Seeds with missing labels anywhere in their top five are excluded. The listening CSV selects the lowest and highest eligible genre-agreement examples, breaking ties by track ID. Audition the seed and all five ranked clips, record timbre, rhythm or instrumentation, and identify useful and misleading matches from what is audible. Genre agreement alone cannot establish listening quality.

## Project usability study

Recruit 4–6 classmates and obtain voluntary participation. Use anonymous codes. Use the same integrated browser build, artifacts and playable seed for all participants. Check the controls before starting. Reset the app before each task and time from the end of the instruction to completion or abandonment. Record assistance and observations separately. Aaron’s three-session pilot informed this protocol and must be counted separately.

| Task | Instruction | Observable completion |
| --- | --- | --- |
| filter | Show only Rock, colour by genre, read a visible track ID, then restore all tracks. | Correct filter and colour settings, matching ID, full map restored. |
| listen | Play the seed and the first two playable neighbours starting at rank 1. Locate the second and report the selected ID. | Playback in rank order, neighbour highlighted, original seed still selected. |
| projection | Select a track on PCA, switch to UMAP, describe one visible difference, then return to PCA. | ID checked across projections or missing-track notice recognized, difference described, PCA restored. |

Use CSV columns `participant,task,completed,seconds,assistance,comment`. Task keys are in the table. Record yes/no and elapsed seconds, including abandoned attempts. Run `python -m timbrelio.usability sessions.csv usability-summary.csv`. Report completion over all attempts and median time among completions. Group recurring comments by task, count distinct participants reporting each issue, and include exceptions. Keep identifiable notes out of Git.

## Paper and outstanding evidence

Use the [official ISMIR LaTeX template](https://github.com/ismir/paper_templates/tree/master/2026/latex) and insert `report-sections.tex` after its abstract. The source covers methods, results to collect, and limitations. The final paper needs full conventional and OpenL3 runs, listened examples, extraction and browser timings from the respective components, and the observed classmate sessions. For browser timings, report app startup and repeated filter/selection latency separately, with machine, track count and warm/cold state.

Generate the paper’s numeric tables with `python -m timbrelio.report results/conventional-s42 results/openl3-s42 evaluation-tables.tex`. The command checks matching track IDs, genre labels and configurations, then compares Precision@5 on the intersection of eligible seeds. Place the generated file beside the paper’s main TeX file and include it with `\input{evaluation-tables}` in the results section.

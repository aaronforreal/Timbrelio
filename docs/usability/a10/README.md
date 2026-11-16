# A10 usability pilot

## Objective

Write and pilot three short Timbrelio browsing tasks covering map/filter
exploration, seed to neighbour listening, and PCA/UMAP comparison. This A10 pilot
checks task wording and the browsing workflow. It is separate from Meet's later
project-level evaluation with 4-6 classmates.

## Pilot setup

- Recruit at least two classmates who did not implement the tested interface.
- Use anonymous participant labels. Do not record names, contact information,
  student IDs, demographic details, audio, or video.
- Use the same app commit and coordinate, neighbour, and audio artifacts for every
  session. Record those identifiers in each session form.
- Before the first session, confirm filters and reset work, a track can be
  selected, the seed and two neighbours have playable audio, locating a neighbour
  keeps the seed selected, and PCA and UMAP are both available.
- Begin every task from the stated clean condition. Time from the end of reading
  the instruction until the observable completion condition is met.
- Wait 30 seconds before offering the neutral prompt, “What control would you
  expect to use next?” Record every prompt as assistance.

Tell each participant that the interface and instructions are being tested, not
them; participation is voluntary; and they may stop at any time.

## Task 1 — Filter and inspect the map

**Starting state:** Default representation, all genres and clusters visible, no
selected track, and the map viewport reset.

**Participant instruction:**

> In the Genres filter, choose only Rock. Set Colour points by to Genre, select
> one visible track, and tell me its displayed title or track ID. Then restore the
> complete map using Reset filters.

**Completion condition:** Rock is the only active genre when a track is selected;
the displayed details match that point; the participant reports the title or ID;
and Reset filters restores the full map.

**Record:** completion, time, major and minor errors, assistance, issue codes, the
observable end state, a concise comment, and a factual observer note.

## Task 2 — Listen to the seed and neighbours

**Starting state:** Clean application state with a preflighted playable seed
selected. The seed and at least two neighbours must have enabled audio controls.

**Participant instruction:**

> In the comparison area, play the selected seed. Then skip disabled audio
> controls and play the two lowest-ranked neighbours whose controls are enabled.
> Locate one of those neighbours on the map and tell me which track remains
> selected.

**Completion condition:** The seed and two playable neighbours are activated in
the requested order; a neighbour is located on the map; and the original seed
remains selected.

**Record:** completion, time, playback order, seed and located-neighbour IDs,
major and minor errors, assistance, issue codes, unavailable audio, the observable
end state, a concise comment, and a factual observer note.

## Task 3 — Compare PCA and UMAP

**Starting state:** Default representation on PCA, all tracks visible, no selected
track, and the map viewport reset.

**Participant instruction:**

> Select a track in PCA and say whether it is near the centre or edge of the map.
> Switch to UMAP, confirm whether the same track remains selected, and describe
> one visible change, such as the points looking more grouped or spread out. Then
> return to PCA.

**Completion condition:** A stable track ID is selected in PCA; UMAP is opened;
the same ID remains selected or an explicit unavailable-track notice appears; the
participant describes one visible structural difference; and the view returns to
PCA.

**Record:** completion, time, selected ID, selection persistence, major and minor
errors, assistance, issue codes, the observable end state, a concise comment, and
a factual observer note.

## Pilot results

| Task | Completed | Median time | Major errors | Minor errors | Assistance |
|---|---:|---:|---:|---:|---:|
| 1 — Filter and inspect | 3/3 | 68 s | 0 | 2 | 1 |
| 2 — Seed and neighbours | 3/3 | 96 s | 0 | 2 | 0 |
| 3 — Compare PCA and UMAP | 3/3 | 82 s | 0 | 1 | 1 |

Across `01 Elephant`, `02 Cat`, and `03 Rabbit`, all nine pilot tasks were
completed. The records contain no major errors, five minor errors, and two
assistance events.

## Wording revisions from the pilot

| Task | Observed friction | Revision made |
|---|---|---|
| 1 | Filtering and colouring were treated as the same action. | Name the Genres filter and Colour points by control separately. |
| 2 | “Available” was unclear when an audio control was disabled. | Say to skip disabled controls and choose the two lowest enabled ranks. |
| 3 | The requested map comparison was too open-ended. | Give neutral centre/edge and grouped/spread-out cues. |

## Issues observed in the pilot

| ID | Severity | Evidence in pilot records | Recommended follow-up |
|---|---|---|---|
| PRACTICE-001 | Medium | 01 Elephant and 02 Cat confused filtering with colouring. | Separate filter and display controls. |
| PRACTICE-002 | Medium | 02 Cat paused at disabled audio; 03 Rabbit briefly lost rank order. | Keep ranks beside players and clarify disabled controls. |
| PRACTICE-003 | Low | 02 Cat expected Locate on map to replace the seed selection. | Clarify that locating highlights without changing the selection. |
| PRACTICE-004 | Low | 02 Cat needed a cue for the PCA/UMAP comparison. | Use the revised instruction in the later evaluation. |

## Handoff and completion

Hand the anonymized pilot notes to Meet for the later 4–6 classmate project
evaluation. Keep these A10 pilot results distinct from Meet's evaluation summary,
and track confirmed UI fixes through the follow-up issues or PRs in Aaron's
deliverables plan.

A10 is complete when all three tasks have been run from clean states on one fixed
build, outcomes and revisions are recorded, and every confirmed UI issue has a
severity and follow-up disposition.

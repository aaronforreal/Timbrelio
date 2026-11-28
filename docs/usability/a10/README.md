# A10 usability pilot protocol and practice examples

## Objective

Write and pilot three short Timbrelio browsing tasks covering map/filter
exploration, seed to neighbour listening, and PCA/UMAP comparison. This A10 pilot
checks task wording and the browsing workflow. It is separate from Meet's later
project-level evaluation with 4-6 classmates.

## Evidence status

The three files in `sessions/` are practice examples, not verified observed
participant sessions. Their `PRACTICE-BUILD` identifier and generic coordinate,
neighbour, and audio descriptions are placeholders; no exact app commit, archived
build, or input artifacts are identified. Times, outcomes, comments, and consent
entries illustrate how to fill out the form and must not be reported as measured
usability results or evidence of participant consent.

The original PR build (`6182eb395bb0f5409646d5512d0762962c82fc3b`) supports the
map and colour controls but does not expose the full filtering, selection,
playback, neighbour, and PCA/UMAP workflow below. It is not a tested pilot build.
The protocol is intended for a later integrated build that passes preflight.

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

> In the comparison area, play the selected seed. Play the first two neighbours
> with enabled audio, starting at rank 1 and skipping disabled controls.
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

## Practice example summary (not participant results)

The following counts summarize only the illustrative records in `sessions/`.

| Task | Completed | Median time | Major errors | Minor errors | Assistance |
|---|---:|---:|---:|---:|---:|
| 1 — Filter and inspect | 3/3 | 68 s | 0 | 2 | 1 |
| 2 — Seed and neighbours | 3/3 | 96 s | 0 | 2 | 0 |
| 3 — Compare PCA and UMAP | 3/3 | 82 s | 0 | 1 | 1 |

Across the practice examples `01 Elephant`, `02 Cat`, and `03 Rabbit`, all nine
task entries are marked completed. The examples contain no major errors, five
minor errors, and two assistance events. These are illustrative values, not
observed completion rates, timings, or error counts.

## Proposed wording revisions illustrated by the examples

| Task | Example friction | Proposed wording |
|---|---|---|
| 1 | Filtering and colouring were treated as the same action. | Name the Genres filter and Colour points by control separately. |
| 2 | “Available” was unclear when an audio control was disabled. | Play the first two neighbours with enabled audio, starting at rank 1 and skipping disabled controls. |
| 3 | The requested map comparison was too open-ended. | Give neutral centre/edge and grouped/spread-out cues. |

## Potential issues illustrated by the examples

| ID | Provisional severity | Practice example scenario | Recommended follow-up |
|---|---|---|---|
| PRACTICE-001 | Medium | 01 Elephant and 02 Cat confused filtering with colouring. | Separate filter and display controls. |
| PRACTICE-002 | Medium | 02 Cat paused at disabled audio; 03 Rabbit briefly lost rank order. | Keep ranks beside players and clarify disabled controls. |
| PRACTICE-003 | Low | 02 Cat expected Locate on map to replace the seed selection. | Clarify that locating highlights without changing the selection. |
| PRACTICE-004 | Low | 02 Cat needed a cue for the PCA/UMAP comparison. | Use the revised instruction in the later evaluation. |

## Handoff and completion

Hand this protocol and the clearly labelled practice examples to Meet as planning
material for the later 4–6 classmate project evaluation. Validate the potential
issues in actual sessions before treating them as findings or confirmed UI fixes.
Track confirmed fixes through follow-up issues or PRs in Aaron's deliverables plan.

An observed participant pilot remains outstanding. Before running it, record the
exact commit SHA or archived build link, coordinate and neighbour file paths with
checksums and configuration, and the audio manifest/root with file identifiers
and checksums. Record the preflighted seed and neighbour IDs and use the same
inputs for every session. Save actual anonymized records separately from these
practice examples and replace the illustrative summary with measured results.

A10 is not yet complete. It is complete when all three tasks have been run from
clean states on one fixed build, outcomes and revisions are recorded, and every
confirmed UI issue has a severity and follow-up disposition.

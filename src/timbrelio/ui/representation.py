"""Set comparison of saved original-space neighbour results."""

from dataclasses import dataclass

from timbrelio.ui.neighbours import NeighbourResult


@dataclass(frozen=True)
class NeighbourOverlap:
    """IDs in deterministic order, preserving each input's saved rank order."""

    shared: tuple[str, ...]
    conventional_only: tuple[str, ...]
    openl3_only: tuple[str, ...]


def compare_neighbours(
    conventional: list[NeighbourResult], openl3: list[NeighbourResult]
) -> NeighbourOverlap:
    """Compare displayed IDs without sorting by metric or changing saved ranks."""

    left = tuple(dict.fromkeys(result.track_id for result in conventional))
    right = tuple(dict.fromkeys(result.track_id for result in openl3))
    left_ids, right_ids = set(left), set(right)
    return NeighbourOverlap(
        shared=tuple(track_id for track_id in left if track_id in right_ids),
        conventional_only=tuple(track_id for track_id in left if track_id not in right_ids),
        openl3_only=tuple(track_id for track_id in right if track_id not in left_ids),
    )

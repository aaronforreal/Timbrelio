from timbrelio.ui.neighbours import neighbours_for_seed, read_neighbours
from timbrelio.ui.data import read_coordinates
from timbrelio.ui.representation import compare_neighbours
from pathlib import Path


def test_overlap_preserves_saved_rank_order_and_inputs():
    coordinates = read_coordinates(Path("data/sample_coordinates.csv"))
    left = neighbours_for_seed(
        read_neighbours(Path("data/sample_neighbours.csv")), coordinates,
        seed_track_id="TRK-0001", representation="Conventional",
    )
    right = neighbours_for_seed(
        read_neighbours(Path("data/sample_openl3_neighbours.csv")), coordinates,
        seed_track_id="TRK-0001", representation="OpenL3",
    )
    comparison = compare_neighbours(left, right)
    assert comparison.shared == ("TRK-0006", "TRK-0009", "TRK-0014")
    assert comparison.conventional_only == ("TRK-0020", "TRK-0003")
    assert comparison.openl3_only == ("TRK-0008", "TRK-0018")
    assert [result.rank for result in right] == [1, 2, 3, 4, 5]
    assert right[0].track_id == "TRK-0009"
    assert compare_neighbours(left, []).conventional_only == tuple(r.track_id for r in left)
    assert compare_neighbours([], []).shared == ()

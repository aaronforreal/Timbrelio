import pandas as pd
import pytest

from timbrelio.ui.data import (
    CoordinateDataError,
    NOISE_LABEL,
    UNASSIGNED_LABEL,
    UNAVAILABLE_TITLE,
    read_coordinates,
)


def write_coordinates(tmp_path, frame):
    path = tmp_path / "coordinates.csv"
    frame.to_csv(path, index=False)
    return path


def test_read_coordinates_accepts_valid_rows(tmp_path):
    path = write_coordinates(
        tmp_path,
        pd.DataFrame(
            {
                "track_id": ["TRK-1", "TRK-2"],
                "x": [0.5, -1.25],
                "y": [2, 3],
                "title": ["  First Light ", "Night Drive"],
                "genre": ["Jazz", "Rock"],
                "cluster": [2, -1],
            }
        ),
    )

    result = read_coordinates(path)

    assert result["track_id"].tolist() == ["TRK-1", "TRK-2"]
    assert result["x"].dtype.kind == "f"
    assert result["y"].dtype.kind == "f"
    assert result["title"].tolist() == ["First Light", "Night Drive"]
    assert result["genre"].tolist() == ["Jazz", "Rock"]
    assert result["cluster"].tolist() == ["2", NOISE_LABEL]


def test_read_coordinates_accepts_header_only_artifact(tmp_path):
    path = write_coordinates(
        tmp_path,
        pd.DataFrame(columns=["track_id", "x", "y"]),
    )

    result = read_coordinates(path)

    assert result.empty
    assert list(result.columns) == [
        "track_id",
        "x",
        "y",
        "title",
        "genre",
        "cluster",
    ]


def test_read_coordinates_makes_missing_display_metadata_explicit(tmp_path):
    path = write_coordinates(
        tmp_path,
        pd.DataFrame(
            {
                "track_id": ["TRK-1", "TRK-2"],
                "x": [0, 1],
                "y": [1, 0],
                "title": [None, "  "],
                "genre": ["", None],
                "cluster": [None, "  "],
            }
        ),
    )

    result = read_coordinates(path)

    assert result["title"].tolist() == [UNAVAILABLE_TITLE, UNAVAILABLE_TITLE]
    assert result["genre"].tolist() == [UNASSIGNED_LABEL, UNASSIGNED_LABEL]
    assert result["cluster"].tolist() == [UNASSIGNED_LABEL, UNASSIGNED_LABEL]


@pytest.mark.parametrize(
    ("frame", "message"),
    [
        (
            pd.DataFrame({"track_id": ["TRK-1"], "x": [1]}),
            "missing required columns: y",
        ),
        (
            pd.DataFrame(
                {"track_id": ["TRK-1", "TRK-1"], "x": [1, 2], "y": [3, 4]}
            ),
            "track_id values must be unique",
        ),
        (
            pd.DataFrame({"track_id": ["TRK-1"], "x": ["nope"], "y": [3]}),
            "Column x must contain only finite numbers",
        ),
    ],
)
def test_read_coordinates_rejects_invalid_artifacts(tmp_path, frame, message):
    path = write_coordinates(tmp_path, frame)

    with pytest.raises(CoordinateDataError, match=message):
        read_coordinates(path)


def test_read_coordinates_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="Coordinate artifact not found"):
        read_coordinates(tmp_path / "missing.csv")


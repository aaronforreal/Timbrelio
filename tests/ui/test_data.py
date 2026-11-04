import pandas as pd
import pytest

from timbrelio.ui.data import CoordinateDataError, read_coordinates


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
                "genre": ["Jazz", "Rock"],
            }
        ),
    )

    result = read_coordinates(path)

    assert result["track_id"].tolist() == ["TRK-1", "TRK-2"]
    assert result["x"].dtype.kind == "f"
    assert result["y"].dtype.kind == "f"
    assert "genre" in result.columns


def test_read_coordinates_accepts_header_only_artifact(tmp_path):
    path = write_coordinates(
        tmp_path,
        pd.DataFrame(columns=["track_id", "x", "y"]),
    )

    result = read_coordinates(path)

    assert result.empty
    assert list(result.columns) == ["track_id", "x", "y"]


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

